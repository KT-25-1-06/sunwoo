from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from ics import Calendar, Event, DisplayAlarm
from datetime import datetime, timedelta
import uuid
import os

app = FastAPI()

# --- 데이터 모델 정의 ---
class EventItem(BaseModel):
    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    alarm_minutes_before: Optional[int] = None

class Schedule(BaseModel):
    events: List[EventItem]


# --- ICS 변환 엔드포인트 ---
@app.post("/convert-to-ics", response_class=FileResponse)
def convert_to_ics(schedule: Schedule):
    cal = Calendar()

    for item in schedule.events:
        e = Event()
        e.name = item.title
        e.begin = item.start
        e.end = item.end
        e.location = item.location
        e.description = item.description

        # 알람 설정 (선택사항)
        if item.alarm_minutes_before:
            alarm = DisplayAlarm(trigger=timedelta(minutes=-item.alarm_minutes_before))
            e.alarms.append(alarm)

        cal.events.add(e)

    # 고유 파일명 생성
    filename = f"{uuid.uuid4()}.ics"
    filepath = f"./icsfiles/{filename}"

    # 파일로 저장
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(cal)

    return FileResponse(filepath, filename="schedule.ics", media_type="text/calendar")