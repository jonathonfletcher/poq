package session

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"go.opentelemetry.io/otel"
	"google.golang.org/protobuf/proto"
)

type LoginHandler struct {
	messaging         messaging.IMessaging
	state             ISessionState
	grpcSendFn        grpcSendHandlerFn
	dispatcher        ISessionDispatcher
	characterListener ISessionLiveListener
	systemListener    ISessionLiveListener
}

func (h *LoginHandler) grpcSendFuncPlayerCharacterRelay(ctx context.Context, msg *poq.SessionMessageResponse) error {
	if msg.Type == poq.SessionMessageType_CHARACTER_LIVE_INFO {
		if h.systemListener != nil {
			if h.systemListener.Id(ctx) != int(msg.CharacterLiveInfo.SystemId) {
				h.systemListener.Shutdown(ctx)
				h.systemListener = nil
			}
		}
		if h.systemListener == nil {
			log.Printf("%s.%s: making new system listener for SysttemId:%d", telemetry.GetPackageName(), telemetry.GetFunctionName(), int(msg.CharacterLiveInfo.SystemId))
			h.systemListener = h.MakeSystemLiveInfoListener(ctx, int(msg.CharacterLiveInfo.SystemId), h.grpcSendFuncSystemRelay)
		}
	}

	return h.grpcSendFn(ctx, msg)
}

func (h *LoginHandler) grpcSendFuncSystemRelay(ctx context.Context, msg *poq.SessionMessageResponse) error {
	return h.grpcSendFn(ctx, msg)
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
				Ok:                resMsg.Ok,
			}
			h.characterListener = h.MakeCharacterLiveInfoListener(ctx, int(resMsg.CharacterId), h.grpcSendFuncPlayerCharacterRelay)
		}
	} else {
		span.RecordError(err)
	}

	// log.Printf("%s.%s %v",
	// 	telemetry.GetPackageName(), telemetry.GetFunctionName(),
	// 	sessionResponseMsg)

	_ = h.grpcSendFuncSystemRelay(ctx, sessionResponseMsg)

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
				Ok:   resMsg.Ok,
			}
		}
	}

	log.Printf("%s.%s %v", telemetry.GetPackageName(), telemetry.GetFunctionName(), sessionResponseMsg)
	_ = h.grpcSendFuncSystemRelay(ctx, sessionResponseMsg)
	return nil
}

func (h *LoginHandler) Shutdown(ctx context.Context) {
	if h.systemListener != nil {
		h.systemListener.Shutdown(ctx)
	}
	if h.characterListener != nil {
		h.characterListener.Shutdown(ctx)
	}
	h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_LOGIN)
	h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_LOGOUT)
}

func NewLoginHandler(messaging messaging.IMessaging, state ISessionState, dispatcher ISessionDispatcher, grpcFunc grpcSendHandlerFn) ISessionEventHandler {
	handler := &LoginHandler{
		messaging:         messaging,
		state:             state,
		grpcSendFn:        grpcFunc,
		dispatcher:        dispatcher,
		characterListener: nil,
		systemListener:    nil,
	}
	dispatcher.SetDispatchHandler(poq.SessionMessageType_LOGIN, handler.handleLogin)
	dispatcher.SetDispatchHandler(poq.SessionMessageType_LOGOUT, handler.handleLogoff)
	return handler
}
