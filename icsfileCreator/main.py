from fastapi import FastAPI, Response, Depends, Query, HTTPException, Path, Body
from icalendar import Calendar, Event
from datetime import datetime
from pytz import timezone
from sqlalchemy.orm import Session
import os

from app.models import ScheduleAnalysis, ICSFileBinary, Base
from app.database import SessionLocal, engine

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

@app.post("/api/v1/ics")
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

@app.put("/api/v1/ics/{ics_id}")
def update_ics_file(
    ics_id: int = Path(...),
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    file_entry = db.query(ICSFileBinary).filter(ICSFileBinary.id == ics_id).first()
    if not file_entry:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    # JSON으로 받은 key-value 쌍을 모두 반영
    for key, value in payload.items():
        if hasattr(file_entry, key):
            setattr(file_entry, key, value)

    db.commit()
    db.refresh(file_entry)

    return {"message": "ICS 파일이 수정되었습니다.", "ics_file_id": file_entry.id}

@app.delete("/api/v1/ics/{ics_id}")
def delete_ics_file(ics_id: int = Path(...), db: Session = Depends(get_db)):
    file_entry = db.query(ICSFileBinary).filter(ICSFileBinary.id == ics_id).first()
    if not file_entry:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    db.delete(file_entry)
    db.commit()

    return {"message": "ICS 파일이 삭제되었습니다."}

@app.get("/api/v1/ics/download-ics/")
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
