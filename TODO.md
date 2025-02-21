# PoQ: Proof of Quoncept - TODO


### Data / Messages

- Separate schemes for Internal / External messages. Make it harder for internal-specific messages to reach the external client.

### Middleware

- Implement subscriber manager so there is at most one NATS subscription per topic per process with a set of channels to trigger the application-level callbacks.

### Telemetry

- Increase coverage

### Functionality

- Implement Room Moves.

