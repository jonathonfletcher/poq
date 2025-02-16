import functools
import inspect
import typing

import opentelemetry.exporter.otlp.proto.grpc.trace_exporter
import opentelemetry.exporter.otlp.proto.http.trace_exporter
import opentelemetry.instrumentation
import opentelemetry.instrumentation.grpc
import opentelemetry.sdk.resources
import opentelemetry.sdk.trace
import opentelemetry.sdk.trace.export
import opentelemetry.semconv.resource
import opentelemetry.trace

_OTEL_INITIALIZED: bool = False


def initialize_telemetry() -> opentelemetry.trace.Tracer:

    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED is False:
        trace_exporter = opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter()

        span_processor = opentelemetry.sdk.trace.export.BatchSpanProcessor(trace_exporter)

        trace_provider = opentelemetry.sdk.trace.TracerProvider()

        trace_provider.add_span_processor(span_processor)

        opentelemetry.trace.set_tracer_provider(trace_provider)

        instrumentor = opentelemetry.instrumentation.grpc.GrpcInstrumentorClient()
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument()

        _OTEL_INITIALIZED = True

    return opentelemetry.trace.get_tracer_provider().get_tracer(__name__)


def trace(func: typing.Callable):

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def asyncwrapfn(*args, **kwargs):
            tracer = opentelemetry.trace.get_tracer_provider().get_tracer(func.__module__)
            with tracer.start_as_current_span(func.__qualname__) as span:
                try:
                    return await func(*args, **kwargs)
                except Exception as ex:
                    span.record_exception(ex)
                    raise ex

        return asyncwrapfn

    else:

        @functools.wraps(func)
        def wrapfn(*args, **kwargs):
            tracer = opentelemetry.trace.get_tracer_provider().get_tracer(func.__module__)
            with tracer.start_as_current_span(func.__qualname__) as span:
                try:
                    return func(*args, **kwargs)
                except Exception as ex:
                    span.record_exception(ex)
                    raise ex

        return wrapfn
