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


class CharacterInstance(common.service.ServiceInstance):

    character_id: int
    system_id: int

    def __init__(self, msg_service: common.messaging.MessageService, character_id: int, name: str, /):
        super().__init__(msg_service)
        self.character_id = character_id
        self.name = name
        self.system_id = 1
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: DEFAULT system_id:{self.system_id}")
        self.publish_topic = f"PUB.CHARACTER.OUT.{self.character_id}"
        self.subscribe_topic = f"PUB.CHARACTER.IN.{self.character_id}"
        self.request_topic = f"REQ.CHARACTER.LIVE.{self.character_id}"

    async def topics(self) -> poq.TopicMessage:
        return poq.TopicMessage(
            subscribe_topic=self.publish_topic,
            publish_topic=self.subscribe_topic,
            request_topic=self.request_topic)

    async def static_info(self) -> poq.CharacterStaticInfoMessage:
        return poq.CharacterStaticInfoMessage(character_id=self.character_id, name=self.name)

    async def live_info(self, active=True) -> poq.CharacterLiveInfoMessage:
        return poq.CharacterLiveInfoMessage(character_id=self.character_id, system_id=self.system_id, active=active)

    @common.telemetry.trace
    async def character_live_request_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.CharacterLiveInfoRequest.FromString(payload)
        response = poq.CharacterLiveInfoResponse(ok=False, character_id=request.character_id)

        if request.character_id == self.character_id:
            character_live_info = await self.live_info()
            response = poq.CharacterLiveInfoResponse(ok=True, character_id=self.character_id,
                character_live_info=character_live_info)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {response=}")
        return response.SerializePartialToString()

    @common.telemetry.trace
    async def _update_system_presence(self, present: bool):
        request_msg = poq.SystemTopicRequest(system_id=self.system_id)
        response_bytes = await self.msg_service.publish("REQ.SYSTEM.TOPIC", request_msg.SerializeToString(), True)
        if response_bytes:
            response_msg = poq.SystemTopicResponse.FromString(response_bytes)
            if isinstance(response_msg, poq.SystemTopicResponse):
                system_topics = response_msg.system_topics
                system_set_presence_msg = poq.SystemSetLiveCharacterRequest(character_id=self.character_id, system_id=self.system_id, present=present)
                await self.msg_service.publish(system_topics.publish_topic, system_set_presence_msg.SerializeToString(), False)

    @common.telemetry.trace
    async def character_sub_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.SessionMessageRequest.FromString(payload)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {msg=}")
        pass

    @common.telemetry.trace
    async def start(self):
        await self.msg_service.subscribe(self.request_topic, self.character_live_request_cb, True)
        await self.msg_service.subscribe(self.subscribe_topic, self.character_sub_cb, False)

        live_info_msg = await self.live_info()
        await self.msg_service.publish(self.publish_topic, live_info_msg.SerializeToString(), False)

        await self._update_system_presence(True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: character_id:{self.character_id}")
        pass

    @common.telemetry.trace
    async def stop(self):
        await self._update_system_presence(False)

        live_info_msg = await self.live_info(active=False)
        await self.msg_service.publish(self.publish_topic, live_info_msg.SerializeToString(), False)

        await self.msg_service.unsubscribe(self.subscribe_topic)
        await self.msg_service.unsubscribe(self.request_topic)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: character_id:{self.character_id}")


class CharacterService(common.service.ServiceManager):

    def __init__(self, msg_service: common.messaging.MessageService, characters: dict[int, common.universe.Character], /):
        super().__init__(msg_service, poq.ServiceType.CHARACTER_SERVICE)
        self.character_static_info = characters
        self.active_character_id: dict[int, CharacterInstance] = dict()

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
            character = CharacterInstance(self.msg_service, character_id, character_static_info.name)
            self.active_character_id[character_id] = character
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
    async def character_topic_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.CharacterTopicRequest.FromString(payload)

        response = poq.CharacterTopicResponse(ok=False, character_id=request.character_id)
        character = self.active_character_id.get(request.character_id)
        if isinstance(character, CharacterInstance):
            response = poq.CharacterTopicResponse(ok=True, character_id=request.character_id,
                                               character_topics=await character.topics())

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} {response=}")
        return response.SerializeToString()

    @common.telemetry.trace
    async def start(self):
        await super().start()

        await self.msg_service.subscribe("REQ.CHARACTER.STATIC", self.character_static_info_cb, True)
        await self.msg_service.subscribe("REQ.CHARACTER.LOGIN", self.character_login_cb, True)
        await self.msg_service.subscribe("REQ.CHARACTER.LOGOUT", self.character_logout_cb, True)
        await self.msg_service.subscribe("REQ.CHARACTER.TOPIC", self.character_topic_cb, True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    @common.telemetry.trace
    async def stop(self):

        await self.msg_service.unsubscribe("REQ.CHARACTER.TOPIC")
        await self.msg_service.unsubscribe("REQ.CHARACTER.LOGOUT")
        await self.msg_service.unsubscribe("REQ.CHARACTER.LOGIN")
        await self.msg_service.unsubscribe("REQ.CHARACTER.STATIC")

        for _, session in self.active_character_id.items():
            await session.stop()
        self.active_character_id.clear()

        await super().stop()
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
