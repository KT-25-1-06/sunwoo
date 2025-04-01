from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import ScheduleAnalysis, CleanedEmail, Base
from app.parser import parse_schedule

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/parse-schedule/")
def parse_schedule_from_cleaned_email(email_id: int, db: Session = Depends(get_db)):
    cleaned_email = db.query(CleanedEmail).filter(CleanedEmail.id == email_id).first()
    if not cleaned_email:
        raise HTTPException(status_code=404, detail="Cleaned email not found")

    try:
        print("💬 이메일 본문:", cleaned_email.body)
        if not cleaned_email.body:
            raise HTTPException(status_code=400, detail="Email body is empty")
        
        parsed = parse_schedule(cleaned_email.body)
        new_entry = ScheduleAnalysis(
            emailContent=None,
            # emailContent=cleaned_email.body
            parsedTitle=parsed["parsedTitle"],
            parsedStartAt=parsed["parsedStartAt"],
            parsedEndAt=parsed["parsedEndAt"],
            parsedLocation=parsed["parsedLocation"],
            status="success"
        )
    except Exception as e:
        new_entry = ScheduleAnalysis(
            emailContent=cleaned_email.body,
            status="fail",
            failureReason=str(e)
        )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"id": new_entry.id, "status": new_entry.status}