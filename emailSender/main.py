from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv

from icalendar import Calendar


load_dotenv()

app = FastAPI()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def summarize_ics(ics_text: str) -> str:
    try:
        cal = Calendar.from_ical(ics_text)
        summaries = []

        for component in cal.walk():
            if component.name == "VEVENT":
                summary = component.get("SUMMARY", "제목 없음")
                location = component.get("LOCATION", "미지정")
                description = component.get("DESCRIPTION", "없음")
                dtstart = component.get("DTSTART").dt
                dtend = component.get("DTEND").dt

                # 참석자 처리
                attendees = component.get("ATTENDEE")
                if isinstance(attendees, list):
                    attendee_list = [
                        a.params.get("CN", "Unknown") + f" <{a.to_ical().decode('utf-8').split(':')[-1]}>"
                        for a in attendees
                    ]
                elif attendees:
                    attendee_list = [
                        attendees.params.get("CN", "Unknown") + f" <{attendees.to_ical().decode('utf-8').split(':')[-1]}>"
                    ]
                else:
                    attendee_list = []

                summary_text = (
                    f"<  {summary} >\n"
                    f" - 시간: {dtstart.strftime('%Y-%m-%d %H:%M')} ~ {dtend.strftime('%H:%M')}\n"
                    f" - 장소: {location}\n"
                    f" - 설명: {description}\n"
                    f" - 참석자: {', '.join(attendee_list) if attendee_list else '없음'}"
                )
                summaries.append(summary_text)

        return "\n\n".join(summaries)

    except Exception as e:
        return f"요약 실패: {e}"


@app.post("/send-ics-email")
async def send_ics_email(
    to_email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    ics_content: UploadFile = Form(...)
):
    try:
        # ICS 내용 읽기 및 요약
        ics_data = await ics_content.read()
        ics_text = ics_data.decode("utf-8")
        ics_summary = summarize_ics(ics_text)

        # 이메일 구성
        msg = MIMEMultipart("mixed")
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        # 본문 작성
        full_message = f"{message}\n\n📌 첨부된 일정 요약:\n\n{ics_summary}"
        msg.attach(MIMEText(full_message, "plain"))

        # ICS 파일 첨부
        part = MIMEApplication(ics_data, _subtype="ics")
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={ics_content.filename}"
        )
        part.add_header("Content-Type", "text/calendar; method=REQUEST")
        msg.attach(part)

        # 메일 전송
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.send_message(msg)

        return JSONResponse(content={"message": "이메일 전송 완료 (요약 포함)"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)