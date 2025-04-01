from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmailInput(BaseModel):
    content: Optional[str] = None
    email_id: Optional[int] = None

class ParsedSchedule(BaseModel):
    parsedTitle: str
    parsedStartAt: datetime
    parsedEndAt: datetime
    parsedLocation: str