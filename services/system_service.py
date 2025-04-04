# Copyright (c) 2025 Jonathon Fletcher
import asyncio
import inspect
import json
import logging

import dotenv

import common.messaging
import common.service
import common.telemetry
import common.universe
import poq_pb2 as poq


class SystemInstance(common.service.ServiceInstance):

    system: common.universe.System

    def __init__(self, msg_service: common.messaging.MessageService, system: common.universe.System, /):
        super().__init__(msg_service)
        self.system = system
        self.system_presence = set()
        self.publish_topic = f"PUB.SYSTEM.OUT.{self.system.system_id}"
        self.subscribe_topic = f"PUB.SYSTEM.IN.{self.system.system_id}"
        self.request_topic = f"REQ.SYSTEM.LIVE.{self.system.system_id}"

    async def topics(self) -> poq.TopicMessage:
        return poq.TopicMessage(
            subscribe_topic=self.publish_topic,
            publish_topic=self.subscribe_topic,
            request_topic=self.request_topic)

    async def static_info(self) -> poq.SystemStaticInfoMessage:
        return poq.SystemStaticInfoMessage(system_id=self.system.system_id, name=self.system.name, neighbours=list(self.system.neighbours))

    async def live_info(self) -> poq.SystemLiveInfoMessage:
        return poq.SystemLiveInfoMessage(system_id=self.system.system_id, character_id=list(self.system_presence))

    async def system_live_request_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SystemLiveInfoRequest.FromString(payload)
        response = poq.SystemLiveInfoResponse(ok=False, system_id=request.system_id)

        if request.system_id == self.system.system_id:
            system_live_info = await self.live_info()
            response = poq.SystemLiveInfoResponse(ok=True, system_id=self.system.system_id,
                system_live_info=system_live_info)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} {response=}")

        return response.SerializeToString()

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
        await self.msg_service.subscribe(self.request_topic, self.system_live_request_cb, True)
        await self.msg_service.subscribe(self.subscribe_topic, self.system_in_cb, False)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}")

    @common.telemetry.trace
    async def stop(self):
        await self.msg_service.unsubscribe(self.subscribe_topic)
        await self.msg_service.unsubscribe(self.request_topic)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: system_id:{self.system.system_id}")


class SystemService(common.service.ServiceManager):

    def __init__(self, msg_service: common.messaging.MessageService, universe: dict, /):
        super().__init__(msg_service, poq.ServiceType.SYSTEM_SERVICE)
        self.universe = universe
        self.active_systems: dict[int, SystemInstance] = dict()

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
        await super().start()

        for _, system in self.universe.items():
            s = SystemInstance(self.msg_service, system)
            await s.start()
            self.active_systems[s.system.system_id] = s

        await self.msg_service.subscribe("REQ.SYSTEM.STATIC", self.system_static_info_cb, True)
        await self.msg_service.subscribe("REQ.SYSTEM.TOPIC", self.system_topic_cb, True)

        await self.msg_service.subscribe("REQ.UNIVERSE.STATIC", self.system_universe_cb, True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    @common.telemetry.trace
    async def stop(self):
        await self.msg_service.unsubscribe("REQ.UNIVERSE.STATIC")

        await self.msg_service.unsubscribe("REQ.SYSTEM.TOPIC")
        await self.msg_service.unsubscribe("REQ.SYSTEM.STATIC")

        for _, session in self.active_systems.items():
            await session.stop()
        self.active_systems.clear()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

        await super().stop()


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
