from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Form
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ICSFileBinary
from app.scheduler import check_gmail
from email_reader import get_ics_summary
from email_sender import send_ics_email_binary

app = FastAPI()

scheduler = BackgroundScheduler()
scheduler.add_job(check_gmail, "interval", minutes=0.5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

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
