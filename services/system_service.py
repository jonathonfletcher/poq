import asyncio
import inspect
import json
import logging

import dotenv
import google.protobuf.timestamp_pb2

import common.messaging
import common.telemetry
import common.universe
import poq_pb2 as poq


class SystemInstance:

    msg_service: common.messaging.MessageService
    logger: logging.Logger
    system: common.universe.System

    def __init__(self, msg_service: common.messaging.MessageService, system: common.universe.System, /):
        self.msg_service = msg_service
        self.logger = logging.getLogger()
        self.system = system
        self.system_presence = set()
        self.publish_topic = f"PUB.SYSTEM.OUT.{self.system.system_id}"
        self.subscribe_topic = f"PUB.SYSTEM.IN.{self.system.system_id}"
        self.request_topic = f"REQ.SYSTEM.{self.system.system_id}"

    async def topics(self) -> poq.TopicMessage:
        return poq.TopicMessage(
            subscribe_topic=self.publish_topic,
            publish_topic=self.subscribe_topic,
            request_topic=self.request_topic)

    async def static_info(self) -> poq.SystemStaticInfoMessage:
        return poq.SystemStaticInfoMessage(system_id=self.system.system_id, name=self.system.name, neighbours=list(self.system.neighbours))

    async def live_info(self) -> poq.SystemLiveInfoMessage:
        return poq.SystemLiveInfoMessage(system_id=self.system.system_id, character_id=list(self.system_presence))

    @common.telemetry.trace
    async def system_request_cb(self, topic: str, payload: bytes, /) -> bytes:
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}")

    @common.telemetry.trace
    async def system_in_cb(self, topic: str, payload: bytes, /):
        msg = poq.SystemSetLiveCharacterRequest.FromString(payload)
        if not msg.system_id == self.system.system_id:
            self.logger.error(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}, {msg=}")
            return

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}")

        publish_update = False
        if msg.present and msg.character_id not in self.system_presence:
            self.system_presence.add(msg.character_id)
            publish_update = True
        elif msg.character_id in self.system_presence and not msg.present:
            self.system_presence.remove(msg.character_id)
            publish_update = True

        if publish_update:
            live_info = await self.live_info()
            self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {self.publish_topic=}, {live_info=}")
            await self.msg_service.publish(self.publish_topic, live_info.SerializeToString(), False)

    @common.telemetry.trace
    async def start(self):
        await self.msg_service.subscribe(self.request_topic, self.system_request_cb, True)
        await self.msg_service.subscribe(self.subscribe_topic, self.system_in_cb, False)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}")

    @common.telemetry.trace
    async def stop(self):
        await self.msg_service.unsubscribe(f"PUB.SYSTEM.IN.{self.system.system_id}")
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}")


class SystemService(common.messaging.MessageServiceStub):

    def __init__(self, msg_service: common.messaging.MessageService, universe: dict, /):
        self.msg_service = msg_service
        self.logger = logging.getLogger()
        self.universe = universe
        self.active_systems: dict[int, SystemInstance] = dict()

    async def service_startup_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.ServiceStart.FromString(payload)
        ts = msg.timestamp.ToDatetime()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: type:{msg.type}, timestamp:{ts}")

    @common.telemetry.trace
    async def system_static_info_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SystemStaticInfoRequest.FromString(payload)

        response = poq.SystemStaticInfoResponse(ok=False, system_id=request.system_id)
        system = self.active_systems.get(request.system_id)
        if isinstance(system, SystemInstance):
            response = poq.SystemStaticInfoResponse(ok=True, system_id=request.system_id,
                system_static_info=await system.static_info())

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} {response=}")

        return response.SerializeToString()

    @common.telemetry.trace
    async def system_live_info_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SystemLiveInfoRequest.FromString(payload)

        response = poq.SystemLiveInfoResponse(ok=False, system_id=request.system_id)
        system = self.active_systems.get(request.system_id)
        if isinstance(system, SystemInstance):
            system_live_info = await system.live_info()
            response = poq.SystemLiveInfoResponse(ok=True, system_id=request.system_id,
                system_live_info=system_live_info)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} {response=}")

        return response.SerializeToString()

    @common.telemetry.trace
    async def system_topic_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SystemTopicRequest.FromString(payload)

        response = poq.SystemTopicResponse(ok=False, system_id=request.system_id)
        system = self.active_systems.get(request.system_id)
        if isinstance(system, SystemInstance):
            response = poq.SystemTopicResponse(ok=True, system_id=request.system_id,
                                               system_topics=await system.topics())

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} {response=}")
        return response.SerializeToString()

    @common.telemetry.trace
    async def system_universe_cb(self, topic: str, payload: bytes, /) -> bytes:
        _ = poq.UniverseRequest.FromString(payload)

        system_list = list()
        for s in self.universe.values():
            s: common.universe.System
            system_list.append(poq.SystemStaticInfoMessage(system_id=s.system_id, name=s.name, neighbours=list(s.neighbours)))

        response = poq.UniverseResponse(ok=True, systems=list(system_list))

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")
        return response.SerializeToString()

    @common.telemetry.trace
    async def start(self):
        start_msg = poq.ServiceStart(type=poq.ServiceStart.ServiceType.SYSTEM, timestamp=google.protobuf.timestamp_pb2.Timestamp().GetCurrentTime())
        await self.msg_service.publish("PUB.SERVICE.START", start_msg.SerializeToString(), False)
        await self.msg_service.subscribe("PUB.SERVICE.START", self.service_startup_cb, False)

        for _, system in self.universe.items():
            s = SystemInstance(self.msg_service, system)
            await s.start()
            self.active_systems[s.system.system_id] = s

        await self.msg_service.subscribe("REQ.SYSTEM.STATIC", self.system_static_info_cb, True)
        await self.msg_service.subscribe("REQ.SYSTEM.LIVE", self.system_live_info_cb, True)
        await self.msg_service.subscribe("REQ.SYSTEM.TOPIC", self.system_topic_cb, True)
        await self.msg_service.subscribe("REQ.UNIVERSE.STATIC", self.system_universe_cb, True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    @common.telemetry.trace
    async def stop(self):
        await self.msg_service.unsubscribe("REQ.UNIVERSE.STATIC")
        await self.msg_service.unsubscribe("REQ.SYSTEM.TOPIC")
        await self.msg_service.unsubscribe("REQ.SYSTEM.LIVE")
        await self.msg_service.unsubscribe("REQ.SYSTEM.STATIC")

        await self.msg_service.unsubscribe("PUB.SERVICE.START")
        stop_msg = poq.ServiceStart(type=poq.ServiceStart.ServiceType.SYSTEM, timestamp=google.protobuf.timestamp_pb2.Timestamp().GetCurrentTime())
        await self.msg_service.publish("PUB.SERVICE.STOP", stop_msg.SerializeToString(), False)

        for _, session in self.active_systems.items():
            await session.stop()
        self.active_systems.clear()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")


async def async_main(msg_service: common.messaging.MessageService, universe: dict):
    service = SystemService(msg_service, universe)
    await service.start()
    await msg_service.run()
    await service.stop()


if __name__ == "__main__":
    dotenv.load_dotenv()
    common.telemetry.initialize_telemetry()
    logging.basicConfig(level=logging.INFO)
    universe: dict[int, common.universe.System] = dict()
    with open('universe.json', 'r') as ifp:
        for record in json.load(ifp):
            system = common.universe.System(**record)
            universe[system.system_id] = system
    msg_service = common.messaging.MessageService()
    asyncio.run(async_main(msg_service, universe))
