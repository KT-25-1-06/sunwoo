from icalendar import Calendar, Event
import asyncio, sys
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Form, Path, Query, Body, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import ICSFileBinary, CleanedEmail, ScheduleAnalysis, Base
from app.scheduler import check_gmail
from email_reader import get_ics_summary
from email_sender import send_ics_email_binary

from app.kafka_service import kafka_service
from app.events import EmailAnalysisResultEvent, ScheduleCreateEvent, CalendarSubscriptionCreatedEvent, CalendarSubscriptionDeletedEvent, CalendarIcsCreatedEvent
from datetime import datetime, timezone
from settings import settings

Base.metadata.create_all(bind=engine)

# 전역 변수로 consumer task를 저장
consumer_task = None

app = FastAPI()

scheduler = BackgroundScheduler()
scheduler.add_job(check_gmail, "interval", minutes=0.1)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

## 단일 조회
@app.get("/ics/single/{schedule_id}")
def get_single_schedule_ics(schedule_id: int = Path(...), db: Session = Depends(get_db)):
    ics_file = db.query(ICSFileBinary).filter(
        ICSFileBinary.scheduleId == schedule_id,
        ICSFileBinary.isGroupSchedule == False
    ).order_by(ICSFileBinary.createdAt.desc()).first()

    if not ics_file:
        raise HTTPException(status_code=404, detail="단일 일정 ICS 파일이 존재하지 않습니다.")

    return {
        "ics_file_id": ics_file.id,
        "filename": ics_file.filename,
        "createdAt": ics_file.createdAt,
    }

## 그룹 조회
@app.get("/ics/group")
def get_group_schedule_ics(
    calendar_id: str = Query(...),
    group_id: str = Query(...),
    db: Session = Depends(get_db)
):
    ics_file = db.query(ICSFileBinary).filter(
        ICSFileBinary.calendarId == calendar_id,
        ICSFileBinary.groupId == group_id,
        ICSFileBinary.isGroupSchedule == True
    ).order_by(ICSFileBinary.createdAt.desc()).first()

    if not ics_file:
        raise HTTPException(status_code=404, detail="그룹 일정 ICS 파일이 존재하지 않습니다.")

    return {
        "ics_file_id": ics_file.id,
        "filename": ics_file.filename,
        "createdAt": ics_file.createdAt,
    }

## calendarId 기반 최신 ICS 반환 (구독 URL)
@app.get("/ics/{calendar_id}.ics")
def download_calendar_ics(calendar_id: str = Path(...), db: Session = Depends(get_db)):
    print(f"🔍 calendar_id: {calendar_id}")
    ics_file = db.query(ICSFileBinary).filter(
        ICSFileBinary.calendarId == calendar_id,
        ICSFileBinary.isGroupSchedule == True
    ).order_by(ICSFileBinary.createdAt.desc()).first()

    if not ics_file:
        raise HTTPException(status_code=404, detail="calendarId에 해당하는 ICS 파일이 존재하지 않습니다.")

    return Response(
        content=ics_file.fileData,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={ics_file.filename}"
        }
    )

## ics파일 생성
@app.post("/ics")
def create_ics_file(
    is_group: bool = Query(False),
    schedule_id: int = Query(None),
    calendar_id: str = Query(None),
    group_id: str = Query(None),
    db: Session = Depends(get_db)
):
    if is_group:
        if not calendar_id or not group_id:
            raise HTTPException(status_code=400, detail="그룹 일정은 calendar_id와 group_id가 필요합니다.")
    else:
        if not schedule_id:
            raise HTTPException(status_code=400, detail="단일 일정은 schedule_id가 필요합니다.")

    schedule = None
    if not is_group:
        if schedule_id != -1:
            schedule = db.query(ScheduleAnalysis).filter(
                ScheduleAnalysis.id == schedule_id,
                ScheduleAnalysis.status == "success"
            ).first()

            if not schedule:
                raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")

    cal = Calendar()
    cal.add("prodid", "-//KT Auto Scheduler//")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", schedule.parsedTitle if schedule else "그룹 일정")
    event.add("dtstart", schedule.parsedStartAt.astimezone(timezone("Asia/Seoul")) if schedule else datetime.now())
    event.add("dtend", schedule.parsedEndAt.astimezone(timezone("Asia/Seoul")) if schedule else datetime.now())
    event.add("location", schedule.parsedLocation if schedule else "미정")
    event.add("description", schedule.emailContent if schedule else "그룹 일정입니다.")
    cal.add_component(event)

    ics_bytes = cal.to_ical()
    filename = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"

    ics_file = ICSFileBinary(
        scheduleId=schedule.id if schedule else None,
        calendarId=calendar_id,
        groupId=group_id,
        isGroupSchedule=is_group,
        filename=filename,
        fileData=ics_bytes
    )
    db.add(ics_file)
    db.commit()
    db.refresh(ics_file)

    return {
        "message": "ICS 파일이 DB에 저장되었습니다.",
        "ics_file_id": ics_file.id
    }

## ICS 파일 수정
@app.put("/ics/{ics_id}")
def update_ics_file(
    ics_id: int = Path(...),
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    file_entry = db.query(ICSFileBinary).filter(ICSFileBinary.id == ics_id).first()
    if not file_entry:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    for key, value in payload.items():
        if hasattr(file_entry, key):
            setattr(file_entry, key, value)

    db.commit()
    db.refresh(file_entry)

    return {"message": "ICS 파일이 수정되었습니다.", "ics_file_id": file_entry.id}

## ICS 파일 삭제
@app.delete("/ics/{ics_id}")
def delete_ics_file(ics_id: int = Path(...), db: Session = Depends(get_db)):
    file_entry = db.query(ICSFileBinary).filter(ICSFileBinary.id == ics_id).first()
    if not file_entry:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    db.delete(file_entry)
    db.commit()

    return {"message": "ICS 파일이 삭제되었습니다."}

## ICS 파일 다운로드
@app.get("/ics/download-ics/")
def download_ics(ics_file_id: int, db: Session = Depends(get_db)):
    file_entry = db.query(ICSFileBinary).filter(ICSFileBinary.id == ics_file_id).first()

    if not file_entry:
        return {"error": "파일을 찾을 수 없습니다"}

    return Response(
        content=file_entry.fileData,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={file_entry.filename}"
        }
    )

#################### kafka ##################################

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
    print(f"summary: {summary}")
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

                        event = ScheduleCreateEvent(
                            email_id=event.email_id,
                            title=event.parsedTitle,
                            description=email.body,
                            start_at=event.parsedStartAt,
                            end_at=event.parsedEndAt,
                            location=event.parsedLocation,
                        )
                        
                        # ics file create
                        result = create_ics_file(is_group=False, schedule_id=-1, calendar_id=-1, group_id=-1, db=db)

                        print(f"🔄 ics file create: {result}")

                        send_from_db(file_id=result["ics_file_id"], to_email=email.sender_email, subject=event.title, message=email.body, db=db)

                        print(f"🔄 ics file send: {result}")

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
    elif topic == "calendar.ics.requested":
        try:
            event = CalendarSubscriptionCreatedEvent(**data)

            print(f"➡️ 처리할 캘린더 ID: {event.calendarId}, 일정 수: {len(event.schedules)}")

            db = SessionLocal()
            try:
                ics_file = db.query(ICSFileBinary).filter(
                    ICSFileBinary.calendarId == event.calendarId,
                    ICSFileBinary.isGroupSchedule == True
                ).order_by(ICSFileBinary.createdAt.desc()).first()

                if ics_file:
                    update_ics_file(ics_id=ics_file.id, payload=data, db=db)
                else:
                    create_ics_file(is_group=True, calendar_id=event.calendarId, group_id=event.calendarId, db=db)

                subscription_url = f"{settings.ICS_FILE_SERVICE_URL}/ics/{event.calendarId}.ics"

                await kafka_service.produce_calendar_ics_created(
                    CalendarIcsCreatedEvent(calendarId=event.calendarId, subscriptionUrl=subscription_url)
                )
                print(f"✅ ICS 파일 생성 완료 이벤트 전송: {subscription_url}")

            finally:
                db.close()

        except Exception as e:
            import traceback
            print(f"❌ CalendarSubscriptionCreatedEvent 처리 중 오류: {e}")
            traceback.print_exc()
    elif topic == "calendar.ics.delete.requested":
        try:
            event = CalendarSubscriptionDeletedEvent(**data)
            print(f"🗑️ ICS 삭제 요청: calendarId = {event.calendarId}")
            # TODO: 삭제 로직 처리
        except Exception as e:
            print(f"❌ CalendarSubscriptionDeletedEvent 처리 중 오류: {e}")
    
    elif topic == "schedule.create":
        try:
            event = ScheduleCreateEvent(**data)
            print(f"🔄 일정 생성 요청 수신: {event.dict()}")

            create_ics_file(is_group=True, calendar_id=0, group_id=0, db=db)

            # send ics file created event
            await kafka_service.produce_calendar_ics_created(
                
            )
        except Exception as e:
            print(f"❌ ScheduleCreateEvent 처리 중 오류: {e}")
