import requests

def request_ics_file(schedule: dict) -> str:
    # 바로 schedule을 JSON으로 보내야 함 (wrap하지 말고)
    response = requests.post("http://localhost:8001/generate-ics", json=schedule)

    if response.status_code == 200:
        with open("generated.ics", "wb") as f:
            f.write(response.content)
        return "generated.ics"
    else:
        raise Exception(f"ICS 서버 오류: {response.status_code}, {response.text}")