### 실행

./venv/bin/python -m uvicorn main:app --port 8002 --reload

### 테스트 방법

```
http://127.0.0.1:8002/send-ics-email
```

으로 post

- 예시

```
[{"key":"to_email","value":"aidnsunwoo@naver.com","description":"","type":"text","uuid":"fe2106f1-14a0-4224-8b35-4d4cd7bb2584","enabled":true},{"key":"subject","value":"회의 일정","description":"","type":"text","uuid":"0c6e5540-c7fe-4351-8925-f15bd10e6d74","enabled":true},{"key":"message","value":"KT ALP-B ics 자동 변환 서비스입니다.","description":"","type":"text","uuid":"ce82e18b-17b3-4383-b31f-1821aef82f6e","enabled":true},{"key":"ics_content","description":"","type":"file","uuid":"d36ee299-e011-4123-9bfe-1dd0b29a1878","enabled":true,"value":["/Users/sunwoo/Desktop/dev/kt-alpb-2ndproj/emailSender/icsfiles/schedule_20250331_095454.ics"]}]

```
