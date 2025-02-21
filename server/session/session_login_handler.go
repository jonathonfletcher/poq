// Copyright (c) 2025 Jonathon Fletcher
package session

import (
	"context"
	"fmt"
	"log"
	"slices"
	"time"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"go.opentelemetry.io/otel"
	"google.golang.org/protobuf/proto"
)

type LoginHandler struct {
	messaging             messaging.IMessaging
	state                 ISessionState
	grpcSendFn            grpcSendHandlerFn
	dispatcher            ISessionDispatcher
	characterListener     ISessionLiveListener
	systemListener        ISessionLiveListener
	systemChatterListener ISessionLiveListener
	localCharacters       map[int]ISessionLiveListener
}

func (h *LoginHandler) grpcSendFuncPlayerCharacterRelay(ctx context.Context, msg *poq.SessionMessageResponse) error {

	doDropDifferentIdFn := func(ctx context.Context, l ISessionLiveListener, id int) ISessionLiveListener {
		if l != nil {
			if l.Id(ctx) != id {
				l.Shutdown(ctx)
				return nil
			}
		}
		return l
	}

	if msg.Type == poq.SessionMessageType_CHARACTER_LIVE_INFO {
		h.state.SetSystemId(int(msg.CharacterLiveInfo.SystemId))
	}

	if msg.Type == poq.SessionMessageType_CHARACTER_LIVE_INFO {

		h.systemListener = doDropDifferentIdFn(ctx, h.systemListener, int(msg.CharacterLiveInfo.SystemId))
		if h.systemListener == nil {
			h.systemListener = h.MakeSystemLiveInfoListener(ctx, int(msg.CharacterLiveInfo.SystemId), int(msg.CharacterLiveInfo.CharacterId), h.grpcSendFuncSystemRelay)
		}

		h.systemChatterListener = doDropDifferentIdFn(ctx, h.systemChatterListener, int(msg.CharacterLiveInfo.SystemId))
		if h.systemChatterListener == nil {
			h.systemChatterListener = h.MakeLiveChatterInfoListener(ctx, h.state.GetSystemId(), h.grpcSendFuncChatterRelay)
		}
	}

	return h.grpcSendFn(ctx, msg)
}

func (h *LoginHandler) grpcSendFuncSystemRelay(ctx context.Context, msg *poq.SessionMessageResponse) error {
	if h.characterListener != nil && msg.Type == poq.SessionMessageType_SYSTEM_LIVE_INFO {

		removeList := make([]int, 0)
		localCharacterList := make([]int, 0)
		for characterId := range h.localCharacters {
			localCharacterList = append(localCharacterList, characterId)
			if !slices.Contains(msg.SystemLiveInfo.CharacterId, int32(characterId)) {
				removeList = append(removeList, characterId)
			}
		}

		myCharacterId := h.characterListener.Id(ctx)
		addList := make([]int, 0)
		for _, characterId := range msg.SystemLiveInfo.CharacterId {
			if int(characterId) != myCharacterId && !slices.Contains(localCharacterList, int(characterId)) {
				addList = append(addList, int(characterId))
			}
		}

		for _, characterId := range removeList {
			listener := h.localCharacters[characterId]
			if listener != nil {
				listener.Shutdown(ctx)
			}
			log.Printf("%s.%s: removing character listener for characterId:%d", telemetry.GetPackageName(), telemetry.GetFunctionName(), characterId)
			delete(h.localCharacters, characterId)
		}

		for _, characterId := range addList {
			listener := h.localCharacters[characterId]
			if listener == nil {
				log.Printf("%s.%s: making new character listener for characterId:%d", telemetry.GetPackageName(), telemetry.GetFunctionName(), characterId)
				h.localCharacters[characterId] = h.MakeCharacterLiveInfoListener(ctx, characterId, h.grpcSendFn)
			}
		}
	}
	return h.grpcSendFn(ctx, msg)
}

func (h *LoginHandler) grpcSendFuncChatterRelay(ctx context.Context, msg *poq.SessionMessageResponse) error {
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

	_ = h.grpcSendFuncSystemRelay(ctx, sessionResponseMsg)
	return nil
}

func (h *LoginHandler) Shutdown(ctx context.Context) {

	doShutdownFn := func(ctx context.Context, l ISessionLiveListener) ISessionLiveListener {
		if l != nil {
			l.Shutdown(ctx)
		}
		return nil
	}

	h.systemListener = doShutdownFn(ctx, h.systemListener)
	h.systemChatterListener = doShutdownFn(ctx, h.systemChatterListener)
	h.characterListener = doShutdownFn(ctx, h.characterListener)
	for _, v := range h.localCharacters {
		doShutdownFn(ctx, v)
	}
	clear(h.localCharacters)

	if h.dispatcher != nil {
		h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_LOGIN)
		h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_LOGOUT)
		h.dispatcher = nil
	}
}

func NewLoginHandler(messaging messaging.IMessaging, state ISessionState, dispatcher ISessionDispatcher, grpcFunc grpcSendHandlerFn) ISessionEventHandler {
	handler := &LoginHandler{
		messaging:             messaging,
		state:                 state,
		grpcSendFn:            grpcFunc,
		dispatcher:            dispatcher,
		characterListener:     nil,
		systemListener:        nil,
		systemChatterListener: nil,
		localCharacters:       make(map[int]ISessionLiveListener, 0),
	}
	dispatcher.SetDispatchHandler(poq.SessionMessageType_LOGIN, handler.handleLogin)
	dispatcher.SetDispatchHandler(poq.SessionMessageType_LOGOUT, handler.handleLogoff)
	return handler
}
