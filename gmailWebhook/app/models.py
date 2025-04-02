from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text, Boolean
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(512), nullable=True)
    subject = Column(String(512))
    sender = Column(String(512))
    to = Column(String(512))
    cc = Column(String(512), nullable=True)
    body = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processedStatus = Column(String(50), default="unread")

class CleanedEmail(Base):
    __tablename__ = "cleaned_emails"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(512))
    sender_name = Column(String(512))
    sender_email = Column(String(512))
    to = Column(String(512))
    cc = Column(String(512))
    body = Column(Text)
    date = Column(String(512))

class ICSFileBinary(Base):
    __tablename__ = "ics_files_binary"

    id = Column(Integer, primary_key=True, index=True)
    isGroupSchedule = Column(Boolean, default=False)
    calendarId = Column(Integer, nullable=True)
    groupId = Column(Integer, nullable=True)
    scheduleId = Column(Integer, nullable=True)
    filename = Column(String)
    fileData = Column(LargeBinary)
    createdAt = Column(DateTime, default=datetime.utcnow)

class ScheduleAnalysis(Base):
    __tablename__ = "schedule_analysis"

    id = Column(Integer, primary_key=True)
    userId = Column(String)
    email_id = Column(Integer)
    email_content = Column(Text)
    parsed_title = Column(String(512), nullable=True)
    parsed_start_at = Column(DateTime, nullable=True)
    parsed_end_at = Column(DateTime, nullable=True)
    status = Column(String(50))
    failure_reason = Column(String(512), nullable=True)
    parsed_location = Column(String(512), nullable=True)
    parsed_description = Column(Text, nullable=True)
    parsed_attendees = Column(Text, nullable=True)  # JSON 문자열로 저장
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)