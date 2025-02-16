package session

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"github.com/nats-io/nats.go"
	"go.opentelemetry.io/otel"
	"google.golang.org/protobuf/proto"
)

type LoginHandler struct {
	mu           sync.Mutex
	messaging    messaging.IMessaging
	state        ISessionState
	grpcSendFunc grpcSendHandler
	dispatcher   ISessionDispatcher
	characterCxl chan error
	systemCxl    chan error
}

func (h *LoginHandler) grpcSendFuncCaller(msg *poq.SessionMessageResponse) error {
	h.mu.Lock()
	defer h.mu.Unlock()
	return h.grpcSendFunc(msg)
}

func (h *LoginHandler) systemLiveInfoListener(ctx context.Context, topic string) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sub, _ := h.messaging.Subscribe(ctx, topic, func(ctx context.Context, msg *nats.Msg) {

		tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
		_, span := tracer.Start(ctx, telemetry.GetFunctionName())
		defer span.End()

		outMsg := &poq.SystemLiveInfoMessage{}
		if err := proto.Unmarshal(msg.Data, outMsg); err != nil {
			span.RecordError(err)
			return
		}
		sessionResponseMsg := &poq.SessionMessageResponse{
			Type:           poq.SessionMessageType_SYSTEM_LIVE_INFO,
			SystemLiveInfo: outMsg}
		_ = h.grpcSendFuncCaller(sessionResponseMsg)
	})
	defer func() {
		if err := sub.Unsubscribe(); err != nil {
			return
		}
	}()
	<-h.systemCxl
}

func (h *LoginHandler) setupSystemLiveInfoListener(ctx context.Context, msg *poq.CharacterLiveInfoMessage) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	reqMsg := &poq.SystemLiveInfoRequest{SystemId: msg.SystemId}
	reqData, _ := proto.Marshal(reqMsg)
	reqTopic := "REQ.SYSTEM.LIVE"
	resData, err := h.messaging.Request(ctx, reqTopic, reqData, time.Duration(10*float64(time.Second)))
	if err == nil {
		resMsg := &poq.SystemLiveInfoResponse{}
		if err := proto.Unmarshal(resData.Data, resMsg); err == nil {
			if resMsg.SubscribeTopic != "" {
				go h.systemLiveInfoListener(ctx, resMsg.SubscribeTopic)
			}
			sessionResponseMsg := &poq.SessionMessageResponse{
				Type:           poq.SessionMessageType_SYSTEM_LIVE_INFO,
				SystemLiveInfo: resMsg.SystemLiveInfo,
			}
			_ = h.grpcSendFuncCaller(sessionResponseMsg)
		} else {
			span.RecordError(err)
		}
	} else {
		span.RecordError(err)
	}
}

func (h *LoginHandler) characterLiveInfoListener(ctx context.Context, topic string) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sub, _ := h.messaging.Subscribe(ctx, topic, func(ctx context.Context, msg *nats.Msg) {

		tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
		_, span := tracer.Start(ctx, telemetry.GetFunctionName())
		defer span.End()

		outMsg := &poq.CharacterLiveInfoMessage{}
		err := proto.Unmarshal(msg.Data, outMsg)
		if err == nil {
			sessionResponseMsg := &poq.SessionMessageResponse{
				Type:              poq.SessionMessageType_CHARACTER_LIVE_INFO,
				CharacterLiveInfo: outMsg}
			_ = h.grpcSendFuncCaller(sessionResponseMsg)
			systemId := int(outMsg.SystemId)
			log.Printf("%s.%s %d",
				telemetry.GetPackageName(), telemetry.GetFunctionName(),
				systemId)
		} else {
			span.RecordError(err)
		}
	})
	defer func() {
		_ = sub.Unsubscribe()
	}()
	<-h.characterCxl
}

func (h *LoginHandler) setupCharacterLiveInfoListener(ctx context.Context, msg *poq.CharacterLiveInfoMessage) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	reqMsg := &poq.CharacterLiveInfoRequest{CharacterId: msg.CharacterId}
	reqData, _ := proto.Marshal(reqMsg)
	reqTopic := "REQ.CHARACTER.LIVE"
	resData, err := h.messaging.Request(ctx, reqTopic, reqData, time.Duration(10*float64(time.Second)))
	if err == nil {
		resMsg := &poq.CharacterLiveInfoResponse{}
		if err := proto.Unmarshal(resData.Data, resMsg); err == nil {
			if resMsg.SubscribeTopic != "" {
				go h.characterLiveInfoListener(ctx, resMsg.SubscribeTopic)
			}
			h.setupSystemLiveInfoListener(ctx, resMsg.CharacterLiveInfo)
			sessionResponseMsg := &poq.SessionMessageResponse{
				Type:              poq.SessionMessageType_CHARACTER_LIVE_INFO,
				CharacterLiveInfo: resMsg.CharacterLiveInfo,
			}
			// log.Printf("%s.%s %v",
			// 	telemetry.GetPackageName(), telemetry.GetFunctionName(),
			// 	sessionResponseMsg)
			_ = h.grpcSendFuncCaller(sessionResponseMsg)
		} else {
			span.RecordError(err)
		}
	} else {
		span.RecordError(err)
	}
}

func (h *LoginHandler) handleLogin(ctx context.Context, msg *poq.SessionMessageRequest) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sessionResponseMsg := &poq.SessionMessageResponse{Type: poq.SessionMessageType_LOGIN, Ok: false}

	reqMsg := &poq.CharacterLoginRequest{CharacterId: int32(h.state.GetCharacterId())}
	reqData, _ := proto.Marshal(reqMsg)
	reqTopic := "REQ.CHARACTER.LOGIN"
	resData, err := h.messaging.Request(ctx, reqTopic, reqData, time.Duration(10*float64(time.Second)))
	if err == nil {
		resMsg := &poq.CharacterLoginResponse{}
		if err := proto.Unmarshal(resData.Data, resMsg); err == nil {
			// log.Printf("%s.%s: %v",
			// 	telemetry.GetPackageName(), telemetry.GetFunctionName(),
			// 	resMsg)
			sessionResponseMsg = &poq.SessionMessageResponse{
				Type:              sessionResponseMsg.Type,
				CharacterLiveInfo: resMsg.CharacterLiveInfo,
				Ok:                err == nil,
			}
			h.setupCharacterLiveInfoListener(ctx, resMsg.CharacterLiveInfo)
		}
	} else {
		span.RecordError(err)
	}

	// log.Printf("%s.%s %v",
	// 	telemetry.GetPackageName(), telemetry.GetFunctionName(),
	// 	sessionResponseMsg)

	_ = h.grpcSendFuncCaller(sessionResponseMsg)

	return nil
}

func (h *LoginHandler) handleLogoff(ctx context.Context, msg *poq.SessionMessageRequest) error {

	fmt.Printf("%s.%s", telemetry.GetPackageName(), telemetry.GetFunctionName())

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	sessionResponseMsg := &poq.SessionMessageResponse{Type: poq.SessionMessageType_LOGOUT, Ok: false}

	reqMsg := &poq.CharacterLogoutRequest{CharacterId: int32(h.state.GetCharacterId())}
	reqData, _ := proto.Marshal(reqMsg)
	reqTopic := "REQ.CHARACTER.LOGOUT"
	resData, err := h.messaging.Request(ctx, reqTopic, reqData, time.Duration(10*float64(time.Second)))
	if err == nil {
		resMsg := &poq.CharacterLogoutResponse{}
		if err := proto.Unmarshal(resData.Data, resMsg); err == nil {
			sessionResponseMsg = &poq.SessionMessageResponse{
				Type: sessionResponseMsg.Type,
				Ok:   err == nil,
			}
		}
	}

	log.Printf("%s.%s %v", telemetry.GetPackageName(), telemetry.GetFunctionName(), sessionResponseMsg)
	_ = h.grpcSendFuncCaller(sessionResponseMsg)
	return nil
}

func (h *LoginHandler) Shutdown(ctx context.Context) {
	h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_LOGIN)
	h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_LOGOUT)
	h.systemCxl <- nil
	h.characterCxl <- nil
}

func NewLoginHandler(messaging messaging.IMessaging, state ISessionState, dispatcher ISessionDispatcher, grpcFunc grpcSendHandler) ISessionEventHandler {
	handler := &LoginHandler{
		messaging:    messaging,
		state:        state,
		grpcSendFunc: grpcFunc,
		dispatcher:   dispatcher,
		characterCxl: make(chan error, 1),
		systemCxl:    make(chan error, 1),
	}
	dispatcher.SetDispatchHandler(poq.SessionMessageType_LOGIN, handler.handleLogin)
	dispatcher.SetDispatchHandler(poq.SessionMessageType_LOGOUT, handler.handleLogoff)
	return handler
}
