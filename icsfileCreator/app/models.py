



Base = declarative_base()

class ScheduleAnalysis(Base):
    __tablename__ = "schedule_analysis"

    # id = Column(Integer, primary_key=True, index=True)
    # userId = Column(String)
    # emailContent = Column(String)
    # parsedTitle = Column(String)
    # parsedStartAt = Column(DateTime)
    # parsedEndAt = Column(DateTime)
    # parsedLocation = Column(String)
    # status = Column(String)
    # failureReason = Column(String)
    # createdAt = Column(DateTime)
    # updatedAt = Column(DateTime)

class ICSFileBinary(Base):
    __tablename__ = "ics_files_binary"

    # id = Column(Integer, primary_key=True, index=True)
    # isGroupSchedule = Column(Boolean, default=False)
    # calendarId = Column(Integer, nullable=True)
    # groupId = Column(Integer, nullable=True)
    # scheduleId = Column(Integer, ForeignKey("schedule_analysis.id"))
    # filename = Column(String)
    # fileData = Column(LargeBinary)
    # createdAt = Column(DateTime, default=datetime.utcnow)

