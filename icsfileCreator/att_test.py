from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime, timedelta
from pytz import UTC

cal = Calendar()
event = Event()

event.add("summary", "팀 회의")
event.add("dtstart", datetime(2025, 4, 1, 10, 0, 0, tzinfo=UTC))
event.add("dtend", datetime(2025, 4, 1, 11, 0, 0, tzinfo=UTC))
event.add("dtstamp", datetime.now(UTC))
event.add("location", vText("서울 본사 회의실"))

organizer = vCalAddress("MAILTO:organizer@example.com")
organizer.params["cn"] = vText("Sunwoo")
organizer.params["role"] = vText("CHAIR")
event["organizer"] = organizer

for email in ["alice@example.com", "bob@example.com"]:
    attendee = vCalAddress(f"MAILTO:{email}")
    attendee.params["cn"] = vText(email.split('@')[0])
    attendee.params["RSVP"] = vText("TRUE")
    event.add("attendee", attendee, encode=0)

cal.add_component(event)

with open("group_event.ics", "wb") as f:
    f.write(cal.to_ical())