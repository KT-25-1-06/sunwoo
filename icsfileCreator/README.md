### 실행

./venv/bin/python -m uvicorn main:app --port 8001 --reload

### 테스트 예시

```
http://127.0.0.1:8000/generate-ics
```

```
{
  "events": [
    {
      "summary": "개발 워크숍",
      "date": "2025-04-10",
      "start_time": "10:00",
      "end_time": "16:00",
      "location": "제주 오션뷰 컨퍼런스룸",
      "description": "팀워크 강화 및 워크숍",
      "attendees": ["user1@example.com", "user2@example.com"]
    }
  ]
}
```
