import json
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from settings import settings
from app.events import EmailAnalysisRequestEvent, EmailAnalysisResultEvent

class KafkaService:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.producer = None
        self.consumer = None

    async def start(self):
        print(f"🔄 Kafka Producer 시작 중... (bootstrap_servers={settings.KAFKA_BOOTSTRAP_SERVERS})")
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
        print("✅ Kafka Producer 시작 완료")

        print(f"🔄 Kafka Consumer 시작 중... (bootstrap_servers={settings.KAFKA_BOOTSTRAP_SERVERS}, topics={settings.TOPIC_EMAIL_ANALYSIS_RESULT})")
        self.consumer = AIOKafkaConsumer(
            settings.TOPIC_EMAIL_ANALYSIS_RESULT,
            loop=self.loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="gmail-webhook-service",
            security_protocol=settings.SECURITY_PROTOCOL,
            sasl_mechanism=settings.SASL_MECHANISM,
            sasl_plain_username=settings.SASL_USERNAME,
            sasl_plain_password=settings.SASL_PASSWORD,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",  # 가장 오래된 메시지부터 읽기
        )
        await self.consumer.start()
        print(f"✅ Kafka Consumer 시작 완료: {settings.TOPIC_EMAIL_ANALYSIS_RESULT} 토픽 구독 중")
        
        # 구독 중인 토픽 확인
        topics = self.consumer.assignment()
        print(f"📋 구독 중인 토픽: {topics}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            print("✅ Kafka Producer 종료 완료")
        if self.consumer:
            await self.consumer.stop()
            print("✅ Kafka Consumer 종료 완료")

    async def produce_email_analysis_request(self, event: EmailAnalysisRequestEvent):
        print(f"📤 이메일 분석 요청 발행: email_id={event.email_id}")
        await self.producer.send_and_wait(
            settings.TOPIC_EMAIL_ANALYSIS_REQUEST, event.dict()
        )
        print(f"✅ 이메일 분석 요청 발행 완료: email_id={event.email_id}")

    async def consume_events(self, handler):
        print("🔄 Kafka 메시지 수신 대기 중...")
        try:
            async for msg in self.consumer:
                print(f"📨 메시지 수신: topic={msg.topic}, partition={msg.partition}, offset={msg.offset}, value={msg.value}")
                await handler(msg.topic, msg.value)
        except Exception as e:
            print(f"❌ Kafka 메시지 수신 중 오류 발생: {str(e)}")
            # 오류 발생 시 다시 시도
            print("🔄 Kafka 메시지 수신 재시도 중...")
            await asyncio.sleep(5)
            await self.consume_events(handler)

kafka_service = KafkaService()