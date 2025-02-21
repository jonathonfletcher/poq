# Copyright (c) 2025 Jonathon Fletcher
import asyncio
import inspect
import logging

import dotenv

import common.messaging
import common.service
import common.telemetry
import common.universe
import poq_pb2 as poq


class ChatterInstance(common.service.ServiceInstance):

    system: common.universe.System

    def __init__(self, msg_service: common.messaging.MessageService, system_id: int, /):
        super().__init__(msg_service)
        self.system_id = system_id
        self.publish_topic = f"PUB.CHATTER.OUT.{self.system_id}"
        self.subscribe_topic = f"PUB.CHATTER.IN.{self.system_id}"
        self.request_topic = None

    async def topics(self) -> poq.TopicMessage:
        return poq.TopicMessage(
            subscribe_topic=self.publish_topic,
            publish_topic=self.subscribe_topic,
            request_topic=self.request_topic)

    @common.telemetry.trace
    async def chatter_inbound_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.ChatterMessage.FromString(payload)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {msg=}")
        await self.msg_service.publish(self.publish_topic, msg.SerializeToString(), False)

    @common.telemetry.trace
    async def start(self):
        await self.msg_service.subscribe(self.subscribe_topic, self.chatter_inbound_cb, False)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system_id}")

    @common.telemetry.trace
    async def stop(self):
        await self.msg_service.unsubscribe(self.subscribe_topic)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system_id}")


class ChatterService(common.service.ServiceManager):

    def __init__(self, msg_service: common.messaging.MessageService, /):
        super().__init__(msg_service, poq.ServiceType.CHATTER_SERVICE)
        self.active_chatters: dict[int, ChatterInstance] = dict()

    @common.telemetry.trace
    async def chatter_topic_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SystemTopicRequest.FromString(payload)

        response = poq.SystemTopicResponse(ok=False, system_id=request.system_id)
        chatter = self.active_chatters.get(request.system_id)

        if chatter is None:
            chatter = ChatterInstance(self.msg_service, request.system_id)
            self.active_chatters[request.system_id] = chatter
            await chatter.start()

        if isinstance(chatter, ChatterInstance):
            response = poq.SystemTopicResponse(ok=True, system_id=request.system_id,
                                               system_topics=await chatter.topics())

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} {response=}")
        return response.SerializeToString()

    @common.telemetry.trace
    async def start(self):
        await super().start()

        await self.msg_service.subscribe("REQ.CHATTER.TOPIC", self.chatter_topic_cb, True)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    @common.telemetry.trace
    async def stop(self):

        await self.msg_service.unsubscribe("REQ.CHATTER.TOPIC")

        for _, session in self.active_chatters.items():
            await session.stop()
        self.active_chatters.clear()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

        await super().stop()


async def async_main(msg_service: common.messaging.MessageService):
    service = ChatterService(msg_service)
    await service.start()
    await msg_service.run()
    await service.stop()


if __name__ == "__main__":
    dotenv.load_dotenv()
    common.telemetry.initialize_telemetry()
    logging.basicConfig(level=logging.INFO)
    msg_service = common.messaging.MessageService()
    asyncio.run(async_main(msg_service))
