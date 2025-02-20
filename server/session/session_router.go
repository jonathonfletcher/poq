package session

import (
	"context"
	"log"
	"sync"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"github.com/nats-io/nats.go"
	"go.opentelemetry.io/otel"
	"google.golang.org/grpc"
	"google.golang.org/grpc/peer"
	"google.golang.org/protobuf/proto"
)

type SessionRouter struct {
	mu             sync.Mutex
	sessionId      string
	subscribeTopic string
	publishTopic   string
	messaging      messaging.IMessaging
	state          ISessionState
	dispatchMap    map[poq.SessionMessageType]NatsHandlerFunc
}

func (router *SessionRouter) SetDispatchHandler(reqType poq.SessionMessageType, handler NatsHandlerFunc) {
	router.mu.Lock()
	defer router.mu.Unlock()
	router.dispatchMap[reqType] = handler
}

func (router *SessionRouter) ClearDispatchHandler(reqType poq.SessionMessageType) {
	router.mu.Lock()
	defer router.mu.Unlock()
	delete(router.dispatchMap, reqType)
}

func (router *SessionRouter) State() ISessionState {
	return router.state
}

func (router *SessionRouter) GetSessionId() string {
	return router.sessionId
}

func (router *SessionRouter) Stream(ctx context.Context, stream grpc.BidiStreamingServer[poq.SessionMessageRequest, poq.SessionMessageResponse]) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	peer, _ := peer.FromContext(ctx)

	grpcSendErrChan := make(chan error, 1)
	grpcResponseHandler := func(_ context.Context, msg *poq.SessionMessageResponse) error {
		err := stream.SendMsg(msg)
		if err != nil {
			grpcSendErrChan <- err
		}
		return err
	}

	infoHandler := NewInfoHandler(router.messaging, router.state, router, grpcResponseHandler)
	defer infoHandler.Shutdown(ctx)

	loginHandler := NewLoginHandler(router.messaging, router.state, router, grpcResponseHandler)
	defer loginHandler.Shutdown(ctx)
	pubCounter := 0
	subCounter := 0

	grpcRecvErrChan := make(chan error, 1)
	go func(ret chan error) {
		inMsg := &poq.SessionMessageRequest{}
		for {
			if err := stream.RecvMsg(inMsg); err != nil {
				ret <- err
				break
			}

			handlerFunc := router.dispatchMap[inMsg.Type]
			if handlerFunc != nil {
				if err := handlerFunc(ctx, inMsg); err != nil {
					ret <- err
					break
				}
			} else {
				log.Printf("%s.%s: no handler for %v",
					telemetry.GetPackageName(), telemetry.GetFunctionName(),
					inMsg.Type)
			}
		}
	}(grpcRecvErrChan)

	natsCxlChan := make(chan error, 1)
	go func(cxl chan error, ret chan error) {
		sub, err := router.messaging.Subscribe(ctx, router.subscribeTopic, func(ctx context.Context, msg *nats.Msg) {
			subCounter += 1
			outMsg := &poq.SessionMessageResponse{}
			if err := proto.Unmarshal(msg.Data, outMsg); err != nil {
				ret <- err
				return
			}
			if err := stream.SendMsg(outMsg); err != nil {
				ret <- err
				return
			}

			if outMsg.Type == poq.SessionMessageType_STOP {
				natsCxlChan <- nil
				return
			}
		})
		if err != nil {
			ret <- err
			return
		}
		defer func() {
			if err := sub.Unsubscribe(); err != nil {
				ret <- err
				return
			}
			ret <- nil
		}()
		<-natsCxlChan
	}(natsCxlChan, grpcSendErrChan)

	var err error
	select {
	case err = <-grpcRecvErrChan:
		natsCxlChan <- nil
		<-grpcSendErrChan
	case err = <-grpcSendErrChan:
		<-grpcRecvErrChan
	}

	log.Printf("%s.%s: peer:%v, sessionId:%v, pubEvent:%d, subEvents:%d, err:%v",
		telemetry.GetPackageName(), telemetry.GetFunctionName(),
		peer.Addr, router.sessionId, pubCounter, subCounter, err)

	return err
}

func (router *SessionRouter) Shutdown(ctx context.Context) {
	router.state.Shutdown(ctx)
}

func NewSessionRouter(messaging messaging.IMessaging, sessionId string, subscribeTopic string, publishTopic string, characterId int) ISessionRouter {
	return &SessionRouter{
		messaging:      messaging,
		sessionId:      sessionId,
		subscribeTopic: subscribeTopic,
		publishTopic:   publishTopic,
		state:          NewSessionState(messaging, sessionId, characterId),
		dispatchMap:    make(map[poq.SessionMessageType]NatsHandlerFunc),
	}
}
