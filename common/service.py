import inspect
import logging

import google.protobuf.timestamp_pb2

import common.messaging
import poq_pb2 as poq


class ServiceInstance:

    msg_service: common.messaging.MessageService
    logger: logging.Logger

    def __init__(self, msg_service: common.messaging.MessageService, /):
        self.msg_service = msg_service
        self.logger = logging.getLogger()

    async def start(self):
        pass

    async def stop(self):
        pass


class ServiceManager:

    msg_service: common.messaging.MessageService
    logger: logging.Logger
    service_type: poq.ServiceType

    def __init__(self, msg_service: common.messaging.MessageService, service_type: poq.ServiceType, /):
        self.msg_service = msg_service
        self.service_type = service_type
        self.logger = logging.getLogger()

    async def service_startup_cb(self, topic: str, payload: bytes, /) -> bytes:
        msg = poq.ServiceStart.FromString(payload)
        ts = msg.timestamp.ToDatetime()
        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}: type:{msg.type}, timestamp:{ts}")

    async def start(self):
        start_msg = poq.ServiceStart(type=self.service_type, timestamp=google.protobuf.timestamp_pb2.Timestamp().GetCurrentTime())
        await self.msg_service.publish("PUB.SERVICE.START", start_msg.SerializeToString(), False)

        await self.msg_service.subscribe("PUB.SERVICE.START", self.service_startup_cb, False)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

    async def stop(self):
        await self.msg_service.unsubscribe("PUB.SERVICE.START")

        stop_msg = poq.ServiceStart(type=self.service_type, timestamp=google.protobuf.timestamp_pb2.Timestamp().GetCurrentTime())

        await self.msg_service.publish("PUB.SERVICE.STOP", stop_msg.SerializeToString(), False)

        self.logger.info(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")

