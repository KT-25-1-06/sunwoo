from fastapi import FastAPI
from client.ics_client import request_ics_file
from services.email_sender import send_email_with_attachment
from pydantic import BaseModel
from typing import Any

app = FastAPI()

# 요청 바디 전체를 하나의 모델로 정의
class SendScheduleRequest(BaseModel):
    schedule: dict
    to_email: str

@app.post("/send-schedule")
def send_schedule(payload: SendScheduleRequest):
    filepath = request_ics_file(payload.schedule)
    send_email_with_attachment(payload.to_email, filepath)
    return {"message": f"{payload.to_email}로 일정 메일 전송 완료"}