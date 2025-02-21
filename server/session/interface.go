// Copyright (c) 2025 Jonathon Fletcher
package session

import (
	"context"

	"github.com/jonathonfletcher/poqserver/poq"
	"google.golang.org/grpc"
)

type ISessionState interface {
	GetSessionId() string
	GetCharacterId() int
	GetSystemId() int
	SetSystemId(system_id int)
	Shutdown(ctx context.Context)
}

type ISessionLiveListener interface {
	Shutdown(ctx context.Context)
	Id(ctx context.Context) int
}

type ISessionRouter interface {
	GetSessionId() string
	Stream(ctx context.Context, stream grpc.BidiStreamingServer[poq.SessionMessageRequest, poq.SessionMessageResponse]) error
	GetState() ISessionState
	Shutdown(ctx context.Context)
}

type grpcSendHandlerFn func(context.Context, *poq.SessionMessageResponse) error
type NatsHandlerFunc func(context.Context, *poq.SessionMessageRequest) error

type ISessionDispatcher interface {
	SetDispatchHandler(reqType poq.SessionMessageType, handler NatsHandlerFunc)
	ClearDispatchHandler(reqType poq.SessionMessageType)
	Shutdown(ctx context.Context)
}

type ISessionEventHandler interface {
	Shutdown(cxt context.Context)
}

type ISessionManager interface {
	AddSessionRouter(ctx context.Context, sessionId string, subscribeTopic string, publishTopic string, characterId int) ISessionRouter
	GetSessionRouter(sessionId string) ISessionRouter
	RemoveSessionRouter(ctx context.Context, router ISessionRouter)
	Shutdown(ctx context.Context)
}
