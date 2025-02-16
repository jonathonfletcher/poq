# PoQ: Proof of Quoncept

## Summary

Proof of concept distributed Client/Server architecture with a client <-> gateway <-> service(s) model.

This is an exploratory prototype. It is **not** production code.

[client](client/) is written in python and uses gRPC to communicate with the [server](server/).

[server](server/) is written in golang and coordinates interaction with the [client](client/) via NATS to various [services](services/).

[services](services/) are written in python and communicate with the [server](server/) and with other [services](services/) via NATS.


Technologies Used:

- [Open Telemetry](https://opentelemetry.io)
- [Nats](https://nats.io)
- [gRPC / Protobuf](https://gRPC.io)
- [Go](https://go.dev)
- [Python](https://www.python.org)

## Architecture Overview

### Middleware

Core NATS Publish / Subscribe. Simple subscriptios are used for updates with multiple consumers. Worker queues and Request / Reply are used for inquiries.

Subscribers are direct - every subscription from a process is a NATS subscription.

Topic Management is based on delegation and on using the middleware to distribute topic information as required. Common topics are hard-wired. Specific topics are communicated overover the common topics via request /r eply. This means that the balance of topic count (low-high) vs subscriber events (high-low) is biased towards more topics / fewer subscribers.

### Telemetry

Telemetry is implemented as code-level tracing (ie function calls etc), not application logic tracing (ie application functionality etc) .. it's less effort for a PoQ.

Trace propagation via the nats msg headers is implemented in go and python.

### Data / Messages

Content messages separate to Request / Reply messages - the content messages can published directly by services (eg LiveInfo).

Separate FooRequest / FooResponse messages for different Foo (Login, Logout, CharacterInfo, SystemInfo, etc).

The same payloads are transmitted over gRPC and Nats. There is no separate - in this poq - of external / internal messages.

### Services

Services are a manager / instance model.

A ServiceInstance manage their own specific state and their own instance-specific topics. 

Service topics are well-known and fixed / constant. ServiceInstance topics are managed via the instance, and can be requested via a request to the Service.
A Service manages a collection of ServiceInstance objects (eg one per CharacterId / SystemId / SessionId) and a set of well-known topics for Request / Reply.
ServiceInstances track their own middleware topics - ie the topic management for a service is contained in the service. 

The Service handles common requests on common (for the service) topic. Replies with information about a ServiceInstance can include the instance-specific topics that can be used for (eg status updates for a specific characerId / systemId / sessionId).

## Client

[Client](client/) is the external end-user. The client knows a username.

At startup the client conencts to the gRPC channel for the [Server](server/) and requests a session (see [SessionService](#session-service)) for the username.

If a session is returned (ie the the username is valid), the client estatblishes a single bidirectional gRPC stream with the server. Aside from some static data, all interation between the client and the service in via this single bidirectional gRPC stream.

When the stream drops, the client is disconnected. This can be triggered by the client or by the server.

With an established stream, the client sends a LOGIN message to the server (see [CharacterService](#character-service)). The client will then receive live updates for the character (characterId) and system (systemId) including the arrival / departure of other characters (ie other clients).


## Server

[Server](server/) acts as the gateway betweeen the external client / end-user and the internal services.

The server tracks distinct clients via the sessionId (which is passed from the client as gRPC metadata for the bidirectional gRPC stream). The server maintains sessionId / systemId / characterId state for the stream. ie that a sessionId has a characterId and that characterId is present in systemId.

The service communicates with the [SessionService](#session-service) for the setup / teardown of the sessionId.

The service communicates with the [CharacterService](#character-service) and [SystemService](#system-service) to provide static data and live updates to the client.

The service is almost entirely a per-session router / dispatcher. See [server/session](server/session/) for the manager / router / handlers.

## Services

[services](services/) are implemented as a Manager / Instance model. eg the SystemService (common messaging topics) manages a collection of SystemInstances - one per systemId - that handle the state of their systemId only (specific messaging topics).

### Session Service

A session is a unique interaction with a client. The SessionService maintains the mapping between a valid username / characterId, manages a collection of SessionInstances (one per sessionId / characterId).

#### SessionService

SessionService manages well-known Request / Reply topics maintains a collection of SessionInstances.

If a session is requested for an invalid username, the response is a rejection.

If a session is requested for a valid inactive username, the response is a new sessionId (and the create / start of a SessionInstance by the manager).

If a session is reqested for a valid active username, the response is the stop the active SessionInstance and create / start a new SeessionInstance for the username.

A mapping of username -> characterid is read from file at startup.

#### SessionInstance

SessionInstance maintains the mapping of a single sessionId / characterId and manages pub / sub / req topics specific to the instance / sessionId.

When a SessionInstance is stopped it sends a LOGOUT message to the CharacerService.

### Character Service

CharacterService maintains state on a characterId, including current systemId and current active state via a set of CharacterInstances.

It provides static data on characters and also provides / publishes live data on active characters.

#### CharacterService

CharacterService manages well-know Request / Reply topics for provide Static and Live info for characterId and also to manage LOGIN / LOGOUT services via CharacterInstances.

A mapping of characterid -> static info is read from file at startup.

#### CharacterInstance

CharacterInstance manages the state for a specific characterId and manages pub / sub / req topics specific to the instance / characterId.

When a CharacterInstance is started / stopped, it communicates with the SystemService to update the presence of the characerId in the correct systemId.

### SystemService

SystemService maintains state on a systemId, including the current set of active characterId in the system via a set of SystemInstances.

It provides static data on systems and also provides / publishes live data on systems.

#### SystemService

A mapping of characterid -> static info is read from file at startup.

#### SystemInstance

SystemInstance manages the state for a specific systemId and manages pub / sub / req topics specific to the instance / systemId.
