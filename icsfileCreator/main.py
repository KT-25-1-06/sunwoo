from fastapi import FastAPI, Response, Depends
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

@app.get("/generate-ics-from-db/")
def generate_ics_from_db(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(ScheduleAnalysis).filter(
        ScheduleAnalysis.id == schedule_id,
        ScheduleAnalysis.status == "success"
    ).first()

    if not schedule:
        return {"message": "No matching schedule found."}

    cal = Calendar()
    cal.add("prodid", "-//KT Auto Scheduler//")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", schedule.parsedTitle)
    event.add("dtstart", schedule.parsedStartAt.astimezone(timezone("Asia/Seoul")))
    event.add("dtend", schedule.parsedEndAt.astimezone(timezone("Asia/Seoul")))
    event.add("location", schedule.parsedLocation or "")
    event.add("description", schedule.emailContent or "")
    cal.add_component(event)

    ics_content = cal.to_ical()

    filename = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
    file_path = os.path.join(SAVE_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(ics_content)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/generate-ics-binary/")
def generate_ics_binary(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(ScheduleAnalysis).filter(
        ScheduleAnalysis.id == schedule_id,
        ScheduleAnalysis.status == "success"
    ).first()

    if not schedule:
        return {"error": "Schedule not found"}

    cal = Calendar()
    cal.add("prodid", "-//KT Auto Scheduler//")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", schedule.parsedTitle)
    event.add("dtstart", schedule.parsedStartAt.astimezone(timezone("Asia/Seoul")))
    event.add("dtend", schedule.parsedEndAt.astimezone(timezone("Asia/Seoul")))
    event.add("location", schedule.parsedLocation or "")
    event.add("description", schedule.emailContent or "")
    cal.add_component(event)

    ics_bytes = cal.to_ical()

    # DB 저장
    ics_file = ICSFileBinary(
        scheduleId=schedule.id,
        filename=f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics",
        fileData=ics_bytes,
    )
    db.add(ics_file)
    db.commit()
    db.refresh(ics_file)

    return {
        "message": "ICS 파일이 DB에 저장되었습니다.",
        "ics_file_id": ics_file.id
    }

@app.get("/download-ics/")
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