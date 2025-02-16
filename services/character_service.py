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


class CharacterInstance:

    msg_service: common.messaging.MessageService
    logger: logging.Logger
    character_id: int
    system_id: int

    def __init__(self, msg_service: common.messaging.MessageService, character_id: int, name: str, /):
        self.msg_service = msg_service
        self.logger = logging.getLogger()
        self.character_id = character_id
        self.name = name
        self.system_id = 1
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: DEFAULT system_id:{self.system_id}")
        self.publish_topic = f"PUB.CHARACTER.OUT.{self.character_id}"
        self.subscribe_topic = f"PUB.CHARACTER.IN.{self.character_id}"
        self.request_topic = f"REQ.CHARACTER.STATIC.{self.character_id}"

    @common.telemetry.trace
    async def static_info(self):
        return poq.CharacterStaticInfoMessage(character_id=self.character_id, name=self.name)

    @common.telemetry.trace
    async def live_info(self, active=True):
        return poq.CharacterLiveInfoMessage(character_id=self.character_id, system_id=self.system_id, active=active)

    @common.telemetry.trace
    async def _update_system_presence(self, present: bool):
        system_live_info_request = poq.SystemLiveInfoRequest(system_id=self.system_id)
        payload = await self.msg_service.publish("REQ.SYSTEM.LIVE", system_live_info_request.SerializeToString(), True)
        if payload:
            system_live_info_response = poq.SystemLiveInfoResponse.FromString(payload)
            if isinstance(system_live_info_response, poq.SystemLiveInfoResponse):
                system_set_presence_msg = poq.SystemSetLiveCharacterRequest(character_id=self.character_id, system_id=self.system_id, present=present)
                await self.msg_service.publish(system_live_info_response.publish_topic, system_set_presence_msg.SerializeToString(), False)

    @common.telemetry.trace
    async def character_sub_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.SessionMessageRequest.FromString(payload)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {msg=}")
        pass

    @common.telemetry.trace
    async def start(self):
        await self.msg_service.subscribe(self.subscribe_topic, self.character_sub_cb, False)

        live_info_msg = await self.live_info()
        await self.msg_service.publish(self.publish_topic, live_info_msg.SerializeToString(), False)

        await self._update_system_presence(True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: character_id:{self.character_id}")
        pass

    @common.telemetry.trace
    async def stop(self):
        stop_message = poq.SessionMessageResponse(type=poq.SessionMessageType.STOP)
        await self.msg_service.publish(self.publish_topic, stop_message.SerializeToString(), False)

        await self._update_system_presence(False)

        live_info_msg = await self.live_info(active=False)
        await self.msg_service.publish(self.publish_topic, live_info_msg.SerializeToString(), False)

        await self.msg_service.unsubscribe(self.subscribe_topic)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: character_id:{self.character_id}")


class CharacterService(common.messaging.MessageServiceStub):

    def __init__(self, msg_service: common.messaging.MessageService, characters: dict[int, common.universe.Character], /):
        self.msg_service = msg_service
        self.logger = logging.getLogger()
        self.character_static_info = characters
        self.active_character_id: dict[int, CharacterInstance] = dict()

    async def service_startup_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.ServiceStart.FromString(payload)
        ts = msg.timestamp.ToDatetime()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: type:{msg.type}, timestamp:{ts}")

    @common.telemetry.trace
    async def character_static_info_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.CharacterStaticInfoRequest.FromString(payload)
        character_id = msg.character_id
        character_static_info = self.character_static_info.get(character_id)
        response = poq.CharacterStaticInfoResponse(ok=False)

        if character_static_info:
            response = poq.CharacterStaticInfoResponse(ok=True,
                character_static_info=poq.CharacterStaticInfoMessage(character_id=character_id, name=character_static_info.name))

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {response=}")
        return response.SerializePartialToString()

    @common.telemetry.trace
    async def character_live_info_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.CharacterLiveInfoRequest.FromString(payload)
        character_id = msg.character_id
        character = self.active_character_id.get(character_id)
        response = poq.CharacterLiveInfoResponse(ok=False)

        if character:
            character_live_info = await character.live_info()
            response = poq.CharacterLiveInfoResponse(ok=True,
                character_live_info=character_live_info,
                request_topic=character.request_topic,
                publish_topic=character.subscribe_topic,
                subscribe_topic=character.publish_topic)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {response=}")
        return response.SerializePartialToString()

    @common.telemetry.trace
    async def character_login_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.CharacterLoginRequest.FromString(payload)

        character_id = msg.character_id
        response = poq.CharacterLoginResponse(ok=False, character_id=character_id)

        # Character can only be present once. If we are loggin in again
        # then remove the previous entry.
        previous_character = self.active_character_id.get(character_id)
        if previous_character:
            await previous_character.stop()
            self.active_character_id.pop(character_id)

        character_static_info = self.character_static_info.get(character_id)
        if character_static_info:
            character = self.active_character_id[character_id] = CharacterInstance(self.msg_service, character_id, character_static_info.name)
            await character.start()
            character_live_info = await character.live_info()
            response = poq.CharacterLoginResponse(ok=True, character_id=character.character_id, character_live_info=character_live_info)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {response=}")

        return response.SerializeToString()

    @common.telemetry.trace
    async def character_logout_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.CharacterLogoutRequest.FromString(payload)

        character_id = msg.character_id
        response = poq.CharacterLogoutResponse(ok=False, character_id=character_id)

        character = self.active_character_id.get(character_id)
        if character:
            await character.stop()
            self.active_character_id.pop(character_id)
            response = poq.CharacterLogoutResponse(ok=True)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {msg=}")

        return response.SerializeToString()

    @common.telemetry.trace
    async def start(self):
        start_msg = poq.ServiceStart(type=poq.ServiceStart.ServiceType.CHARACTER, timestamp=google.protobuf.timestamp_pb2.Timestamp().GetCurrentTime())
        await self.msg_service.publish("PUB.SERVICE.START", start_msg.SerializeToString(), False)
        await self.msg_service.subscribe("PUB.SERVICE.START", self.service_startup_cb, False)

        await self.msg_service.subscribe("REQ.CHARACTER.STATIC", self.character_static_info_cb, True)
        await self.msg_service.subscribe("REQ.CHARACTER.LIVE", self.character_live_info_cb, True)
        await self.msg_service.subscribe("REQ.CHARACTER.LOGIN", self.character_login_cb, True)
        await self.msg_service.subscribe("REQ.CHARACTER.LOGOUT", self.character_logout_cb, True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    @common.telemetry.trace
    async def stop(self):
        await self.msg_service.unsubscribe("PUB.SERVICE.START")
        stop_msg = poq.ServiceStart(type=poq.ServiceStart.ServiceType.CHARACTER, timestamp=google.protobuf.timestamp_pb2.Timestamp().GetCurrentTime())
        await self.msg_service.publish("PUB.SERVICE.STOP", stop_msg.SerializeToString(), False)

        await self.msg_service.unsubscribe("REQ.CHARACTER.LOGIN")
        await self.msg_service.unsubscribe("REQ.CHARACTER.LOGOUT")
        await self.msg_service.unsubscribe("REQ.CHARACTER.LIVE")
        await self.msg_service.unsubscribe("REQ.CHARACTER.STATIC")

        for _, session in self.active_character_id.items():
            await session.stop()
        self.active_character_id.clear()

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")


async def async_main(msg_service: common.messaging.MessageService, characters: dict):
    service = CharacterService(msg_service, characters)
    await service.start()
    await msg_service.run()
    await service.stop()


if __name__ == "__main__":
    dotenv.load_dotenv()
    common.telemetry.initialize_telemetry()
    logging.basicConfig(level=logging.INFO)
    characters = dict()
    with open('characters.json', 'r') as ifp:
        for record in json.load(ifp):
            system = common.universe.Character(**record)
            characters[system.character_id] = system
    msg_service = common.messaging.MessageService()
    asyncio.run(async_main(msg_service, characters))
