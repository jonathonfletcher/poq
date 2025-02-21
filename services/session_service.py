# Copyright (c) 2025 Jonathon Fletcher
import asyncio
import datetime
import hashlib
import inspect
import json
import logging

import dotenv

import common.messaging
import common.service
import common.telemetry
import poq_pb2 as poq


class SessionInstance(common.service.ServiceInstance):

    session_id: str
    character_id: int

    def new_session_id(self, character_id, /) -> str:
        hash = hashlib.sha1()
        hash.update(datetime.datetime.now(tz=datetime.UTC).isoformat().encode())
        hash.update(str(character_id).encode())
        return hash.hexdigest()

    def __init__(self, msg_service: common.messaging.MessageService, character_id: int, /):
        super().__init__(msg_service)
        self.character_id = character_id
        self.session_id = self.new_session_id(self.character_id)
        self.publish_topic = f"PUB.SESSION.OUT.{self.session_id}"
        self.subscribe_topic = f"PUB.SESSION.IN.{self.session_id}"
        self.request_topic = None

    def topics(self) -> poq.TopicMessage:
        return poq.TopicMessage(
            subscribe_topic=self.publish_topic,
            publish_topic=self.subscribe_topic,
            request_topic=self.request_topic)

    @common.telemetry.trace
    async def session_inbound_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.SessionMessageRequest.FromString(payload)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {msg=}")

    @common.telemetry.trace
    async def start(self):
        await self.msg_service.subscribe(self.subscribe_topic, self.session_inbound_cb, False)
        start_message = poq.SessionMessageResponse(type=poq.SessionMessageType.START)
        await self.msg_service.publish(self.publish_topic, start_message.SerializeToString(), False)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: session_id:{self.session_id}")

    @common.telemetry.trace
    async def stop(self):
        stop_message = poq.SessionMessageResponse(type=poq.SessionMessageType.STOP)
        await self.msg_service.publish(self.publish_topic, stop_message.SerializeToString(), False)
        await self.msg_service.unsubscribe(self.subscribe_topic)

        # send character logout - fallback in case the client does not logout themselves
        logoff_message = poq.CharacterLogoutRequest(character_id=self.character_id)
        await self.msg_service.publish("REQ.CHARACTER.LOGOUT", logoff_message.SerializeToString(), False)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: session_id:{self.session_id}")


class SessionService(common.service.ServiceManager):

    def __init__(self, msg_service: common.messaging.MessageService, accounts: dict, /):
        super().__init__(msg_service, poq.ServiceType.SESSION_SERVICE)
        self.accounts = accounts
        self.active_session_id: dict[str, SessionInstance] = dict()
        self.active_character_id: dict[int, str] = dict()
        pass

    @common.telemetry.trace
    async def session_start_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SessionStartRequest.FromString(payload)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {request=}")

        response = poq.SessionStartResponse(ok=False)
        if request.username in self.accounts.keys():
            character_id = self.accounts[request.username]

            # Only one active session per character_id
            previous_session_id = self.active_character_id.get(character_id)
            if previous_session_id:
                previous_session = self.active_session_id.get(previous_session_id)
                if previous_session:
                    await previous_session.stop()
                    self.active_character_id.pop(previous_session.character_id)
                    self.active_session_id.pop(previous_session.session_id)

            # Install new session
            session = SessionInstance(self.msg_service, character_id)
            self.active_session_id[session.session_id] = session
            self.active_character_id[character_id] = session.session_id
            await session.start()

            response = poq.SessionStartResponse(
                ok=True, character_id=character_id,
                session_id=session.session_id,
                session_topics=session.topics())

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {response=}")

        return response.SerializeToString()

    @common.telemetry.trace
    async def session_stop_cb(self, topic: str, payload: bytes, /) -> bytes:
        request = poq.SessionStopRequest.FromString(payload)

        response = poq.SessionStopResponse(ok=False, session_id=request.session_id)
        session = self.active_session_id.get(request.session_id)
        if session:
            await session.stop()
            self.active_character_id.pop(session.character_id)
            self.active_session_id.pop(session.session_id)
            response = poq.SessionStopResponse(ok=True, session_id=request.session_id)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: session_id:{request.session_id}")

        return response.SerializeToString()

    @common.telemetry.trace
    async def start(self):
        await super().start()

        await self.msg_service.subscribe("REQ.SESSION.START", self.session_start_cb, True)
        await self.msg_service.subscribe("REQ.SESSION.STOP", self.session_stop_cb, True)
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    @common.telemetry.trace
    async def stop(self):

        await self.msg_service.unsubscribe("REQ.SESSION.STOP")
        await self.msg_service.unsubscribe("REQ.SESSION.START")

        for _, session in self.active_session_id.items():
            await session.stop()
        self.active_session_id.clear()

        await super().stop()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")


async def async_main(msg_service: common.messaging.MessageService, accounts: dict):
    service = SessionService(msg_service, accounts)
    await service.start()
    await msg_service.run()
    await service.stop()


if __name__ == "__main__":
    dotenv.load_dotenv()
    common.telemetry.initialize_telemetry()
    logging.basicConfig(level=logging.INFO)
    accounts = dict()
    with open('accounts.json', 'r') as ifp:
        for record in json.load(ifp):
            accounts[record['username']] = record['character_id']

    msg_service = common.messaging.MessageService()
    asyncio.run(async_main(msg_service, accounts))
