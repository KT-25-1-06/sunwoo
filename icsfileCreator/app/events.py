from typing import List
from pydantic import BaseModel
from datetime import datetime

class ScheduleEvent(BaseModel):
    scheduleId: int
    title: str
    description: str
    location: str
    startAt: datetime
    endAt: datetime

class CalendarSubscriptionCreatedEvent(BaseModel):
    calendarId: int
    calendarName: str
    schedules: List[ScheduleEvent]

class CalendarSubscriptionDeletedEvent(BaseModel):
    calendarId: int

class CalendarIcsCreatedEvent(BaseModel):
    calendarId: int
    subscriptionUrl: str