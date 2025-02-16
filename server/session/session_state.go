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
	session.mu.Lock()
	defer session.mu.Unlock()
	return session.characterId
}

func (session *SessionState) SetCharacterId(characterId int) {
	session.mu.Lock()
	session.characterId = characterId
	session.mu.Unlock()
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
	session.mu.Lock()
	defer session.mu.Unlock()
	return session.sessionId
}

func (session *SessionState) Shutdown(context.Context) {

}

func NewSessionState(messaging messaging.IMessaging, sessionId string, characterId int) ISessionState {
	return &SessionState{
		messaging:   messaging,
		sessionId:   sessionId,
		characterId: characterId,
	}
}
