import itertools
import asyncio
import inspect
import logging
import sys

import dotenv
import google.protobuf.message
import grpc.aio

import common.telemetry
import common.universe
import poq_pb2 as poq
import poq_pb2_grpc as poq_grpc


class QueueIterator:

    eof = object()

    def __init__(self, /):
        self.q = asyncio.Queue()

    def __aiter__(self):
        return self

    async def __anext__(self):
        n = await self.q.get()
        if n is self.eof:
            raise StopAsyncIteration
        return n

    async def put(self, message: google.protobuf.message.Message, /):
        await self.q.put(message)

    async def close(self, /):
        await self.q.put(self.eof)


class ClientSessionState:

    character_id: int
    active: bool
    system_id: int
    locals: set[int]
    session_id: str

    def __init__(self, character_id: int, session_id: str, universe: dict[int, common.universe.System], /):
        self.active = False
        self.character_id = character_id
        self.system_id = 0
        self.locals = set()
        self.session_id = session_id

    @property
    def metadata(self) -> dict:
        return {'x-session-id': self.session_id}

    def __repr__(self):
        if self.active:
            return f"{self.__class__.__name__}(character_id:{self.character_id}, active:{self.active}, system_id:{self.system_id})"
        else:
            return f"{self.__class__.__name__}(character_id:{self.character_id}, active:{self.active})"


class Client:

    username: str
    endpoint: str

    def __init__(self, username: str, /):
        self.logger = logging.getLogger()
        self.username = username
        self.endpoint = "127.0.0.1:50051"

        pass

    async def stream_task(self, to_client: QueueIterator, from_server, /):
        try:
            async for e in from_server:
                await to_client.put(e)
        except asyncio.CancelledError:
            pass
        await to_client.close()

    async def on_message_login(self, event: poq.SessionMessageResponse, state: ClientSessionState, to_server: QueueIterator, /):
        state.character_id = event.character_live_info.character_id
        state.system_id = event.character_live_info.system_id
        state.active = True
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {state!s}")

        chatter_msg = poq.ChatterMessage(character_id=state.character_id, system_id=state.system_id, text="HELLO WORLD")
        msg = poq.SessionMessageRequest(type=poq.SessionMessageType.CHATTER, chatter=chatter_msg)
        await to_server.put(msg)
        return True

    async def on_message_character_static_info(self, event: poq.SessionMessageResponse, state: ClientSessionState, to_server: QueueIterator, /):
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {event=}")
        return True

    async def on_message_character_live_info(self, event: poq.SessionMessageResponse, state: ClientSessionState, to_server: QueueIterator, /):
        if event.character_live_info.character_id == state.character_id:
            state.character_id = event.character_live_info.character_id
            state.system_id = event.character_live_info.system_id
            self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {state!s}")
        else:
            self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: character_id:{event.character_live_info.character_id}, active:{event.character_live_info.active}")
        return True

    async def on_message_system_live_info(self, event: poq.SessionMessageResponse, state: ClientSessionState, to_server: QueueIterator, /):
        system_locals = frozenset(event.system_live_info.character_id)
        if system_locals != state.locals:
            self.logger.info(
                f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}:"
                f" system_id:{event.system_live_info.system_id},"
                f" arrived:{sorted(list(system_locals.difference(state.locals)))}"
                f" departed:{sorted(list(state.locals.difference(system_locals)))}")
            state.locals = system_locals
        return True

    async def on_message_chatter(self, event: poq.SessionMessageResponse, state: ClientSessionState, to_server: QueueIterator, /):
        if event.chatter:
            if state.character_id != event.chatter.character_id:
                self.logger.info(
                    f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}:"
                    f" system_id:{event.chatter.system_id},"
                    f" character_id:{event.chatter.character_id},"
                    f" text:{event.chatter.text}")
        return True

    async def on_message_default(self, event: poq.SessionMessageResponse, state: ClientSessionState, to_server: QueueIterator, /):
        self.logger.error(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {event=}")
        return True

    async def chatter_task(self, queue: QueueIterator, state: ClientSessionState, interval: int, /):
        counter = itertools.count(1)
        while True:
            await asyncio.sleep(interval)
            chatter_msg = poq.ChatterMessage(character_id=state.character_id, system_id=state.system_id, text=f"{state.character_id} says #{next(counter)}")
            msg = poq.SessionMessageRequest(type=poq.SessionMessageType.CHATTER, chatter=chatter_msg)
            await queue.put(msg)

    async def session(self, channel: grpc.aio.Channel, stub: poq_grpc.PoQStub, state: ClientSessionState, /):
        to_server = QueueIterator()
        to_client = QueueIterator()

        session_task = asyncio.create_task(self.stream_task(to_client, stub.StreamSession(to_server, metadata=tuple(state.metadata.items()))))
        tasklist = list()

        chatter_task = asyncio.create_task(self.chatter_task(to_server, state, 25))

        await to_server.put(poq.SessionMessageRequest(type=poq.SessionMessageType.LOGIN))
        dispatch_table = {
            poq.SessionMessageType.LOGIN: self.on_message_login,
            poq.SessionMessageType.CHARACTER_STATIC_INFO: self.on_message_character_static_info,
            poq.SessionMessageType.CHARACTER_LIVE_INFO: self.on_message_character_live_info,
            poq.SessionMessageType.SYSTEM_LIVE_INFO: self.on_message_system_live_info,
            poq.SessionMessageType.CHATTER: self.on_message_chatter,
        }
        async for in_event in to_client:
            handler_function = dispatch_table.get(in_event.type, self.on_message_default)
            if not await handler_function(in_event, state, to_server):
                await to_server.put(poq.SessionMessageRequest(type=poq.SessionMessageType.LOGOUT))
                break

        await to_server.put(poq.SessionMessageRequest(type=poq.SessionMessageType.LOGOUT))
        if len(tasklist) > 0:
            await asyncio.gather(*tasklist)

        chatter_task.cancel()

        # character_task.cancel()
        session_task.cancel()
        pass

    async def universe(self, channel: grpc.aio.Channel, stub: poq_grpc.PoQStub, /):
        r: poq.UniverseResponse = await stub.GetUniverse(poq.UniverseRequest())
        if r.ok:
            u = dict()
            for s in r.systems:
                s: poq.SystemStaticInfoMessage
                u[s.system_id] = common.universe.System(system_id=s.system_id, name=s.name, neighbours=frozenset(s.neighbours))
            return u
        return None

    async def run(self):
        async with grpc.aio.insecure_channel(self.endpoint) as channel:
            stub = poq_grpc.PoQStub(channel)
            session: poq.SessionStartResponse = await stub.StartSession(poq.SessionStartRequest(username=self.username))
            if session.ok:
                universe = await self.universe(channel, stub)
                print(f"{universe=}")

                state = ClientSessionState(session.character_id, session.session_id, universe)
                await self.session(channel, stub, state)
            print(f"{session=}")
            pass
        pass


class Player:

    username: str

    def __init__(self, username: str):
        self.username = username

    async def play(self):
        client = Client(self.username)
        await client.run()


async def async_main(username: str, /):
    client = Player(username)
    await client.play()


if __name__ == "__main__":
    dotenv.load_dotenv()
    common.telemetry.initialize_telemetry()
    logging.basicConfig(level=logging.INFO)
    username = "userone"
    if len(sys.argv) > 1:
        username = sys.argv[-1]
    asyncio.run(async_main(username))
