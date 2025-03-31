from fastapi import FastAPI
from app.scheduler import check_gmail
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

scheduler = BackgroundScheduler()
scheduler.add_job(check_gmail, "interval", minutes=1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/check-gmail")
def manual_check():
    check_gmail()
    return {"message": "수동으로 Gmail 확인 완료"}