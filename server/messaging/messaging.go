// Copyright (c) 2025 Jonathon Fletcher
package messaging

import (
	"context"
	"log"
	"os"
	"sync"
	"time"

	"github.com/jonathonfletcher/poqserver/telemetry"
	"github.com/nats-io/nats.go"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/propagation"
)

type MessagingImpl struct {
	nc *nats.Conn
}

var messageState *MessagingImpl
var messageStateOnce sync.Once

func (m *MessagingImpl) Request(ctx context.Context, subj string, data []byte, timeout time.Duration) (*nats.Msg, error) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	span.SetAttributes(attribute.String("nats.topic", subj))

	header := make(nats.Header)
	propagator := propagation.TraceContext{}
	propagator.Inject(ctx, propagation.HeaderCarrier(header))
	return m.nc.RequestMsg(&nats.Msg{
		Subject: subj,
		Header:  header,
		Data:    data,
	}, timeout)
}

func (m *MessagingImpl) Publish(ctx context.Context, subj string, data []byte) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	span.SetAttributes(attribute.String("nats.topic", subj))

	header := make(nats.Header)
	propagator := propagation.TraceContext{}
	propagator.Inject(ctx, propagation.HeaderCarrier(header))
	return m.nc.PublishMsg(&nats.Msg{
		Subject: subj,
		Header:  header,
		Data:    data,
	})
}

func (m *MessagingImpl) PublishWithReply(ctx context.Context, subj string, reply string, data []byte) error {
	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	span.SetAttributes(attribute.String("nats.topic", subj))

	header := make(nats.Header)
	propagator := propagation.TraceContext{}
	propagator.Inject(ctx, propagation.HeaderCarrier(header))
	return m.nc.PublishMsg(&nats.Msg{
		Subject: subj,
		Header:  header,
		Data:    data,
		Reply:   reply,
	})
}

func (m *MessagingImpl) Subscribe(ctx context.Context, subj string, cb func(ctx context.Context, msg *nats.Msg)) (*nats.Subscription, error) {

	sub, err := m.nc.Subscribe(subj, func(msg *nats.Msg) {
		propagator := propagation.TraceContext{}
		ctx := propagator.Extract(context.Background(), propagation.HeaderCarrier(msg.Header))
		cb(ctx, msg)
	})
	return sub, err
}

func (m *MessagingImpl) Shutdown(ctx context.Context) {
	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	_, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	m.nc.Drain()
}

func NewMessaging(ctx context.Context) IMessaging {
	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	_, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	messageStateOnce.Do(func() {
		natsUrl := os.Getenv("NATS_ENDPOINT")
		var natsOps []nats.Option
		nc, err := nats.Connect(natsUrl, natsOps...)
		if err != nil {
			log.Fatal(err)
		}

		messageState = &MessagingImpl{nc: nc}
	})

	return messageState
}
