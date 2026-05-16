package ws

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/ml-in-dota/bff/internal/redisclient"
	"nhooyr.io/websocket"
)

func TestHub_RequiresToken(t *testing.T) {
	hub := NewHub(redisclient.NewFakeStore(), 10*time.Millisecond)
	req := httptest.NewRequest(http.MethodGet, "/ws/predictions", nil)
	w := httptest.NewRecorder()
	hub.ServeHTTP(w, req)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 without token, got %d", w.Code)
	}
}

func TestHub_StreamsForwardsStoredPrediction(t *testing.T) {
	store := redisclient.NewFakeStore()
	store.SetPrediction("t1", `{"radiant_win_prob":0.81,"source":"stored"}`)

	hub := NewHub(store, 50*time.Millisecond)
	srv := httptest.NewServer(hub)
	defer srv.Close()

	wsURL := "ws" + strings.TrimPrefix(srv.URL, "http") + "/?token=t1"
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	c, _, err := websocket.Dial(ctx, wsURL, nil)
	if err != nil {
		t.Fatalf("dial: %v", err)
	}
	defer c.Close(websocket.StatusNormalClosure, "")

	_, data, err := c.Read(ctx)
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if !strings.Contains(string(data), `"source":"stored"`) {
		t.Fatalf("expected stored frame to be forwarded, got %s", string(data))
	}
}
