from pydantic import BaseModel
from typing import Optional

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