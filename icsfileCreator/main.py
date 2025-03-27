from fastapi import FastAPI
from fastapi.responses import FileResponse
from models import Schedule
from services.ics_generator import create_ics_file

app = FastAPI()

@app.post("/generate-ics")
def generate_ics(schedule: Schedule):
    filepath = create_ics_file(schedule)
    return FileResponse(filepath, filename="schedule.ics", media_type="text/calendar")