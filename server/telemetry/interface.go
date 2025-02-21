// Copyright (c) 2025 Jonathon Fletcher
package telemetry

import "context"

type ITelemetry interface {
	Shutdown(ctx context.Context)
}
