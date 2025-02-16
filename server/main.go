package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"

	"github.com/joho/godotenv"
	"github.com/jonathonfletcher/poqserver/gateway"
	"github.com/jonathonfletcher/poqserver/messaging"
	"github.com/jonathonfletcher/poqserver/telemetry"
	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
	"google.golang.org/grpc"
)

var (
	port = flag.Int("port", 50051, "The server port")
)

func main() {
	ctx := context.Background()
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	telemetry := telemetry.NewTelemetryService(ctx)
	defer func() {
		log.Println("shutdown telemetry")
		telemetry.Shutdown(ctx)
	}()

	flag.Parse()
	listener, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", *port))
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	messaging := messaging.NewMessaging(ctx)
	defer messaging.Shutdown(ctx)

	var grpcOpts []grpc.ServerOption
	grpcOpts = append(grpcOpts, grpc.StatsHandler(otelgrpc.NewServerHandler()))
	grpcServer := grpc.NewServer(grpcOpts...)

	if err = gateway.RegisterPoQServer(ctx, grpcServer, messaging); err != nil {
		log.Fatalf("grpc registration failed: %v", err)
	}

	wg := sync.WaitGroup{}

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	wg.Add(1)

	go func() {
		<-sigCh
		grpcServer.GracefulStop()
		wg.Done()
	}()

	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("grpc server failed: %v", err)
	}

	wg.Wait()
}
