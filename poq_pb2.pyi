from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SessionMessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[SessionMessageType]
    START: _ClassVar[SessionMessageType]
    STOP: _ClassVar[SessionMessageType]
    PING: _ClassVar[SessionMessageType]
    PONG: _ClassVar[SessionMessageType]
    LOGIN: _ClassVar[SessionMessageType]
    LOGOUT: _ClassVar[SessionMessageType]
    CHARACTER_STATIC_INFO: _ClassVar[SessionMessageType]
    CHARACTER_LIVE_INFO: _ClassVar[SessionMessageType]
    SYSTEM_STATIC_INFO: _ClassVar[SessionMessageType]
    SYSTEM_LIVE_INFO: _ClassVar[SessionMessageType]
    JOIN_SYSTEM: _ClassVar[SessionMessageType]
    LEAVE_SYSTEM: _ClassVar[SessionMessageType]
    BLEUGH: _ClassVar[SessionMessageType]
UNKNOWN: SessionMessageType
START: SessionMessageType
STOP: SessionMessageType
PING: SessionMessageType
PONG: SessionMessageType
LOGIN: SessionMessageType
LOGOUT: SessionMessageType
CHARACTER_STATIC_INFO: SessionMessageType
CHARACTER_LIVE_INFO: SessionMessageType
SYSTEM_STATIC_INFO: SessionMessageType
SYSTEM_LIVE_INFO: SessionMessageType
JOIN_SYSTEM: SessionMessageType
LEAVE_SYSTEM: SessionMessageType
BLEUGH: SessionMessageType

class ServiceStart(_message.Message):
    __slots__ = ("type", "timestamp")
    class ServiceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[ServiceStart.ServiceType]
        GATEWAY: _ClassVar[ServiceStart.ServiceType]
        SESSION: _ClassVar[ServiceStart.ServiceType]
        CHARACTER: _ClassVar[ServiceStart.ServiceType]
        SYSTEM: _ClassVar[ServiceStart.ServiceType]
    UNKNOWN: ServiceStart.ServiceType
    GATEWAY: ServiceStart.ServiceType
    SESSION: ServiceStart.ServiceType
    CHARACTER: ServiceStart.ServiceType
    SYSTEM: ServiceStart.ServiceType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    type: ServiceStart.ServiceType
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, type: _Optional[_Union[ServiceStart.ServiceType, str]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CharacterStaticInfoMessage(_message.Message):
    __slots__ = ("character_id", "name")
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    name: str
    def __init__(self, character_id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...

class CharacterStaticInfoRequest(_message.Message):
    __slots__ = ("character_id",)
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    def __init__(self, character_id: _Optional[int] = ...) -> None: ...

class CharacterStaticInfoResponse(_message.Message):
    __slots__ = ("ok", "character_static_info")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_STATIC_INFO_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_static_info: CharacterStaticInfoMessage
    def __init__(self, ok: bool = ..., character_static_info: _Optional[_Union[CharacterStaticInfoMessage, _Mapping]] = ...) -> None: ...

class CharacterLiveInfoMessage(_message.Message):
    __slots__ = ("character_id", "system_id", "active")
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    system_id: int
    active: bool
    def __init__(self, character_id: _Optional[int] = ..., system_id: _Optional[int] = ..., active: bool = ...) -> None: ...

class CharacterLiveInfoRequest(_message.Message):
    __slots__ = ("character_id",)
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    def __init__(self, character_id: _Optional[int] = ...) -> None: ...

class CharacterLiveInfoResponse(_message.Message):
    __slots__ = ("ok", "character_id", "character_live_info", "request_topic", "publish_topic", "subscribe_topic")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    REQUEST_TOPIC_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_TOPIC_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_TOPIC_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    character_live_info: CharacterLiveInfoMessage
    request_topic: str
    publish_topic: str
    subscribe_topic: str
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., character_live_info: _Optional[_Union[CharacterLiveInfoMessage, _Mapping]] = ..., request_topic: _Optional[str] = ..., publish_topic: _Optional[str] = ..., subscribe_topic: _Optional[str] = ...) -> None: ...

class CharacterLoginRequest(_message.Message):
    __slots__ = ("character_id",)
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    def __init__(self, character_id: _Optional[int] = ...) -> None: ...

class CharacterLoginResponse(_message.Message):
    __slots__ = ("ok", "character_id", "character_live_info")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    character_live_info: CharacterLiveInfoMessage
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., character_live_info: _Optional[_Union[CharacterLiveInfoMessage, _Mapping]] = ...) -> None: ...

class CharacterLogoutRequest(_message.Message):
    __slots__ = ("character_id",)
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    def __init__(self, character_id: _Optional[int] = ...) -> None: ...

class CharacterLogoutResponse(_message.Message):
    __slots__ = ("ok", "character_id")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ...) -> None: ...

class SystemStaticInfoMessage(_message.Message):
    __slots__ = ("system_id", "name", "neighbours")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NEIGHBOURS_FIELD_NUMBER: _ClassVar[int]
    system_id: int
    name: str
    neighbours: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, system_id: _Optional[int] = ..., name: _Optional[str] = ..., neighbours: _Optional[_Iterable[int]] = ...) -> None: ...

class Universe(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UniverseRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UniverseResponse(_message.Message):
    __slots__ = ("ok", "systems")
    OK_FIELD_NUMBER: _ClassVar[int]
    SYSTEMS_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    systems: _containers.RepeatedCompositeFieldContainer[SystemStaticInfoMessage]
    def __init__(self, ok: bool = ..., systems: _Optional[_Iterable[_Union[SystemStaticInfoMessage, _Mapping]]] = ...) -> None: ...

class SystemStaticInfoRequest(_message.Message):
    __slots__ = ("system_id",)
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    system_id: int
    def __init__(self, system_id: _Optional[int] = ...) -> None: ...

class SystemStaticInfoResponse(_message.Message):
    __slots__ = ("ok", "system_id", "system_static_info")
    OK_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_STATIC_INFO_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    system_id: int
    system_static_info: SystemStaticInfoMessage
    def __init__(self, ok: bool = ..., system_id: _Optional[int] = ..., system_static_info: _Optional[_Union[SystemStaticInfoMessage, _Mapping]] = ...) -> None: ...

class SystemLiveInfoMessage(_message.Message):
    __slots__ = ("system_id", "character_id")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    system_id: int
    character_id: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, system_id: _Optional[int] = ..., character_id: _Optional[_Iterable[int]] = ...) -> None: ...

class SystemLiveInfoRequest(_message.Message):
    __slots__ = ("system_id",)
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    system_id: int
    def __init__(self, system_id: _Optional[int] = ...) -> None: ...

class SystemLiveInfoResponse(_message.Message):
    __slots__ = ("ok", "system_id", "system_live_info", "request_topic", "publish_topic", "subscribe_topic")
    OK_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    REQUEST_TOPIC_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_TOPIC_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_TOPIC_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    system_id: int
    system_live_info: SystemLiveInfoMessage
    request_topic: str
    publish_topic: str
    subscribe_topic: str
    def __init__(self, ok: bool = ..., system_id: _Optional[int] = ..., system_live_info: _Optional[_Union[SystemLiveInfoMessage, _Mapping]] = ..., request_topic: _Optional[str] = ..., publish_topic: _Optional[str] = ..., subscribe_topic: _Optional[str] = ...) -> None: ...

class SystemSetLiveCharacterRequest(_message.Message):
    __slots__ = ("character_id", "system_id", "present")
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    system_id: int
    present: bool
    def __init__(self, character_id: _Optional[int] = ..., system_id: _Optional[int] = ..., present: bool = ...) -> None: ...

class SystemSetLiveCharacterResponse(_message.Message):
    __slots__ = ("ok", "character_id", "system_id")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    system_id: int
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., system_id: _Optional[int] = ...) -> None: ...

class SessionStartRequest(_message.Message):
    __slots__ = ("username",)
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class SessionStartResponse(_message.Message):
    __slots__ = ("ok", "character_id", "request_topic", "publish_topic", "subscribe_topic", "session_id")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_TOPIC_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_TOPIC_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_TOPIC_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    request_topic: str
    publish_topic: str
    subscribe_topic: str
    session_id: str
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., request_topic: _Optional[str] = ..., publish_topic: _Optional[str] = ..., subscribe_topic: _Optional[str] = ..., session_id: _Optional[str] = ...) -> None: ...

class SessionStopRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class SessionStopResponse(_message.Message):
    __slots__ = ("ok", "session_id")
    OK_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    session_id: str
    def __init__(self, ok: bool = ..., session_id: _Optional[str] = ...) -> None: ...

class SessionPing(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class SessionPong(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class SessionMessageRequest(_message.Message):
    __slots__ = ("type", "character_id", "system_id")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    type: SessionMessageType
    character_id: int
    system_id: int
    def __init__(self, type: _Optional[_Union[SessionMessageType, str]] = ..., character_id: _Optional[int] = ..., system_id: _Optional[int] = ...) -> None: ...

class SessionMessageResponse(_message.Message):
    __slots__ = ("type", "ok", "pingpong", "character_static_info", "character_live_info", "system_static_info", "system_live_info")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OK_FIELD_NUMBER: _ClassVar[int]
    PINGPONG_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_STATIC_INFO_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_STATIC_INFO_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    type: SessionMessageType
    ok: bool
    pingpong: int
    character_static_info: CharacterStaticInfoMessage
    character_live_info: CharacterLiveInfoMessage
    system_static_info: SystemStaticInfoMessage
    system_live_info: SystemLiveInfoMessage
    def __init__(self, type: _Optional[_Union[SessionMessageType, str]] = ..., ok: bool = ..., pingpong: _Optional[int] = ..., character_static_info: _Optional[_Union[CharacterStaticInfoMessage, _Mapping]] = ..., character_live_info: _Optional[_Union[CharacterLiveInfoMessage, _Mapping]] = ..., system_static_info: _Optional[_Union[SystemStaticInfoMessage, _Mapping]] = ..., system_live_info: _Optional[_Union[SystemLiveInfoMessage, _Mapping]] = ...) -> None: ...
