from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class ScheduleEvent(BaseModel):
    summary: str
    date: date
    start_time: str  # "HH:MM" 형식
    end_time: str    # "HH:MM" 형식
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = []

class ScheduleRequest(BaseModel):
    events: List[ScheduleEvent]