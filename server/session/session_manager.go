package session

import (
	"context"
	"sync"

	"github.com/jonathonfletcher/poqserver/messaging"
)

type SessionManager struct {
	mu        sync.Mutex
	messaging messaging.IMessaging
	sessions  map[string]ISessionRouter
}

func (manager *SessionManager) GetSessionRouter(sessionId string) ISessionRouter {
	var session ISessionRouter = nil
	manager.mu.Lock()
	defer manager.mu.Unlock()
	session = manager.sessions[sessionId]
	return session
}

func (manager *SessionManager) AddSessionRouter(ctx context.Context, sessionId string, subscribeTopic string, publishTopic string, characterId int) ISessionRouter {
	var session ISessionRouter = nil
	manager.mu.Lock()
	defer manager.mu.Unlock()
	session = NewSessionRouter(manager.messaging, sessionId, subscribeTopic, publishTopic, characterId)
	manager.sessions[sessionId] = session
	return session
}

func (manager *SessionManager) RemoveSessionRouter(ctx context.Context, router ISessionRouter) {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	defer router.Shutdown(ctx)
	delete(manager.sessions, router.GetSessionId())
}

func (manager *SessionManager) Shutdown(ctx context.Context) {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	for _, v := range manager.sessions {
		v.Shutdown(ctx)
	}
	clear(manager.sessions)
}

func NewSessionManager(messaging messaging.IMessaging) ISessionManager {
	return &SessionManager{messaging: messaging, sessions: make(map[string]ISessionRouter)}
}
