from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime

class ScheduleAnalysis(Base):
    
    __tablename__ = "schedule_analysis"

    id = Column(Integer, primary_key=True, index=True)
    emailContent = Column(Text)
    parsedTitle = Column(String)
    parsedStartAt = Column(DateTime)
    parsedEndAt = Column(DateTime)
    parsedLocation = Column(String)
    status = Column(String)
    failureReason = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    userId = Column(Integer, nullable=True)

class CleanedEmail(Base):
    __tablename__ = "cleaned_emails"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String)
    sender_name = Column(String)
    sender_email = Column(String)
    to = Column(String)
    cc = Column(String)
    body = Column(Text)
    date = Column(DateTime) 
    userId = Column(Integer, nullable=True)