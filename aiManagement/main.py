from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import ScheduleAnalysis, CleanedEmail, Base
from app.parser import parse_schedule
from settings import settings
from app.kafka_service import kafka_service
from app.events import EmailAnalysisRequestEvent, EmailAnalysisResultEvent
import asyncio
import json
from datetime import datetime

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    print("🚀 AI Management 서비스 시작")
    await kafka_service.start()
    print("✅ Kafka 서비스 시작 완료")
    asyncio.create_task(consume_messages())

@app.on_event("shutdown")
async def shutdown_event():
    print("⏹️ AI Management 서비스 종료")
    await kafka_service.stop()
    print("✅ Kafka 서비스 종료 완료")

async def handle_kafka_message(topic: str, message: dict):
    print(f"📨 메시지 수신: topic={topic}, message={json.dumps(message, indent=2)}")
    try:
        if topic == settings.TOPIC_EMAIL_ANALYSIS_REQUEST:
            event = EmailAnalysisRequestEvent(**message)
            print(f"📧 이메일 분석 요청: email_id={event.email_id}")
            print(f"🔍 이메일 분석 시작: subject={event.subject}")
            
            # 이메일 본문에서 일정 정보 추출
            try:
                # parser.py를 사용하여 이메일 내용 분석
                parsed = parse_schedule(event.body)
                print(f"✅ 이메일 분석 완료: {parsed}")
                
                # 분석 결과를 데이터베이스에 저장
                db = SessionLocal()
                try:
                    new_entry = ScheduleAnalysis(
                        emailContent=event.body,
                        parsedTitle=parsed["parsedTitle"],
                        parsedStartAt=parsed["parsedStartAt"],
                        parsedEndAt=parsed["parsedEndAt"],
                        parsedLocation=parsed["parsedLocation"],
                        status="success"
                    )
                    db.add(new_entry)
                    db.commit()
                    db.refresh(new_entry)
                    print(f"✅ 분석 결과 저장 완료: id={new_entry.id}")
                finally:
                    db.close()
                
                # 분석 결과를 Kafka로 발행
                result = EmailAnalysisResultEvent(
                    email_id=event.email_id,
                    parsedTitle=parsed["parsedTitle"],
                    parsedStartAt=parsed["parsedStartAt"],
                    parsedEndAt=parsed["parsedEndAt"],
                    parsedLocation=parsed["parsedLocation"],
                    status="SUCCESS"
                )
                await kafka_service.produce_email_analysis_result(result)
                print(f"✅ 분석 결과 발행 완료: email_id={event.email_id}")
            except Exception as e:
                print(f"❌ 이메일 분석 실패: {str(e)}")
                
                # 분석 실패 결과를 데이터베이스에 저장
                db = SessionLocal()
                try:
                    new_entry = ScheduleAnalysis(
                        emailContent=event.body,
                        status="fail",
                        failureReason=str(e)
                    )
                    db.add(new_entry)
                    db.commit()
                    db.refresh(new_entry)
                    print(f"❌ 분석 실패 결과 저장 완료: id={new_entry.id}")
                finally:
                    db.close()
                
                # 분석 실패 결과를 Kafka로 발행
                result = EmailAnalysisResultEvent(
                    email_id=event.email_id,
                    parsedTitle="",
                    parsedStartAt="",
                    parsedEndAt="",
                    parsedLocation="",
                    status="FAILURE",
                    failureReason=str(e)
                )
                await kafka_service.produce_email_analysis_result(result)
                print(f"❌ 분석 실패 결과 발행 완료: email_id={event.email_id}")
    except Exception as e:
        print(f"❌ 메시지 처리 중 오류 발생: {str(e)}")
        error_result = EmailAnalysisResultEvent(
            email_id=message.get("email_id", "unknown"),
            parsedTitle="",
            parsedStartAt="",
            parsedEndAt="",
            parsedLocation="",
            status="FAILURE",
            failureReason=str(e)
        )
        await kafka_service.produce_email_analysis_result(error_result)

async def consume_messages():
    print("🔄 메시지 수신 대기 시작...")
    await kafka_service.consume_events(handle_kafka_message)

@app.get("/")
async def root():
    return {"message": "AI Management Service is running"}