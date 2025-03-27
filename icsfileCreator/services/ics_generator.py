from ics import Calendar, Event, DisplayAlarm
from datetime import timedelta
from models import Schedule
import uuid


def create_ics_file(schedule: Schedule) -> str:
    cal = Calendar()
    for item in schedule.events:
        e = Event()
        e.name = item.title
        e.begin = item.start
        e.end = item.end
        e.location = item.location
        e.description = item.description
        if item.alarm_minutes_before:
            e.alarms.append(DisplayAlarm(trigger=timedelta(minutes=-item.alarm_minutes_before)))
        cal.events.add(e)

    filename = f"{uuid.uuid4()}.ics"
    filepath = f"./icsfiles/{filename}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(cal)

    return filepath