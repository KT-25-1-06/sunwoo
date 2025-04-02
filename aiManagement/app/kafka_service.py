import json
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from settings import settings
from app.events import EmailAnalysisRequestEvent, EmailAnalysisResultEvent

class KafkaService:
    def __init__(self):
        print("🔄 Kafka 서비스 초기화")
        self.loop = asyncio.get_event_loop()
        self.producer = None
        self.consumer = None

    async def start(self):
        print(f"📡 Kafka 서버 연결 시도: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        self.producer = AIOKafkaProducer(
            loop=self.loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            security_protocol=settings.SECURITY_PROTOCOL,
            sasl_mechanism=settings.SASL_MECHANISM,
            sasl_plain_username=settings.SASL_USERNAME,
            sasl_plain_password=settings.SASL_PASSWORD,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self.producer.start()
        print("✅ Kafka Producer 시작")

        self.consumer = AIOKafkaConsumer(
            settings.TOPIC_EMAIL_ANALYSIS_REQUEST,
            loop=self.loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="ai-management-service",
            security_protocol=settings.SECURITY_PROTOCOL,
            sasl_mechanism=settings.SASL_MECHANISM,
            sasl_plain_username=settings.SASL_USERNAME,
            sasl_plain_password=settings.SASL_PASSWORD,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        print(f"✅ Kafka Consumer 시작 (구독 토픽: {settings.TOPIC_EMAIL_ANALYSIS_REQUEST})")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            print("⏹️ Kafka Producer 중지")
        if self.consumer:
            await self.consumer.stop()
            print("⏹️ Kafka Consumer 중지")

    async def produce_email_analysis_result(self, event: EmailAnalysisResultEvent):
        print(f"📤 분석 결과 발행 시도: email_id={event.email_id}")
        # 이메일 분석 결과를 email.analysis.result 토픽으로 발행
        await self.producer.send_and_wait(
            "email.analysis.result", event.dict()
        )
        print(f"✅ 분석 결과 발행 완료: email_id={event.email_id}")

    async def consume_events(self, handler):
        print("🔄 메시지 수신 대기 시작...")
        async for msg in self.consumer:
            print(f"📨 메시지 수신: {msg.topic}")
            await handler(msg.topic, msg.value)

kafka_service = KafkaService()