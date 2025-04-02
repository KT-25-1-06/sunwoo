import asyncio
import os
import json
from datetime import datetime

from fastapi import (Body, Depends, FastAPI, HTTPException, Path, Query, Response)
from icalendar import Calendar, Event
from pytz import timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.events import (CalendarIcsCreatedEvent,
                        CalendarSubscriptionCreatedEvent,
                        CalendarSubscriptionDeletedEvent,
                        ScheduleCreateEvent)
from app.models import Base, ICSFileBinary, ScheduleAnalysis
from app.kafka_service import kafka_service

from settings import settings

Base.metadata.create_all(bind=engine)

app = FastAPI()

SAVE_DIR = "./icsfiles"
os.makedirs(SAVE_DIR, exist_ok=True)

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

@app.on_event("startup")
async def startup():
    await kafka_service.start()
    asyncio.create_task(kafka_service.consume_events(handle_kafka_message))

@app.on_event("shutdown")
async def shutdown():
    await kafka_service.stop()

async def handle_kafka_message(topic: str, payload: str):
    print(f"📩 Kafka Received: topic={topic}, data={payload}")
    try:
        data = json.loads(payload)
    except Exception as e:
        print(f"❌ JSON 디코딩 실패: {e}")
        return

    if topic == "calendar.ics.requested":
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
        