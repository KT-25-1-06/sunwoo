import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Form
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ICSFileBinary, CleanedEmail, ScheduleAnalysis
from app.scheduler import check_gmail
from email_reader import get_ics_summary
from email_sender import send_ics_email_binary

from app.kafka_service import kafka_service
from app.events import EmailAnalysisResultEvent
from datetime import datetime
from settings import settings

from app.database import engine, Base
from app.models import Email, CleanedEmail, ICSFileBinary, ScheduleAnalysis

Base.metadata.create_all(bind=engine)

# 전역 변수로 consumer task를 저장
consumer_task = None

app = FastAPI()

scheduler = BackgroundScheduler()
scheduler.add_job(check_gmail, "interval", minutes=0.1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    
    # Startup
    print("🚀 Gmail Webhook 서비스 시작")
    scheduler.start()
    print("✅ 스케줄러 시작 완료")
    
    # Kafka 서비스 시작
    print("🔄 Kafka 서비스 시작 중...")
    try:
        await kafka_service.start()
        print("✅ Kafka 서비스 시작 완료")
        
        # Kafka 메시지 핸들러 등록
        print("🔄 Kafka 메시지 핸들러 등록 중...")
        consumer_task = asyncio.create_task(kafka_service.consume_events(handle_kafka_message))
        print("✅ Kafka 메시지 핸들러 등록 완료")
    except Exception as e:
        print(f"❌ Kafka 서비스 시작 실패: {str(e)}")
    
    yield
    
    # Shutdown
    print("⏹️ Gmail Webhook 서비스 종료")
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    scheduler.shutdown()
    print("✅ 스케줄러 종료 완료")
    await kafka_service.stop()
    print("✅ Kafka 서비스 종료 완료")

app.router.lifespan_context = lifespan

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/check-gmail")
def manual_check():
    check_gmail()
    return {"message": "수동으로 Gmail 확인 완료"}

@app.post("/send-ics-email")
def send_from_db(
    file_id: int = Form(...),
    to_email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    ics = db.query(ICSFileBinary).filter(ICSFileBinary.id == file_id).first()
    if not ics:
        return {"error": "해당 파일이 존재하지 않습니다."}

    summary = get_ics_summary(file_id, db)
    # TODO: Replace with Kafka message publish to trigger email sending
    return send_ics_email_binary(to_email, subject, message, ics.fileData, summary, ics.filename)

async def handle_kafka_message(topic: str, payload: dict):
    print(f"📨 메시지 수신: topic={topic}, payload={payload}")
    
    if topic == settings.TOPIC_EMAIL_ANALYSIS_RESULT:
        print(f"📧 이메일 분석 결과 수신: {payload}")
        try:
            event = EmailAnalysisResultEvent(**payload)
            print(f"✅ 이메일 분석 결과 파싱 성공: email_id={event.email_id}")
            
            db = SessionLocal()
            try:
                # 이메일 ID로 원본 이메일 찾기
                email = db.query(CleanedEmail).filter(CleanedEmail.id == event.email_id).first()
                if not email:
                    print(f"❌ 이메일을 찾을 수 없음: email_id={event.email_id}")
                    return
                
                # 분석 결과에 따라 처리
                if event.status == "SUCCESS":
                    print(f"✅ 이메일 분석 성공: email_id={event.email_id}")
                    print(f"  - 제목: {event.parsedTitle}")
                    print(f"  - 시작: {event.parsedStartAt}")
                    print(f"  - 종료: {event.parsedEndAt}")
                    print(f"  - 장소: {event.parsedLocation}")
                    
                    # 분석 결과를 ScheduleAnalysis 테이블에 저장
                    try:
                        # 문자열 날짜를 datetime 객체로 변환
                        start_at = datetime.fromisoformat(event.parsedStartAt)
                        end_at = datetime.fromisoformat(event.parsedEndAt)
                        
                        analysis = ScheduleAnalysis(
                            email_id=event.email_id,
                            parsed_title=event.parsedTitle,
                            parsed_start_time=start_at,
                            parsed_end_time=end_at,
                            parsed_location=event.parsedLocation,
                            created_at=datetime.now()
                        )
                        db.add(analysis)
                        db.commit()
                        print(f"✅ 이메일 분석 결과 저장 완료: email_id={event.email_id}")
                    except Exception as e:
                        print(f"❌ 이메일 분석 결과 저장 실패: {str(e)}")
                        db.rollback()
                else:
                    print(f"❌ 이메일 분석 실패: email_id={event.email_id}")
                    print(f"  - 실패 사유: {event.failureReason}")
            except Exception as e:
                print(f"❌ 이메일 분석 결과 처리 실패: {str(e)}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            print(f"❌ 이메일 분석 결과 파싱 실패: {str(e)}")
            print(f"  - 원본 데이터: {payload}")