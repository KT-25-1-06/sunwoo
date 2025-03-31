import os
import imaplib
import email
from email.header import decode_header

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def check_gmail():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        mail.select("inbox")

        result, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()

        for i in mail_ids[-10:]:
            result, msg_data = mail.fetch(i, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            print("\n📨 새 메일 도착!")
            print(" - 제목:", subject)
            print(" - 보낸 사람:", msg.get("From"))
            print(" - 날짜:", msg.get("Date"))

        mail.logout()

    except Exception as e:
        print("Gmail 확인 중 오류:", e)