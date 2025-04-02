import os
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
import re
import asyncio
from aiokafka import AIOKafkaProducer
import json

from app.database import SessionLocal
from app.utils import save_email_to_db, save_cleaned_email_to_db
from app.events import EmailAnalysisRequestEvent

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def remove_angle_brackets(s):
    return re.sub(r"[<>]", "", s or "")

async def send_email_to_analysis(email_id, subject, body, sender_name, sender_email, to, cc, date):
    # Kafka 프로듀서 생성
    producer = AIOKafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_plain_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_plain_password=os.getenv("KAFKA_SASL_PASSWORD"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    
    # 프로듀서 시작
    await producer.start()
    
    try:
        # 이메일 분석 요청 이벤트 생성
        event = EmailAnalysisRequestEvent(
            email_id=email_id,
            subject=subject,
            body=body,
            sender_name=sender_name,
            sender_email=sender_email,
            to=to,
            cc=cc,
            date=date
        )
        
        # 이메일 분석 요청 발행
        print(f"📤 이메일 분석 요청 발행: email_id={email_id}")
        await producer.send_and_wait("email.analysis.request", event.dict())
        print(f"✅ 이메일 분석 요청 발행 완료: email_id={email_id}")
    finally:
        # 프로듀서 중지
        await producer.stop()

def check_gmail():
    db = SessionLocal()
    try:
        # 메일 수신
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        mail.select("inbox")

        result, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()

        if not mail_ids:
            print("📭 새 메일 없음")
            return

        for i in mail_ids[-10:]:
            result, msg_data = mail.fetch(i, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            sender_name, sender_email = parseaddr(msg.get("From"))
            to_clean = remove_angle_brackets(msg.get("To"))
            cc_clean = remove_angle_brackets(msg.get("Cc"))

            print("\n📨 새 메일 도착!")
            print(" - 제목:", subject)
            print(" - 보낸 사람:", msg.get("From"))
            print(" - 날짜:", msg.get("Date"))

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            # 원본 저장
            email_record = save_email_to_db(
                db=db,
                subject=subject,
                sender=msg.get("From"),
                to=msg.get("To"),
                cc=msg.get("Cc", ""),
                body=body
            )

            # 정제본 저장
            cleaned_email_record = save_cleaned_email_to_db(
                db=db,
                subject=subject,
                sender_name=sender_name,
                sender_email=sender_email,
                to=to_clean,
                cc=cc_clean,
                body=body,
                date=msg.get("Date")
            )

            # 이메일 분석 요청 발행
            asyncio.run(send_email_to_analysis(
                email_id=cleaned_email_record.id,
                subject=subject,
                body=body,
                sender_name=sender_name,
                sender_email=sender_email,
                to=to_clean,
                cc=cc_clean,
                date=msg.get("Date")
            ))

        print("✅ 새 메일 DB 저장 완료")
        mail.logout()

    except Exception as e:
        print("❌ Gmail 확인 중 오류:", e)
    finally:
        db.close()