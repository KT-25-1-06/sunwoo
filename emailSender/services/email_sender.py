import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def send_email_with_attachment(to_email: str, file_path: str, subject: str = "일정 파일 전달드립니다"):
    reg = r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$"
    if not re.match(reg, to_email):
        raise ValueError("유효하지 않은 이메일 주소입니다.")

    my_email = os.getenv("MY_EMAIL")
    my_password = os.getenv("MY_PASSWORD")

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = my_email
    msg["To"] = to_email

    body = MIMEText("안녕하세요,\n일정 파일을 첨부해드립니다.\n감사합니다.", "plain")
    msg.attach(body)

    filename = Path(file_path).name
    with open(file_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(my_email, my_password)
    smtp.sendmail(my_email, to_email, msg.as_string())
    smtp.quit()
