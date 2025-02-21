# Copyright (c) 2025 Jonathon Fletcher
import asyncio
import enum
import inspect
import logging
import os
import typing

import nats
import nats.aio.client
import nats.aio.errors
import nats.errors
import opentelemetry.context
import opentelemetry.propagate
import opentelemetry.trace


class MessageServiceState(enum.Enum):
    INIT = 0
    CONNECTED = 1
    DISCONNECTED = 2
    CLOSED = 3


class MessageService:

    def __init__(self):
        self.nats_options = {
            "servers": os.environ['NATS_ENDPOINT'],
            "connect_timeout": 15,
            "reconnect_time_wait": 15,
            "max_reconnect_attempts": 100,
            "error_cb": self._nats_error,
            "closed_cb": self._nats_closed,
            "reconnected_cb": self._nats_reconnected,
            "disconnected_cb": self._nats_disconnected,
        }
        self.logger = logging.getLogger()
        self.state = MessageServiceState.INIT
        self.nc = nats.aio.client.Client()
        self.topic_subscriptions: dict[str, nats.aio.client.Subscription] = dict()
        self.topic_callbacks: dict[str, typing.Callable] = dict()
        self.topic_queues: set[str] = set()

    async def _nats_error(self, e, /) -> None:
        self.logger.error(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {e}")

    async def _nats_closed(self, /) -> None:
        self.logger.warning(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")
        self.state = MessageServiceState.CLOSED

    async def _nats_reconnected(self, /) -> None:
        self.logger.warning(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {self.nc.connected_url.netloc}")
        await self.resubscribe()
        self.state = MessageServiceState.CONNECTED

    async def _nats_disconnected(self, /) -> None:
        self.logger.warning(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")
        self.state = MessageServiceState.DISCONNECTED

    async def _nats_message(self, msg: nats.aio.client.Msg, /) -> None:

        context: opentelemetry.trace.Context = None
        if msg.headers:
            headers = {k.lower(): v for k, v in msg.headers.items()}
            propagator = opentelemetry.propagate.get_global_textmap()
            context: opentelemetry.trace.Context = propagator.extract(headers)

        token = opentelemetry.context.attach(context)
        try:
            topic = msg.subject
            cb = self.topic_callbacks.get(topic)
            if cb:
                response = await cb(msg.subject, msg.data)
                if msg.reply:
                    await msg.respond(response)
            else:
                self.logger.error(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {topic=} has no callback")
        finally:
            opentelemetry.context.detach(token)

    async def resubscribe(self, /):
        for topic in self.topic_subscriptions.keys():
            await self.topic_subscriptions[topic].unsubscribe()
        for topic in self.topic_callbacks.keys():
            if topic in self.topic_queues:
                self.topic_subscriptions[topic] = await self.nc.subscribe(f"{topic!s}", f"{topic!s}", cb=self._nats_message)
            else:
                self.topic_subscriptions[topic] = await self.nc.subscribe(f"{topic!s}", cb=self._nats_message)

    async def subscribe(self, topic: str, callback: typing.Callable, isqueue: bool, /) -> bool:
        if topic in self.topic_callbacks:
            return False
        self.topic_callbacks[topic] = callback
        if isqueue:
            self.topic_queues.add(topic)
        if self.state == MessageServiceState.CONNECTED:
            if topic in self.topic_queues:
                self.topic_subscriptions[topic] = await self.nc.subscribe(f"{topic!s}", f"{topic!s}", cb=self._nats_message)
            else:
                self.topic_subscriptions[topic] = await self.nc.subscribe(f"{topic!s}", cb=self._nats_message)
        return True

    async def unsubscribe(self, topic: str, /) -> bool:
        if topic not in self.topic_callbacks:
            return False
        if topic in self.topic_subscriptions:
            await self.topic_subscriptions[topic].unsubscribe()
        if topic in self.topic_callbacks:
            del self.topic_callbacks[topic]
        if topic in self.topic_queues:
            self.topic_queues.remove(topic)
        return True

    async def start(self, /) -> None:
        await self.nc.connect(**self.nats_options)
        self.state = MessageServiceState.CONNECTED
        await self.resubscribe()

    async def stop(self, /) -> None:
        for topic in self.topic_subscriptions.keys():
            await self.topic_subscriptions[topic].unsubscribe()
        try:
            await self.nc.close()
        except nats.errors.FlushTimeoutError as ex:
            self.logger.error(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: {ex!s}")
        self.state = MessageServiceState.CLOSED

    async def run(self, /) -> None:
        event = asyncio.Event()
        await self.start()
        try:
            await event.wait()
        finally:
            pass
        await self.stop()

    async def publish(self, topic: str, payload: bytes, reply: bool, /, headers: dict = None, timeout: int = 10) -> bytes:
        if self.state != MessageServiceState.CONNECTED:
            return None

        tracer = opentelemetry.trace.get_tracer_provider().get_tracer(self.__module__)
        with tracer.start_span(inspect.currentframe().f_code.co_name) as span:
            span.set_attribute("nats.topic", topic)
            span.set_attribute("nats.message.length", len(payload))
            try:
                headers = headers or dict()
                propagator = opentelemetry.propagate.get_global_textmap()
                propagator.inject(headers)
                # opentelemetry.propagate.inject(headers)
                if reply:
                    res = await self.nc.request(topic, payload=payload, headers=headers, timeout=timeout)
                    if res:
                        return res.data
                    else:
                        return b''
                else:
                    return await self.nc.publish(topic, payload=payload, headers=headers)
            except (nats.errors.TimeoutError, nats.errors.NoRespondersError) as ex:
                if span.is_recording():
                    span.record_exception(ex)
                self.logger.error(f"{self.__init__.__class__}.{inspect.currentframe().f_code.co_name}: {ex=}")
            except (nats.errors.Error) as ex:
                if span.is_recording():
                    span.record_exception(ex)
                self.logger.error(f"{self.__init__.__class__}.{inspect.currentframe().f_code.co_name}: {ex=}")
                raise ex
            return None
