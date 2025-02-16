package messaging

import (
	"context"
	"time"

	"github.com/nats-io/nats.go"
)

type IMessaging interface {
	Request(ctx context.Context, subj string, data []byte, timeout time.Duration) (*nats.Msg, error)
	Publish(ctx context.Context, subj string, data []byte) error
	PublishWithReply(ctx context.Context, subj string, reply string, data []byte) error
	Subscribe(ctx context.Context, subj string, cb func(ctx context.Context, msg *nats.Msg)) (*nats.Subscription, error)
	Shutdown(ctx context.Context)
}
