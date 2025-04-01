import os
from icalendar import Calendar
from sqlalchemy.orm import Session
from app.models import ICSFileBinary


def get_ics_summary(file_id: int, db: Session) -> str:
    ics_file = db.query(ICSFileBinary).filter(ICSFileBinary.id == file_id).first()
    if not ics_file:
        raise ValueError("해당 ID의 ICS 파일이 존재하지 않습니다.")

    try:
        cal = Calendar.from_ical(ics_file.fileData)
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