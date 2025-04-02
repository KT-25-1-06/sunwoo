import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL")
    SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM")
    SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME")
    SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD")

    TOPIC_EMAIL_ANALYSIS_REQUEST = os.getenv("TOPIC_EMAIL_ANALYSIS_REQUEST")
    TOPIC_EMAIL_ANALYSIS_RESULT = os.getenv("TOPIC_EMAIL_ANALYSIS_RESULT")
    TOPIC_SCHEDULE_CREATE = os.getenv("TOPIC_SCHEDULE_CREATE")

    TOPIC_CALENDAR_ICS_CREATE = os.getenv("TOPIC_CALENDAR_ICS_CREATE")
    TOPIC_CALENDAR_ICS_DELETE = os.getenv("TOPIC_CALENDAR_ICS_DELETE")
    TOPIC_CALENDAR_ICS_CREATED = os.getenv("TOPIC_CALENDAR_ICS_CREATED")


settings = Settings()