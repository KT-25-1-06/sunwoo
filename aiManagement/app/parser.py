from app.openai_client import client
import json
from datetime import datetime

def parse_schedule(content: str) -> dict:
    system_prompt = (
        "다음 이메일 내용에서 회의 일정을 추출하세요. "
        "이메일 내용을 바탕으로 아래와 같은 JSON으로 반환해 주세요. JSON 이외의 문장은 포함하지 마세요. 예시: "
        "{ \"parsedTitle\": \"주간 회의\", \"parsedStartAt\": \"2025-04-02T10:00:00\", \"parsedEndAt\": \"2025-04-02T11:00:00\", \"parsedLocation\": \"회의실 A\" }"
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    )

    print("🔍 GPT 응답:", completion)

    try:
        # GPT 응답에서 JSON 부분만 추출
        content = completion.choices[0].message.content
        # ```json과 ``` 제거
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        raise ValueError(f"GPT 응답이 JSON이 아님: {completion}") from e