// Copyright (c) 2025 Jonathon Fletcher
package session

import (
	"context"
	"time"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"go.opentelemetry.io/otel"
	"google.golang.org/protobuf/proto"
)

type InfoHandler struct {
	messaging  messaging.IMessaging
	state      ISessionState
	grpcFunc   grpcSendHandlerFn
	dispatcher ISessionDispatcher
}

func (h *InfoHandler) handleCharacterStaticInfo(ctx context.Context, msg *poq.SessionMessageRequest) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sessionResponseMsg := &poq.SessionMessageResponse{Type: poq.SessionMessageType_CHARACTER_STATIC_INFO, Ok: false}

	requestMsg := &poq.CharacterStaticInfoRequest{CharacterId: msg.CharacterId}
	requestData, _ := proto.Marshal(requestMsg)
	requestTopic := "REQ.CHARACTER.STATIC"
	responseData, err := h.messaging.Request(ctx, requestTopic, requestData, time.Duration(10*float64(time.Second)))
	if err == nil {
		responseMsg := &poq.CharacterStaticInfoResponse{}
		err = proto.Unmarshal(responseData.Data, responseMsg)
		if err == nil {
			sessionResponseMsg = &poq.SessionMessageResponse{
				Type:                poq.SessionMessageType_CHARACTER_STATIC_INFO,
				CharacterStaticInfo: responseMsg.CharacterStaticInfo,
				Ok:                  responseMsg.Ok,
			}
		}
	}

	if err != nil {
		span.RecordError(err)
	}

	_ = h.grpcFunc(ctx, sessionResponseMsg)
	return nil
}

func (h *InfoHandler) handleSystemStaticInfo(ctx context.Context, msg *poq.SessionMessageRequest) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sessionResponseMsg := &poq.SessionMessageResponse{Type: poq.SessionMessageType_SYSTEM_STATIC_INFO, Ok: false}

	requestMsg := &poq.SystemStaticInfoRequest{SystemId: msg.SystemId}
	requestData, _ := proto.Marshal(requestMsg)
	requestTopic := "REQ.SYSTEM.STATIC"
	responseData, err := h.messaging.Request(ctx, requestTopic, requestData, time.Duration(10*float64(time.Second)))
	if err == nil {
		responseMsg := &poq.SystemStaticInfoResponse{}
		err = proto.Unmarshal(responseData.Data, responseMsg)
		if err == nil {
			sessionResponseMsg = &poq.SessionMessageResponse{
				Type:             sessionResponseMsg.Type,
				SystemStaticInfo: responseMsg.SystemStaticInfo,
				Ok:               responseMsg.Ok,
			}
		}
	}

	if err != nil {
		span.RecordError(err)
	}

	_ = h.grpcFunc(ctx, sessionResponseMsg)
	return nil
}

func (h *InfoHandler) Shutdown(ctx context.Context) {
	if h.dispatcher != nil {
		h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_CHARACTER_STATIC_INFO)
		h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_SYSTEM_STATIC_INFO)
		h.dispatcher = nil
	}
}

func NewInfoHandler(messaging messaging.IMessaging, state ISessionState, dispatcher ISessionDispatcher, grpcFunc grpcSendHandlerFn) ISessionEventHandler {
	handler := &InfoHandler{
		messaging:  messaging,
		state:      state,
		grpcFunc:   grpcFunc,
		dispatcher: dispatcher,
	}
	dispatcher.SetDispatchHandler(poq.SessionMessageType_CHARACTER_STATIC_INFO, handler.handleCharacterStaticInfo)
	dispatcher.SetDispatchHandler(poq.SessionMessageType_SYSTEM_STATIC_INFO, handler.handleSystemStaticInfo)
	return handler
}
