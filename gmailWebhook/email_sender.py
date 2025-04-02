import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

## TODO: Replace this direct SMTP send logic with Kafka publisher to email-sending service
def send_ics_email_binary(to_email: str, subject: str, message: str, ics_bytes: bytes, summary: str, filename: str):
    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        full_message = f"{message}\n\n📌 첨부된 일정 요약:\n\n{summary}"
        msg.attach(MIMEText(full_message, "plain"))

        part = MIMEApplication(ics_bytes, _subtype="ics")
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        part.add_header("Content-Type", "text/calendar; method=REQUEST")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.send_message(msg)

        return JSONResponse(content={"message": "이메일 전송 완료 (요약 포함)"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

