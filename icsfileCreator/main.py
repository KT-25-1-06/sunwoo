from fastapi import FastAPI, Response
from models import ScheduleRequest
from datetime import datetime, time
from icalendar import Calendar, Event, vCalAddress, vText
from pytz import timezone
import os

app = FastAPI()

SAVE_DIR = "/Users/sunwoo/Desktop/dev/kt-alpb-2ndproj/icsfileCreator/icsfiles"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.post("/generate-ics")
def generate_ics(data: ScheduleRequest):
    cal = Calendar()
    cal.add("prodid", "-//KT Auto Scheduler//")
    cal.add("version", "2.0")

    for item in data.events:
        event = Event()
        start_dt = datetime.combine(item.date, time.fromisoformat(item.start_time)).astimezone(timezone("Asia/Seoul"))
        end_dt = datetime.combine(item.date, time.fromisoformat(item.end_time)).astimezone(timezone("Asia/Seoul"))

        event.add("summary", item.summary)
        event.add("dtstart", start_dt)
        event.add("dtend", end_dt)
        event.add("location", item.location or "")
        event.add("description", item.description or "")

        # 참석자 정보 추가 (있을 경우)
        if item.attendees:
            for attendee_email in item.attendees:
                attendee = vCalAddress(f"mailto:{attendee_email}")
                attendee.params["cn"] = vText(attendee_email.split("@")[0])
                attendee.params["ROLE"] = vText("REQ-PARTICIPANT")
                attendee.params["RSVP"] = vText("TRUE")
                event.add("attendee", attendee)

        cal.add_component(event)

    ics_content = cal.to_ical()

    # 파일 저장
    filename = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
    file_path = os.path.join(SAVE_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(ics_content)

    # 파일 응답
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )