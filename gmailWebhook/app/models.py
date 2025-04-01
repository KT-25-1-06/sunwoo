from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text

from app.database import Base


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
    scheduleId = Column(Integer)
    filename = Column(String)
    fileData = Column(LargeBinary)
    createdAt = Column(DateTime, default=datetime.utcnow)