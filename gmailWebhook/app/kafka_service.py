import json
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from settings import settings
from app.events import EmailAnalysisRequestEvent, EmailAnalysisResultEvent, ScheduleCreateEvent
import logging

logger = logging.getLogger(__name__)

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
        if topics:
            print(f"📋 구독 중인 토픽: {topics}")
        else:
            print("⚠️ 구독 중인 토픽이 없습니다.")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()

    async def produce_email_analysis_request(self, event: EmailAnalysisRequestEvent):
        print(f"📤 이메일 분석 요청 발행: email_id={event.email_id}")
        await self.producer.send_and_wait(
            settings.TOPIC_EMAIL_ANALYSIS_REQUEST, event.dict()
        )
        print(f"✅ 이메일 분석 요청 발행 완료: email_id={event.email_id}")

    async def produce_schedule_create(self, event: ScheduleCreateEvent):
        """일정 생성 이벤트를 발행합니다."""
        try:
            await self.producer.send_and_wait(
                settings.TOPIC_SCHEDULE_CREATE,
                event.dict()
            )
            logger.info(f"일정 생성 이벤트 발행 완료: {event.dict()}")
        except Exception as e:
            logger.error(f"일정 생성 이벤트 발행 실패: {str(e)}")
            raise

    async def consume_events(self, handler):
        print("🔄 Kafka 메시지 수신 대기 중...")
        try:
            async for message in self.consumer:
                print(f"📨 메시지 수신: topic={message.topic}, partition={message.partition}, offset={message.offset}, value={message.value}")
                await handler(message.topic, message.value)
        except Exception as e:
            print(f"❌ Kafka 메시지 수신 중 오류: {str(e)}")
            raise e

kafka_service = KafkaService()