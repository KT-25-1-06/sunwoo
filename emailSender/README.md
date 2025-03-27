### 실행

./venv/bin/python -m uvicorn main:app --port 8002 --reload

### 테스트 방법

```
http://localhost:8002/send-schedule
```

으로 post

- 예시

```
{
  "schedule": {
    "events": [
      {
        "title": "개발 워크숍",
        "start": "2025-04-10T10:00:00",
        "end": "2025-04-10T16:00:00",
        "location": "제주 오션뷰 컨퍼런스룸",
        "description": "팀워크 강화 및 워크숍",
        "alarm_minutes_before": 120
      }
    ]
  },
  "to_email": "aidnsunwoo@naver.com"
}
```
