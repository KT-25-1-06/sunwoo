from sqlalchemy.orm import Session
from app.models import Email, CleanedEmail


def save_email_to_db(db: Session, subject: str, sender: str, to: str, cc: str, body: str):
    email = Email(
        subject=subject,
        sender=sender,
        to=to,
        cc=cc,
        body=body
    )
    db.add(email)
    db.commit()
    db.refresh(email)

def save_cleaned_email_to_db(db, subject, sender_name, sender_email, to, cc, body, date):
    email = CleanedEmail(
        subject=subject,
        sender_name=sender_name,
        sender_email=sender_email,
        to=to,
        cc=cc,
        body=body,
        date=date
    )
    db.add(email)
    db.commit()