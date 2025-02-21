from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ServiceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_SERVICE: _ClassVar[ServiceType]
    GATEWAY_SERVICE: _ClassVar[ServiceType]
    SESSION_SERVICE: _ClassVar[ServiceType]
    CHARACTER_SERVICE: _ClassVar[ServiceType]
    SYSTEM_SERVICE: _ClassVar[ServiceType]
    CHATTER_SERVICE: _ClassVar[ServiceType]

class SessionMessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN_MESSAGE_TYPE: _ClassVar[SessionMessageType]
    START: _ClassVar[SessionMessageType]
    STOP: _ClassVar[SessionMessageType]
    LOGIN: _ClassVar[SessionMessageType]
    LOGOUT: _ClassVar[SessionMessageType]
    CHARACTER_STATIC_INFO: _ClassVar[SessionMessageType]
    CHARACTER_LIVE_INFO: _ClassVar[SessionMessageType]
    SYSTEM_STATIC_INFO: _ClassVar[SessionMessageType]
    SYSTEM_LIVE_INFO: _ClassVar[SessionMessageType]
    CHATTER: _ClassVar[SessionMessageType]
UNKNOWN_SERVICE: ServiceType
GATEWAY_SERVICE: ServiceType
SESSION_SERVICE: ServiceType
CHARACTER_SERVICE: ServiceType
SYSTEM_SERVICE: ServiceType
CHATTER_SERVICE: ServiceType
UNKNOWN_MESSAGE_TYPE: SessionMessageType
START: SessionMessageType
STOP: SessionMessageType
LOGIN: SessionMessageType
LOGOUT: SessionMessageType
CHARACTER_STATIC_INFO: SessionMessageType
CHARACTER_LIVE_INFO: SessionMessageType
SYSTEM_STATIC_INFO: SessionMessageType
SYSTEM_LIVE_INFO: SessionMessageType
CHATTER: SessionMessageType

class TopicMessage(_message.Message):
    __slots__ = ("request_topic", "publish_topic", "subscribe_topic")
    REQUEST_TOPIC_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_TOPIC_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_TOPIC_FIELD_NUMBER: _ClassVar[int]
    request_topic: str
    publish_topic: str
    subscribe_topic: str
    def __init__(self, request_topic: _Optional[str] = ..., publish_topic: _Optional[str] = ..., subscribe_topic: _Optional[str] = ...) -> None: ...

class ServiceStart(_message.Message):
    __slots__ = ("type", "timestamp")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    type: ServiceType
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, type: _Optional[_Union[ServiceType, str]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

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
    __slots__ = ("ok", "character_id", "character_live_info")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    character_live_info: CharacterLiveInfoMessage
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., character_live_info: _Optional[_Union[CharacterLiveInfoMessage, _Mapping]] = ...) -> None: ...

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

class CharacterTopicRequest(_message.Message):
    __slots__ = ("character_id",)
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    def __init__(self, character_id: _Optional[int] = ...) -> None: ...

class CharacterTopicResponse(_message.Message):
    __slots__ = ("ok", "character_id", "character_topics")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_TOPICS_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    character_topics: TopicMessage
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., character_topics: _Optional[_Union[TopicMessage, _Mapping]] = ...) -> None: ...

class ChatterMessage(_message.Message):
    __slots__ = ("character_id", "system_id", "text")
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    character_id: int
    system_id: int
    text: str
    def __init__(self, character_id: _Optional[int] = ..., system_id: _Optional[int] = ..., text: _Optional[str] = ...) -> None: ...

class ChatterTopicRequest(_message.Message):
    __slots__ = ("system_id",)
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    system_id: int
    def __init__(self, system_id: _Optional[int] = ...) -> None: ...

class ChatterTopicResponse(_message.Message):
    __slots__ = ("ok", "system_id", "chatter_topics")
    OK_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    CHATTER_TOPICS_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    system_id: int
    chatter_topics: TopicMessage
    def __init__(self, ok: bool = ..., system_id: _Optional[int] = ..., chatter_topics: _Optional[_Union[TopicMessage, _Mapping]] = ...) -> None: ...

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
    __slots__ = ("ok", "system_id", "system_live_info")
    OK_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    system_id: int
    system_live_info: SystemLiveInfoMessage
    def __init__(self, ok: bool = ..., system_id: _Optional[int] = ..., system_live_info: _Optional[_Union[SystemLiveInfoMessage, _Mapping]] = ...) -> None: ...

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

class SystemTopicRequest(_message.Message):
    __slots__ = ("system_id",)
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    system_id: int
    def __init__(self, system_id: _Optional[int] = ...) -> None: ...

class SystemTopicResponse(_message.Message):
    __slots__ = ("ok", "system_id", "system_topics")
    OK_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_TOPICS_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    system_id: int
    system_topics: TopicMessage
    def __init__(self, ok: bool = ..., system_id: _Optional[int] = ..., system_topics: _Optional[_Union[TopicMessage, _Mapping]] = ...) -> None: ...

class SessionStartRequest(_message.Message):
    __slots__ = ("username",)
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class SessionStartResponse(_message.Message):
    __slots__ = ("ok", "character_id", "session_id", "session_topics")
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_TOPICS_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    character_id: int
    session_id: str
    session_topics: TopicMessage
    def __init__(self, ok: bool = ..., character_id: _Optional[int] = ..., session_id: _Optional[str] = ..., session_topics: _Optional[_Union[TopicMessage, _Mapping]] = ...) -> None: ...

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
    __slots__ = ("type", "character_id", "system_id", "chatter")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    CHATTER_FIELD_NUMBER: _ClassVar[int]
    type: SessionMessageType
    character_id: int
    system_id: int
    chatter: ChatterMessage
    def __init__(self, type: _Optional[_Union[SessionMessageType, str]] = ..., character_id: _Optional[int] = ..., system_id: _Optional[int] = ..., chatter: _Optional[_Union[ChatterMessage, _Mapping]] = ...) -> None: ...

class SessionMessageResponse(_message.Message):
    __slots__ = ("type", "ok", "character_static_info", "character_live_info", "system_static_info", "system_live_info", "chatter")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OK_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_STATIC_INFO_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_STATIC_INFO_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_LIVE_INFO_FIELD_NUMBER: _ClassVar[int]
    CHATTER_FIELD_NUMBER: _ClassVar[int]
    type: SessionMessageType
    ok: bool
    character_static_info: CharacterStaticInfoMessage
    character_live_info: CharacterLiveInfoMessage
    system_static_info: SystemStaticInfoMessage
    system_live_info: SystemLiveInfoMessage
    chatter: ChatterMessage
    def __init__(self, type: _Optional[_Union[SessionMessageType, str]] = ..., ok: bool = ..., character_static_info: _Optional[_Union[CharacterStaticInfoMessage, _Mapping]] = ..., character_live_info: _Optional[_Union[CharacterLiveInfoMessage, _Mapping]] = ..., system_static_info: _Optional[_Union[SystemStaticInfoMessage, _Mapping]] = ..., system_live_info: _Optional[_Union[SystemLiveInfoMessage, _Mapping]] = ..., chatter: _Optional[_Union[ChatterMessage, _Mapping]] = ...) -> None: ...
