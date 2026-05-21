package redisclient

import (
	"context"
	"errors"
	"strings"
	"sync"
)

type FakeStore struct {
	mu                 sync.RWMutex
	sessions           map[string]Session
	heatmap            [][]float64
	heatmapsPerToken   map[string][][]float64
	predictionConfigs  map[string]SessionConfig
	snapshotKeys       map[string]struct{}
	heatmapSubscribers map[string]map[chan struct{}]struct{}
	PingErr            error
}

func NewFakeStore() *FakeStore {
	return &FakeStore{sessions: make(map[string]Session), heatmapsPerToken: make(map[string][][]float64), predictionConfigs: make(map[string]SessionConfig), snapshotKeys: make(map[string]struct{}), heatmapSubscribers: make(map[string]map[chan struct{}]struct{})}
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
	// Remove direct token-scoped maps
	delete(f.sessions, token)
	delete(f.heatmapsPerToken, token)
	delete(f.predictionConfigs, token)
	// Remove snapshot keys for this token
	for key := range f.snapshotKeys {
		if strings.Contains(key, token) {
			delete(f.snapshotKeys, key)
		}
	}
	// Additionally, remove any stored artifacts whose map key contains the token
	for k := range f.heatmapsPerToken {
		if strings.Contains(k, token) {
			delete(f.heatmapsPerToken, k)
		}
	}
	for k := range f.predictionConfigs {
		if strings.Contains(k, token) {
			delete(f.predictionConfigs, k)
		}
	}
	for k := range f.sessions {
		if strings.Contains(k, token) {
			delete(f.sessions, k)
		}
	}
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
	f.notifyHeatmapLocked("")
}

func (f *FakeStore) GetHeatmapForToken(_ context.Context, token string) ([][]float64, error) {
	f.mu.RLock()
	defer f.mu.RUnlock()
	if token != "" {
		if m, ok := f.heatmapsPerToken[token]; ok {
			out := make([][]float64, len(m))
			for i, row := range m {
				dup := make([]float64, len(row))
				copy(dup, row)
				out[i] = dup
			}
			return out, nil
		}
	}
	if f.heatmap == nil {
		return nil, nil
	}
	out := make([][]float64, len(f.heatmap))
	for i, row := range f.heatmap {
		dup := make([]float64, len(row))
		copy(dup, row)
		out[i] = dup
	}
	return out, nil
}

func (f *FakeStore) SetHeatmapForToken(token string, m [][]float64) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.heatmapsPerToken[token] = m
	f.notifyHeatmapLocked(token)
}

func (f *FakeStore) SetPredictionConfig(_ context.Context, token string, cfg SessionConfig) error {
	if token == "" {
		return errors.New("empty token")
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	f.predictionConfigs[token] = cfg
	return nil
}

func (f *FakeStore) SetSnapshotKey(token string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.snapshotKeys["snapshot:"+token+":current"] = struct{}{}
}

func (f *FakeStore) Ping(_ context.Context) error { return f.PingErr }
func (f *FakeStore) Close() error                 { return nil }

func (f *FakeStore) SubscribeHeatmapUpdates(ctx context.Context, token string) (<-chan struct{}, func(), error) {
	updates := make(chan struct{}, 1)
	f.mu.Lock()
	if f.heatmapSubscribers[token] == nil {
		f.heatmapSubscribers[token] = make(map[chan struct{}]struct{})
	}
	f.heatmapSubscribers[token][updates] = struct{}{}
	f.mu.Unlock()

	cleanup := func() {
		f.mu.Lock()
		if subs, ok := f.heatmapSubscribers[token]; ok {
			delete(subs, updates)
			if len(subs) == 0 {
				delete(f.heatmapSubscribers, token)
			}
		}
		f.mu.Unlock()
	}

	go func() {
		<-ctx.Done()
		cleanup()
		close(updates)
	}()

	return updates, cleanup, nil
}

func (f *FakeStore) notifyHeatmapLocked(token string) {
	for ch := range f.heatmapSubscribers[token] {
		select {
		case ch <- struct{}{}:
		default:
		}
	}
}

// HasSession is a test helper.
func (f *FakeStore) HasSession(token string) bool {
	f.mu.RLock()
	defer f.mu.RUnlock()
	_, ok := f.sessions[token]
	return ok
}
