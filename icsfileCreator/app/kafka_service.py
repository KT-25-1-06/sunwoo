import asyncio
import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.events import (CalendarIcsCreatedEvent, CalendarSubscriptionCreatedEvent,
                    CalendarSubscriptionDeletedEvent)

from settings import settings


class KafkaService:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.producer = None
        self.consumer = None

    async def start(self):
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

        self.consumer = AIOKafkaConsumer(
            settings.TOPIC_CALENDAR_ICS_CREATE,
            settings.TOPIC_CALENDAR_ICS_DELETE,
            settings.TOPIC_SCHEDULE_CREATE,
            loop=self.loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="icsfile-service",
            security_protocol=settings.SECURITY_PROTOCOL,
            sasl_mechanism=settings.SASL_MECHANISM,
            sasl_plain_username=settings.SASL_USERNAME,
            sasl_plain_password=settings.SASL_PASSWORD,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()

    async def stop(self):
        await self.producer.stop()
        await self.consumer.stop()

    async def produce_calendar_ics_created(self, event: CalendarIcsCreatedEvent):
        await self.producer.send_and_wait(
            settings.TOPIC_CALENDAR_ICS_CREATED, json.dumps(event.dict())
        ) 

    async def consume_events(self, handler):
        async for msg in self.consumer:
            await handler(msg.topic, msg.value)

kafka_service = KafkaService()