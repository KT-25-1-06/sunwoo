import requests

BASE_URL = "http://localhost:8000/api/v1/ics"  # FastAPI 서버 주소

# 1. ICS 파일 생성 (단일 일정용)
def test_create_ics():
    response = requests.post(
        BASE_URL,
        params={
            "is_group": False,
            "schedule_id": 1  # 실제 존재하는 일정 ID로 바꿔줘야 함
        }
    )
    print("CREATE:", response.status_code, response.json())
    return response.json().get("ics_file_id")


# 2. ICS 파일 수정
def test_update_ics(ics_id: int):
    response = requests.put(
        f"{BASE_URL}/{ics_id}",
        json={
            "createdAt": "2025-04-02T12:00:00"
        }
    )
    print("UPDATE:", response.status_code, response.json())


# 3. ICS 파일 삭제
def test_delete_ics(ics_id: int):
    response = requests.delete(f"{BASE_URL}/{ics_id}")
    print("DELETE:", response.status_code, response.json())


if __name__ == "__main__":
    ics_id = test_create_ics()
    if ics_id:
        test_update_ics(ics_id)
        test_delete_ics(ics_id)