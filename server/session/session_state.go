// Copyright (c) 2025 Jonathon Fletcher
package session

import (
	"context"
	"sync"

	"github.com/jonathonfletcher/poqserver/messaging"
)

type SessionState struct {
	mu          sync.Mutex
	messaging   messaging.IMessaging
	characterId int
	systemId    int
	sessionId   string
}

func (session *SessionState) GetCharacterId() int {
	return session.characterId
}

func (session *SessionState) GetSystemId() int {
	session.mu.Lock()
	defer session.mu.Unlock()
	return session.systemId
}

func (session *SessionState) SetSystemId(systemId int) {
	session.mu.Lock()
	defer session.mu.Unlock()
	session.systemId = systemId
}

func (session *SessionState) GetSessionId() string {
	return session.sessionId
}

func (session *SessionState) Shutdown(context.Context) {

}

func NewSessionState(sessionId string, characterId int) ISessionState {
	return &SessionState{
		sessionId:   sessionId,
		characterId: characterId,
	}
}
