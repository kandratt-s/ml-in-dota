package redisclient

import (
	"context"
	"errors"
	"sync"
)

// FakeStore is a thread-safe in-memory implementation of Store for tests and
// local development without a real Redis.
type FakeStore struct {
	mu          sync.RWMutex
	sessions    map[string]Session
	predictions map[string]string
	PingErr     error
}

func NewFakeStore() *FakeStore {
	return &FakeStore{
		sessions:    make(map[string]Session),
		predictions: make(map[string]string),
	}
}

func (f *FakeStore) StartSession(_ context.Context, s Session) error {
	if s.Token == "" {
		return errors.New("empty token")
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	f.sessions[s.Token] = s
	return nil
}

func (f *FakeStore) StopSession(_ context.Context, token string) error {
	if token == "" {
		return errors.New("empty token")
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	delete(f.sessions, token)
	return nil
}

func (f *FakeStore) GetSession(_ context.Context, token string) (*Session, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()
	s, ok := f.sessions[token]
	if !ok {
		return nil, nil
	}
	return &s, nil
}

func (f *FakeStore) GetPrediction(_ context.Context, token string) (string, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()
	if v, ok := f.predictions[token]; ok {
		return v, nil
	}
	if v, ok := f.predictions["__latest__"]; ok {
		return v, nil
	}
	return "", nil
}

func (f *FakeStore) SetPrediction(token, payload string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.predictions[token] = payload
}

func (f *FakeStore) Ping(_ context.Context) error { return f.PingErr }
func (f *FakeStore) Close() error                 { return nil }

// HasSession is a test helper.
func (f *FakeStore) HasSession(token string) bool {
	f.mu.RLock()
	defer f.mu.RUnlock()
	_, ok := f.sessions[token]
	return ok
}
