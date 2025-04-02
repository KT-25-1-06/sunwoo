from app.database import engine, Base
from app.models import Email, CleanedEmail, ICSFileBinary, ScheduleAnalysis

Base.metadata.create_all(bind=engine)