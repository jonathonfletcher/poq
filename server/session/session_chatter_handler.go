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

type ChatterHandler struct {
	messaging          messaging.IMessaging
	state              ISessionState
	dispatcher         ISessionDispatcher
	currentSystemId    int
	currentPublicTopic string
}

func (h *ChatterHandler) handleIncomingChatterMessage(ctx context.Context, msg *poq.SessionMessageRequest) error {

	tracer := otel.GetTracerProvider().Tracer(telemetry.GetPackageName())
	ctx, span := tracer.Start(ctx, telemetry.GetFunctionName())
	defer span.End()

	if msg.Type != poq.SessionMessageType_CHATTER {
		return nil
	}

	if h.currentSystemId != int(msg.Chatter.SystemId) {
		requestTopic := "REQ.CHATTER.TOPIC"
		topicRequest := &poq.ChatterTopicRequest{SystemId: msg.Chatter.SystemId}
		topicResponse := &poq.ChatterTopicResponse{}

		requestBytes, _ := proto.Marshal(topicRequest)
		responseBytes, err := h.messaging.Request(ctx, requestTopic, requestBytes, time.Duration(10*float64(time.Second)))
		if err != nil {
			span.RecordError(err)
		} else if err := proto.Unmarshal(responseBytes.Data, topicResponse); err != nil {
			span.RecordError(err)
		} else if topicResponse.ChatterTopics != nil {
			h.currentPublicTopic = topicResponse.ChatterTopics.PublishTopic
			h.currentSystemId = int(msg.Chatter.SystemId)
		}
	}

	var err error
	if h.currentSystemId == h.state.GetSystemId() && h.state.GetSystemId() == int(msg.Chatter.SystemId) && h.currentPublicTopic != "" {
		msgData, _ := proto.Marshal(msg.Chatter)
		err = h.messaging.Publish(ctx, h.currentPublicTopic, msgData)
	}

	if err != nil {
		span.RecordError(err)
	}

	return err
}

func (h *ChatterHandler) Shutdown(ctx context.Context) {
	if h.dispatcher != nil {
		h.dispatcher.ClearDispatchHandler(poq.SessionMessageType_CHATTER)
		h.dispatcher = nil
	}
}

func NewChatterHandler(messaging messaging.IMessaging, state ISessionState, dispatcher ISessionDispatcher) ISessionEventHandler {
	handler := &ChatterHandler{
		messaging:          messaging,
		state:              state,
		dispatcher:         dispatcher,
		currentSystemId:    0,
		currentPublicTopic: "",
	}
	dispatcher.SetDispatchHandler(poq.SessionMessageType_CHATTER, handler.handleIncomingChatterMessage)
	return handler
}
