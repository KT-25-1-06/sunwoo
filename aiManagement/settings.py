import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL")
    SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM")
    SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME")
    SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD")

    TOPIC_EMAIL_ANALYSIS_REQUEST = os.getenv("TOPIC_EMAIL_ANALYSIS_REQUEST", "email.analysis.request")

settings = Settings()