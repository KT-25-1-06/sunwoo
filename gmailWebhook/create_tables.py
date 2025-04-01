from app.database import engine, Base
from app.models import Email, CleanedEmail

Base.metadata.create_all(bind=engine)