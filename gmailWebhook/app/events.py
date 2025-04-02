from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class EmailAnalysisRequestEvent(BaseModel):
    email_id: int
    subject: str
    body: str
    sender_name: str
    sender_email: str
    to: str
    cc: str
    date: str

class EmailAnalysisResultEvent(BaseModel):
    email_id: int
    parsedTitle: str
    parsedStartAt: str
    parsedEndAt: str
    parsedLocation: str
    status: str
    failureReason: Optional[str] = None

class ScheduleCreateEvent(BaseModel):
    email_id: int
    title: str
    description: Optional[str] = None
    start_at: str
    end_at: str
    location: Optional[str] = None
    status: str = "UPCOMING"
    repeat_type: str = "NONE"



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