package session

import (
	"context"

	"github.com/jonathonfletcher/poqserver/poq"
	"google.golang.org/grpc"
)

type ISessionState interface {
	GetSessionId() string
	GetCharacterId() int
	SetCharacterId(character_id int)
	GetSystemId() int
	SetSystemId(system_id int)
	Shutdown(ctx context.Context)
}

type ISessionRouter interface {
	GetSessionId() string
	Stream(ctx context.Context, stream grpc.BidiStreamingServer[poq.SessionMessageRequest, poq.SessionMessageResponse]) error
	State() ISessionState
	Shutdown(ctx context.Context)
}

type grpcSendHandler func(msg *poq.SessionMessageResponse) error
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
