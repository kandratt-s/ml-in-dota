package ws

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/ml-in-dota/bff/internal/redisclient"
	"nhooyr.io/websocket"
)

func TestIntervalForToken(t *testing.T) {
	ctx := context.Background()
	store := redisclient.NewFakeStore()

	// No session → fall back to default.
	if got := intervalForToken(ctx, store, "missing", 2*time.Second); got != 2*time.Second {
		t.Fatalf("no session: want 2s, got %s", got)
	}

	// Session present → its Interval (seconds) wins.
	_ = store.StartSession(ctx, redisclient.Session{
		Token:  "tok-5",
		Config: redisclient.SessionConfig{Model: "boosting", Time: 10, Interval: 5, FullMap: true},
	})
	if got := intervalForToken(ctx, store, "tok-5", 1*time.Second); got != 5*time.Second {
		t.Fatalf("session Interval=5: want 5s, got %s", got)
	}

	// Zero in session config is treated as "unset" → default.
	_ = store.StartSession(ctx, redisclient.Session{
		Token:  "tok-zero",
		Config: redisclient.SessionConfig{Model: "boosting", Time: 10, Interval: 0, FullMap: true},
	})
	if got := intervalForToken(ctx, store, "tok-zero", 3*time.Second); got != 3*time.Second {
		t.Fatalf("Interval=0: want default 3s, got %s", got)
	}

	// Out-of-range values are clamped.
	_ = store.StartSession(ctx, redisclient.Session{
		Token:  "tok-huge",
		Config: redisclient.SessionConfig{Model: "boosting", Time: 10, Interval: 9999, FullMap: true},
	})
	if got := intervalForToken(ctx, store, "tok-huge", 1*time.Second); got != maxStreamInterval {
		t.Fatalf("clamp upper: want %s, got %s", maxStreamInterval, got)
	}
}

func TestHub_RequiresToken(t *testing.T) {
	hub := NewHub(redisclient.NewFakeStore(), 10*time.Millisecond)
	req := httptest.NewRequest(http.MethodGet, "/ws/predictions", nil)
	w := httptest.NewRecorder()
	hub.ServeHTTP(w, req)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 without token, got %d", w.Code)
	}
}

func TestHub_ForwardsStoredHeatmap(t *testing.T) {
	store := redisclient.NewFakeStore()
	// Tiny 2x2 matrix is enough to assert the wire format.
	store.SetHeatmap([][]float64{{0.0, 0.5}, {0.25, 1.0}})

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

	var got heatmapFrame
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatalf("unmarshal: %v — raw=%s", err, string(data))
	}
	if got.Source != "redis" {
		t.Fatalf("expected source=redis, got %q (raw=%s)", got.Source, string(data))
	}
	if got.Cells != 2 || len(got.Matrix) != 2 || got.Matrix[1][1] != 1.0 {
		t.Fatalf("unexpected matrix in frame: %+v", got)
	}
	if got.MaxValue != 1.0 {
		t.Fatalf("expected max_value=1.0, got %f", got.MaxValue)
	}
}

func TestHub_DoesNotEmitMockWhenNoRealData(t *testing.T) {
	hub := NewHub(redisclient.NewFakeStore(), 50*time.Millisecond)
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
	if err == nil {
		var got heatmapFrame
		if err := json.Unmarshal(data, &got); err != nil {
			t.Fatalf("unmarshal: %v", err)
		}
		if got.Source == "mock" {
			t.Fatalf("expected no mock frame, got %q", string(data))
		}
	}
}

func TestHub_SendsUpdateAfterHeatmapChange(t *testing.T) {
	store := redisclient.NewFakeStore()
	store.SetHeatmapForToken("t1", [][]float64{{0.1}})

	hub := NewHub(store, 500*time.Millisecond)
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

	if _, _, err := c.Read(ctx); err != nil {
		t.Fatalf("initial read: %v", err)
	}

	store.SetHeatmapForToken("t1", [][]float64{{0.9}})

	_, data, err := c.Read(ctx)
	if err != nil {
		t.Fatalf("update read: %v", err)
	}

	var got heatmapFrame
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if got.Source != "redis" {
		t.Fatalf("expected source=redis, got %q", got.Source)
	}
	if got.Matrix[0][0] != 0.9 {
		t.Fatalf("expected updated matrix, got %+v", got.Matrix)
	}
}
