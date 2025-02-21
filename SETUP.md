# PoQ: Proof of Quoncept - Setup

## Requirements:

See the `.env` file in base of the repo. `NATS_ENDPOINT` and `OTEL_EXPORTER_OTLP_ENDPOINT` have to be valid nats server (no tls) and collectors (no tls).

### NATS

nats server configured to allow the default user to publish to "PUB.>" and "REQ.>", and subscribe to "PUB.>", "REQ.>", and "INBOX.>":

```
accounts: {
  POQ: {
    POQ_DEFAULT: {
      publish: [ "PUB.>", "REQ.>" ]
      subscribe: [ "PUB.>", "REQ.>", "_INBOX.>" ]
      allow_responses: true
    }
    users = [
      { user: "default", permissions: $POQ_DEFAULT }
    ]
  }
  SYS: {
    users = [
      { user: "sys", password: "##YOUR_SYS_PASSWORD_HERE##" }
    ]
  }
}
system_account: SYS
no_auth_user: "default"
```

### Telemetry

a collector with a basic config, including setting the apikey for honeycomb:

```
extensions:         

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 127.0.0.1:4317
      http:
        endpoint: 127.0.0.1:4318

processors:
  batch:
    timeout: 15s

exporters:
  otlp/honeycomb:
    endpoint: "api.honeycomb.io:443"
    headers:
        "x-honeycomb-team": "##YOUR_API_KEY_HERE##"

service:
  pipelines:
    traces/honeycomb:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/honeycomb]
    metrics/honeycomb:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/honeycomb]
    logs/honeycomb:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/honeycomb]

  extensions: []
```


### Python

```
python3 -m venv ./python-env
. ./python-env/bin/activate
pip install -r requirements.txt
```


## Running the PoQ:

1: Services

Four terminals, one for each of SessionService / SystemService / CharacterService / ChatterService

```shell
. ./python-env/bin/activate
env PYTHONPATH=${PWD} python services/session_service.py
```

(SessionService will read `accounts.json` for the valid username / character_id mapping)

```shell
. ./python-env/bin/activate
env PYTHONPATH=${PWD} python services/system_service.py
```

(SystemService will read `universe.json` for the valid sysem_id / static info)

```shell
. ./python-env/bin/activate
env PYTHONPATH=${PWD} python services/character_service.py
```

(CharacterService will read `characters.json` for the valid character_id / static info)


```shell
. ./python-env/bin/activate
env PYTHONPATH=${PWD} python services/chatter_service.py
```

2: Server

```shell
cd ./server
go mod tidy
go run .
```

3: Client

```shell
. ./python-env/bin/activate
env PYTHONPATH=${PWD} python client/main.py <username>
```

.. where username is one of the valid usernames. 
Run more than one client at the same time (different terminals).


## Updating the Protobug / gRPC

```shell
. ./python-env/bin/activate
python -m grpc_tools.protoc -I=proto \
    --go_out=./server --go-grpc_out=./server \
    --python_out=. --pyi_out=. --grpc_python_out=. \
    proto/poq.proto
```
