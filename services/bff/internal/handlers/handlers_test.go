package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/ml-in-dota/bff/internal/redisclient"
)

func newAPIWithFake() (*API, *redisclient.FakeStore) {
	store := redisclient.NewFakeStore()
	return New(store), store
}

func doJSON(t *testing.T, h http.HandlerFunc, body any) *httptest.ResponseRecorder {
	t.Helper()
	b, err := json.Marshal(body)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	req := httptest.NewRequest(http.MethodPost, "/", bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	h(w, req)
	return w
}

func TestStart_Success(t *testing.T) {
	api, store := newAPIWithFake()
	w := doJSON(t, api.Start, map[string]any{
		"token": "abc123",
		"config": map[string]any{
			"model":    "boosting",
			"time":     10,
			"interval": 1,
			"full_map": true,
		},
	})
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	if !store.HasSession("abc123") {
		t.Fatalf("session was not persisted")
	}
	s, _ := store.GetSession(nil, "abc123")
	if s.Config.Model != "boosting" || s.Config.Time != 10 || s.Config.Interval != 1 || !s.Config.FullMap {
		t.Fatalf("unexpected stored session: %+v", s)
	}
}

func TestStart_BadModel(t *testing.T) {
	api, _ := newAPIWithFake()
	w := doJSON(t, api.Start, map[string]any{
		"token": "tok",
		"config": map[string]any{
			"model":    "linear",
			"time":     10,
			"interval": 1,
			"full_map": true,
		},
	})
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestStart_BadTime(t *testing.T) {
	api, _ := newAPIWithFake()
	w := doJSON(t, api.Start, map[string]any{
		"token": "tok",
		"config": map[string]any{
			"model":    "logreg",
			"time":     7,
			"interval": 1,
			"full_map": false,
		},
	})
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestStart_BadInterval(t *testing.T) {
	api, _ := newAPIWithFake()
	w := doJSON(t, api.Start, map[string]any{
		"token":  "tok",
		"config": map[string]any{"model": "logreg", "time": 5, "interval": 2, "full_map": true},
	})
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestStart_EmptyToken(t *testing.T) {
	api, _ := newAPIWithFake()
	w := doJSON(t, api.Start, map[string]any{
		"token":  "   ",
		"config": map[string]any{"model": "logreg", "time": 5, "interval": 1, "full_map": true},
	})
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestStart_InvalidJSON(t *testing.T) {
	api, _ := newAPIWithFake()
	req := httptest.NewRequest(http.MethodPost, "/", bytes.NewReader([]byte("{not-json")))
	w := httptest.NewRecorder()
	api.Start(w, req)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestStop_Success(t *testing.T) {
	api, store := newAPIWithFake()
	_ = store.StartSession(nil, redisclient.Session{
		Token:  "xyz",
		Config: redisclient.SessionConfig{Model: "boosting", Time: 10, Interval: 1, FullMap: true},
	})
	w := doJSON(t, api.Stop, map[string]any{"token": "xyz"})
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	if store.HasSession("xyz") {
		t.Fatalf("session should be deleted")
	}
}

func TestStop_EmptyToken(t *testing.T) {
	api, _ := newAPIWithFake()
	w := doJSON(t, api.Stop, map[string]any{"token": ""})
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestHealth_OK(t *testing.T) {
	api, _ := newAPIWithFake()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()
	api.Health(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestHealth_RedisDown(t *testing.T) {
	store := redisclient.NewFakeStore()
	store.PingErr = errAlwaysDown
	api := New(store)
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()
	api.Health(w, req)
	if w.Code != http.StatusServiceUnavailable {
		t.Fatalf("expected 503, got %d", w.Code)
	}
}
