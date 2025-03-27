from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EventItem(BaseModel):
    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    alarm_minutes_before: Optional[int] = None

class Schedule(BaseModel):
    events: List[EventItem]