package telemetry

import "context"

type ITelemetry interface {
	Shutdown(ctx context.Context)
}
