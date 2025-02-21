// Copyright (c) 2025 Jonathon Fletcher
package session

import (
	"context"
	"log"
	"time"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"github.com/nats-io/nats.go"
	"go.opentelemetry.io/otel"
	"google.golang.org/protobuf/proto"
)

type LiveChatterListener struct {
	messaging    messaging.IMessaging
	grpcSendFunc grpcSendHandlerFn
	id           int
	cxl          chan error
}

func (l *LiveChatterListener) Id(context.Context) int {
	return l.id
}

func (l *LiveChatterListener) Shutdown(ctx context.Context) {
	l.cxl <- nil
}

func (l *LiveChatterListener) runLiveChatterInfoListener(ctx context.Context, topic string) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sub, _ := l.messaging.Subscribe(ctx, topic, func(ctx context.Context, msg *nats.Msg) {

		tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
		_, span := tracer.Start(ctx, telemetry.GetFunctionName())
		defer span.End()

		chatterMsg := &poq.ChatterMessage{}
		if err := proto.Unmarshal(msg.Data, chatterMsg); err != nil {
			span.RecordError(err)
			return
		}
		sessionResponseMsg := &poq.SessionMessageResponse{
			Type:    poq.SessionMessageType_CHATTER,
			Chatter: chatterMsg,
		}
		_ = l.grpcSendFunc(ctx, sessionResponseMsg)
	})
	defer func() {
		if err := sub.Unsubscribe(); err != nil {
			return
		}
	}()
	<-l.cxl
	log.Printf("%s.%s: stopping listening for systemId:%d", telemetry.GetPackageName(), telemetry.GetFunctionName(), l.id)
}

func (h *LoginHandler) MakeLiveChatterInfoListener(ctx context.Context, systemId int, grpcSendFn grpcSendHandlerFn) ISessionLiveListener {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	log.Printf("%s.%s(systemId:%d, characterId:%d)", telemetry.GetPackageName(), telemetry.GetFunctionName(), systemId, h.state.GetCharacterId())
	l := &LiveChatterListener{
		messaging:    h.messaging,
		grpcSendFunc: grpcSendFn,
		id:           systemId,
		cxl:          make(chan error, 1),
	}

	reqTopic := "REQ.CHATTER.TOPIC"
	topicRequest := &poq.SystemTopicRequest{SystemId: int32(systemId)}
	topicResponse := &poq.SystemTopicResponse{}

	requestBytes, _ := proto.Marshal(topicRequest)
	responseBytes, err := l.messaging.Request(ctx, reqTopic, requestBytes, time.Duration(10*float64(time.Second)))
	if err != nil {
		span.RecordError(err)
	} else {
		if err := proto.Unmarshal(responseBytes.Data, topicResponse); err != nil {
			span.RecordError(err)
		} else {
			if topicResponse.SystemTopics != nil {
				if topicResponse.SystemTopics.SubscribeTopic != "" {
					go l.runLiveChatterInfoListener(ctx, topicResponse.SystemTopics.SubscribeTopic)
				}
			}
		}
	}

	return l
}
