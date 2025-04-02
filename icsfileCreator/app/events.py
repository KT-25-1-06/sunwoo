from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ScheduleEvent(BaseModel):
    scheduleId: int
    title: str 
    description: str
    location: str
    startAt: datetime
    endAt: datetime

    # class Config:
    #     json_encoders = {
    #         datetime: lambda dt: dt.isoformat()
    #     }

class CalendarSubscriptionCreatedEvent(BaseModel):
    calendarId: int
    calendarName: str
    schedules: List[ScheduleEvent]

class CalendarSubscriptionDeletedEvent(BaseModel):
    calendarId: int

class CalendarIcsCreatedEvent(BaseModel):
    calendarId: int
    subscriptionUrl: str

class ScheduleCreateEvent(BaseModel):
    email_id: int
    title: str
    description: Optional[str] = None
    start_at: str
    end_at: str
    location: Optional[str] = None
    status: str = "UPCOMING"
    repeat_type: str = "NONE"