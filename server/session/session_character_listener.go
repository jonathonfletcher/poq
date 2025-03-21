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

type LiveCharacterListener struct {
	messaging    messaging.IMessaging
	grpcSendFunc grpcSendHandlerFn
	id           int
	cxl          chan error
}

func (l *LiveCharacterListener) Id(context.Context) int {
	return l.id
}

func (l *LiveCharacterListener) Shutdown(ctx context.Context) {
	l.cxl <- nil
}

func (l *LiveCharacterListener) runCharacterLiveInfoListener(ctx context.Context, topic string) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sub, _ := l.messaging.Subscribe(ctx, topic, func(ctx context.Context, msg *nats.Msg) {

		tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
		_, span := tracer.Start(ctx, telemetry.GetFunctionName())
		defer span.End()

		outMsg := &poq.CharacterLiveInfoMessage{}
		if err := proto.Unmarshal(msg.Data, outMsg); err != nil {
			span.RecordError(err)
		} else {
			sessionResponseMsg := &poq.SessionMessageResponse{
				Type:              poq.SessionMessageType_CHARACTER_LIVE_INFO,
				CharacterLiveInfo: outMsg}
			_ = l.grpcSendFunc(ctx, sessionResponseMsg)
		}
	})
	defer func() {
		_ = sub.Unsubscribe()
	}()
	<-l.cxl
	log.Printf("%s.%s: stopping listening for characterId:%d", telemetry.GetPackageName(), telemetry.GetFunctionName(), l.id)
}

func (h *LoginHandler) MakeCharacterLiveInfoListener(ctx context.Context, characterId int, grpcSendFn grpcSendHandlerFn) ISessionLiveListener {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	log.Printf("%s.%s(characterId:%d)", telemetry.GetPackageName(), telemetry.GetFunctionName(), characterId)
	l := &LiveCharacterListener{
		messaging:    h.messaging,
		grpcSendFunc: grpcSendFn,
		id:           characterId,
		cxl:          make(chan error, 1),
	}

	reqTopic := "REQ.CHARACTER.TOPIC"
	topicRequest := &poq.CharacterTopicRequest{CharacterId: int32(characterId)}
	topicResponse := &poq.CharacterTopicResponse{}

	liveRequestTopic := ""
	requestBytes, _ := proto.Marshal(topicRequest)
	responseBytes, err := l.messaging.Request(ctx, reqTopic, requestBytes, time.Duration(10*float64(time.Second)))
	if err != nil {
		span.RecordError(err)
	} else if err := proto.Unmarshal(responseBytes.Data, topicResponse); err != nil {
		span.RecordError(err)
	} else {
		if topicResponse.CharacterTopics != nil {
			liveRequestTopic = topicResponse.CharacterTopics.RequestTopic
			if topicResponse.CharacterTopics.SubscribeTopic != "" {
				go l.runCharacterLiveInfoListener(ctx, topicResponse.CharacterTopics.SubscribeTopic)
			}
		}
	}

	if liveRequestTopic != "" {
		liveRequest := &poq.CharacterLiveInfoRequest{CharacterId: int32(characterId)}
		liveResponse := &poq.CharacterLiveInfoResponse{}

		requestBytes, _ = proto.Marshal(liveRequest)
		responseBytes, err = l.messaging.Request(ctx, liveRequestTopic, requestBytes, time.Duration(10*float64(time.Second)))
		if err != nil {
			span.RecordError(err)
		} else if err := proto.Unmarshal(responseBytes.Data, liveResponse); err != nil {
			span.RecordError(err)
		} else {
			sessionResponseMsg := &poq.SessionMessageResponse{
				Type:              poq.SessionMessageType_CHARACTER_LIVE_INFO,
				CharacterLiveInfo: liveResponse.CharacterLiveInfo,
				Ok:                liveResponse.Ok,
			}
			_ = l.grpcSendFunc(ctx, sessionResponseMsg)
			// h.setupSystemLiveInfoListener(ctx, liveResponse.CharacterLiveInfo)
		}
	}

	return l
}
