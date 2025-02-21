// Copyright (c) 2025 Jonathon Fletcher
package telemetry

import (
	"context"
	"log"
	"runtime"
	"strings"
	"sync"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	"go.opentelemetry.io/otel/sdk/trace"
)

type TelemetryService struct {
	tracerProvider *trace.TracerProvider
}

var telemetryResources *resource.Resource
var initTelemetryResourcesOnce sync.Once

func initTelemetryResources() *resource.Resource {
	initTelemetryResourcesOnce.Do(func() {
		extraResources, _ := resource.New(
			context.Background(),
			resource.WithHost(),
			resource.WithHostID(),
			resource.WithOS(),
			resource.WithOSType(),
			resource.WithProcessPID(),
			resource.WithProcessRuntimeDescription(),
			resource.WithProcessRuntimeName(),
			resource.WithProcessRuntimeVersion(),
		)
		telemetryResources, _ = resource.Merge(
			resource.Default(),
			extraResources,
		)
	})
	return telemetryResources
}

func NewTelemetryService(ctx context.Context) ITelemetry {

	exporter, err := otlptracegrpc.New(ctx, otlptracegrpc.WithInsecure())
	// exporter, err := stdouttrace.New(stdouttrace.WithPrettyPrint())
	if err != nil {
		log.Fatalf("otlptracegrpc.New: %v", err)
	}
	tracerProvider := trace.NewTracerProvider(
		trace.WithBatcher(exporter),
		trace.WithResource(initTelemetryResources()))
	otel.SetTracerProvider(tracerProvider)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}))
	return &TelemetryService{tracerProvider: tracerProvider}
}

func (service *TelemetryService) Shutdown(ctx context.Context) {
	if err := service.tracerProvider.Shutdown(ctx); err != nil {
		log.Panicf("Shutdown: %v", err)
	}
}

func GetPackageName() string {
	pc, _, _, _ := runtime.Caller(1)
	funcParts := strings.Split(runtime.FuncForPC(pc).Name(), ".")
	return strings.Join(funcParts[0:2], ".")
}

func GetFunctionName() string {
	pc, _, _, _ := runtime.Caller(1)
	funcParts := strings.Split(runtime.FuncForPC(pc).Name(), ".")
	return funcParts[len(funcParts)-1]
}
