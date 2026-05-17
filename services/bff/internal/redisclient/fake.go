package redisclient

import (
	"context"
	"errors"
	"sync"
)

type FakeStore struct {
	mu       sync.RWMutex
	sessions map[string]Session
	heatmap  [][]float64
	PingErr  error
}

func NewFakeStore() *FakeStore {
	return &FakeStore{sessions: make(map[string]Session)}
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

func (f *FakeStore) GetHeatmap(_ context.Context) ([][]float64, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()
	if f.heatmap == nil {
		return nil, nil
	}
	// Return a defensive copy so callers can't mutate stored state.
	out := make([][]float64, len(f.heatmap))
	for i, row := range f.heatmap {
		dup := make([]float64, len(row))
		copy(dup, row)
		out[i] = dup
	}
	return out, nil
}

func (f *FakeStore) SetHeatmap(m [][]float64) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.heatmap = m
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
