# PoQ: Proof of Quoncept - TODO


### Data / Messages

- Separate schemes for Internal / External messages. Make it harder for internal-specific messages to reach the external client.

### Middleware

- Implement subscriber manager so there is at most one NATS subscription per topic per process with a set of channels to trigger the application-level callbacks.

### Telemetry

- Increase coverage

### Services

- Separate the LiveInfo requests from the topic requests. Change the operating model to request the LiveInfo topics for a service instance, subscribe as needed, then finally request the LiveInfo status in case we missed an update.


### Functionality

- Implement LiveInfo subscriptions to the set CharacterID in the current room.
- Implement Room Moves.

