import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수 로드 시 로그 출력
print("🔍 환경 변수 로드 중...")
print(f"  - KAFKA_BOOTSTRAP_SERVERS: {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
print(f"  - KAFKA_SECURITY_PROTOCOL: {os.getenv('KAFKA_SECURITY_PROTOCOL')}")
print(f"  - KAFKA_SASL_MECHANISM: {os.getenv('KAFKA_SASL_MECHANISM')}")
print(f"  - KAFKA_SASL_USERNAME: {os.getenv('KAFKA_SASL_USERNAME')}")
print(f"  - TOPIC_EMAIL_ANALYSIS_RESULT: {os.getenv('TOPIC_EMAIL_ANALYSIS_RESULT')}")

class Settings:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL")
    SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM")
    SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME")
    SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD")

    TOPIC_EMAIL_ANALYSIS_REQUEST = os.getenv("TOPIC_EMAIL_ANALYSIS_REQUEST")
    TOPIC_EMAIL_ANALYSIS_RESULT = os.getenv("TOPIC_EMAIL_ANALYSIS_RESULT")

settings = Settings()