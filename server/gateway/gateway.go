package gateway

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/poq"
	"github.com/jonathonfletcher/poqserver/session"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"go.opentelemetry.io/otel"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/peer"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/timestamppb"
)

type PoQServer struct {
	poq.PoQServer
	messaging messaging.IMessaging
	manager   session.ISessionManager
}

func (server *PoQServer) sessionRouterFromMetadata(md metadata.MD) session.ISessionRouter {
	if sessionIdList := md.Get("x-session-id"); len(sessionIdList) > 0 {
		sessionId := sessionIdList[0]
		return server.manager.GetSessionRouter(sessionId)
	}
	return nil
}

func (server *PoQServer) GetUniverse(ctx context.Context, request *poq.UniverseRequest) (*poq.UniverseResponse, error) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	requestData, _ := proto.Marshal(request)
	requestTopic := "REQ.UNIVERSE.STATIC"
	responseData, err := server.messaging.Request(ctx, requestTopic, requestData, time.Duration(5*float64(time.Second)))
	if err != nil {
		err = status.Error(codes.Unimplemented, fmt.Sprintf("topic:%v, err:%v", requestTopic, err))
		return nil, err
	}

	response := &poq.UniverseResponse{}
	if err = proto.Unmarshal(responseData.Data, response); err != nil {
		return nil, err
	}

	return response, nil
}

func (server *PoQServer) StartSession(ctx context.Context, request *poq.SessionStartRequest) (*poq.SessionStartResponse, error) {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	peer, _ := peer.FromContext(ctx)

	requestData, _ := proto.Marshal(request)
	requestTopic := "REQ.SESSION.START"
	responseData, err := server.messaging.Request(ctx, requestTopic, requestData, time.Duration(5*float64(time.Second)))
	if err != nil {
		err := status.Error(codes.Unimplemented, fmt.Sprintf("peer:%v, topic:%v, err:%v", peer.Addr, requestTopic, err))
		log.Printf("%s.%s: %s", telemetry.GetPackageName(), telemetry.GetFunctionName(), err)
		span.RecordError(err)
		return nil, err
	}

	response := &poq.SessionStartResponse{}
	if err = proto.Unmarshal(responseData.Data, response); err != nil {
		log.Printf("%s.%s: peer:%v, err:%v", telemetry.GetPackageName(), telemetry.GetFunctionName(), peer.Addr, err)
		return nil, err
	}

	if response.Ok {
		sessionTopics := response.SessionTopics
		if sessionTopics == nil {
			err = status.Error(codes.Unimplemented, fmt.Sprintf("peer:%v, topic:%v, err:%v", peer.Addr, requestTopic, "SessionTopics missing"))
			log.Printf("%s.%s: %s", telemetry.GetPackageName(), telemetry.GetFunctionName(), err)
			span.RecordError(err)
		} else {
			_ = server.manager.AddSessionRouter(ctx, response.SessionId, sessionTopics.SubscribeTopic, sessionTopics.PublishTopic, int(response.CharacterId))
		}
	}

	return response, err
}

func (server *PoQServer) StreamSession(stream grpc.BidiStreamingServer[poq.SessionMessageRequest, poq.SessionMessageResponse]) error {
	ctx := stream.Context()

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	peer, _ := peer.FromContext(ctx)

	md, _ := metadata.FromIncomingContext(ctx)
	router := server.sessionRouterFromMetadata(md)
	if router == nil {
		err := status.Error(codes.Unimplemented, fmt.Sprintf("peer:%v, err:%v", peer.Addr, "invalid session"))
		log.Printf("%s.%s: %s", telemetry.GetPackageName(), telemetry.GetFunctionName(), err)
		span.RecordError(err)
		return err
	}

	defer server.manager.RemoveSessionRouter(ctx, router)

	if streamErr := router.Stream(ctx, stream); streamErr != nil {
		err := status.Error(codes.Unimplemented, fmt.Sprintf("peer:%v, err:%v", peer.Addr, streamErr))
		log.Printf("%s.%s: %s", telemetry.GetPackageName(), telemetry.GetFunctionName(), err)
		span.RecordError(err)
	}

	stopMsg := &poq.SessionStopRequest{SessionId: router.GetSessionId()}
	buf, _ := proto.Marshal(stopMsg)
	requestTopic := "REQ.SESSION.STOP"
	resBuf, err := server.messaging.Request(ctx, requestTopic, buf, time.Duration(10*float64(time.Second)))
	if err == nil {
		resMsg := poq.SessionMessageResponse{}
		err = proto.Unmarshal(resBuf.Data, &resMsg)
	}

	log.Printf("%s.%s: peer:%v, topic:%v, err:%v", telemetry.GetPackageName(), telemetry.GetFunctionName(), peer.Addr, requestTopic, err)
	return err
}

func newPoQServer(messaging messaging.IMessaging) *PoQServer {
	return &PoQServer{messaging: messaging, manager: session.NewSessionManager(messaging)}
}

func (server *PoQServer) poqStartup(ctx context.Context) {
	intRequest := &poq.ServiceStart{Type: poq.ServiceType_GATEWAY_SERVICE, Timestamp: timestamppb.Now()}
	requestData, _ := proto.Marshal(intRequest)
	_ = server.messaging.Publish(ctx, "PUB.SERVICE.START", requestData)
}

func RegisterPoQServer(ctx context.Context, s grpc.ServiceRegistrar, messaging messaging.IMessaging) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	poqServer := newPoQServer(messaging)
	poqServer.poqStartup(ctx)
	poq.RegisterPoQServer(s, poqServer)
	return nil
}
