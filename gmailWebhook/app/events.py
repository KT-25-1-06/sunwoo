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