package ws

import (
	"context"
	"encoding/json"
	"log"
	"math"
	"math/rand"
	"net/http"
	"time"

	"github.com/ml-in-dota/bff/internal/redisclient"
	"nhooyr.io/websocket"
)

const (
	defaultCells      = 32
	minStreamInterval = 200 * time.Millisecond
	maxStreamInterval = 60 * time.Second
)

type Hub struct {
	Store           redisclient.Store
	DefaultInterval time.Duration
	Cells           int
}

func NewHub(store redisclient.Store, defaultInterval time.Duration) *Hub {
	if defaultInterval <= 0 {
		defaultInterval = time.Second
	}
	return &Hub{Store: store, DefaultInterval: defaultInterval, Cells: defaultCells}
}

// intervalForToken decides how often this WS connection should emit frames.
// Priority: session config in Redis (set by /api/start) → hub default → 1s.
// The result is clamped to [minStreamInterval, maxStreamInterval] so a
// malformed value can't either pin a CPU or freeze the UI.
func intervalForToken(ctx context.Context, store redisclient.Store, token string, def time.Duration) time.Duration {
	chosen := def
	if s, err := store.GetSession(ctx, token); err == nil && s != nil && s.Config.Interval > 0 {
		chosen = time.Duration(s.Config.Interval) * time.Second
	}
	if chosen < minStreamInterval {
		chosen = minStreamInterval
	}
	if chosen > maxStreamInterval {
		chosen = maxStreamInterval
	}
	return chosen
}

// heatmapFrame is the on-the-wire shape the frontend subscribes to. We keep
// the matrix explicit (no compression) — 32×32 floats fit comfortably in a
// single websocket text frame.
type heatmapFrame struct {
	Token     string      `json:"token"`
	Timestamp time.Time   `json:"timestamp"`
	Cells     int         `json:"cells"`
	MaxValue  float64     `json:"max_value"`
	Matrix    [][]float64 `json:"matrix"`
	Source    string      `json:"source"` // "redis" or "mock"
}

// ServeHTTP upgrades to a websocket and streams heatmap frames for the token
func (h *Hub) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	if token == "" {
		http.Error(w, "token query parameter required", http.StatusBadRequest)
		return
	}

	interval := intervalForToken(r.Context(), h.Store, token, h.DefaultInterval)

	c, err := websocket.Accept(w, r, &websocket.AcceptOptions{
		InsecureSkipVerify: true,
	})
	if err != nil {
		log.Printf("ws accept: %v", err)
		return
	}
	defer c.Close(websocket.StatusInternalError, "stream ended")
	log.Printf("ws open token=%s interval=%s", token, interval)

	ctx := r.Context()
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	if err := h.sendOnce(ctx, c, token); err != nil {
		log.Printf("ws initial send: %v", err)
		return
	}

	for {
		select {
		case <-ctx.Done():
			c.Close(websocket.StatusNormalClosure, "client gone")
			return
		case <-ticker.C:
			if err := h.sendOnce(ctx, c, token); err != nil {
				return
			}
		}
	}
}

func (h *Hub) sendOnce(ctx context.Context, c *websocket.Conn, token string) error {
	sendCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	cells := h.Cells
	if cells <= 0 {
		cells = defaultCells
	}

	var (
		matrix [][]float64
		source = "none"
	)
	// Prefer token-scoped heatmap written by inference: heat_map:<token>
	if m, err := h.Store.GetHeatmapForToken(ctx, token); err != nil {
		log.Printf("heatmap read failed for token=%s: %v", token, err)
		// don't silently fallback to mock; skip sending a frame so frontend
		// doesn't receive fabricated data. Connection remains open and we
		// will retry on next tick.
		return nil
	} else if len(m) > 0 {
		matrix = m
		source = "redis"
		cells = len(m)
	} else {
		// No token-specific heatmap available. Attempt legacy global key.
		if gm, gerr := h.Store.GetHeatmap(ctx); gerr != nil {
			log.Printf("global heatmap read failed: %v", gerr)
			return nil
		} else if len(gm) > 0 {
			matrix = gm
			source = "redis"
			cells = len(gm)
		} else {
			// No data available; do not emit mock frames by default.
			// emit a lightweight heartbeat so clients know connection is alive
			hb := map[string]any{"type": "heartbeat", "timestamp": time.Now().UTC()}
			if b, err := json.Marshal(hb); err == nil {
				_ = c.Write(sendCtx, websocket.MessageText, b)
			}
			return nil
		}
	}

	frame := heatmapFrame{
		Token:     token,
		Timestamp: time.Now().UTC(),
		Cells:     cells,
		MaxValue:  maxValue(matrix),
		Matrix:    matrix,
		Source:    source,
	}
	b, err := json.Marshal(frame)
	if err != nil {
		return err
	}
	return c.Write(sendCtx, websocket.MessageText, b)
}

func maxValue(m [][]float64) float64 {
	max := 0.0
	for _, row := range m {
		for _, v := range row {
			if v > max {
				max = v
			}
		}
	}
	if max == 0 {
		return 1.0
	}
	return max
}

// mockMatrix produces
func mockMatrix(cells int, tick uint64) [][]float64 {
	t := float64(tick) * 0.07
	cx := float64(cells)/2 + math.Cos(t)*float64(cells)*0.3
	cy := float64(cells)/2 + math.Sin(t*0.8)*float64(cells)*0.3
	sigma := float64(cells) * 0.18
	denom := 2 * sigma * sigma

	out := make([][]float64, cells)
	for r := 0; r < cells; r++ {
		row := make([]float64, cells)
		for col := 0; col < cells; col++ {
			dx := float64(col) - cx
			dy := float64(r) - cy
			v := math.Exp(-(dx*dx + dy*dy) / denom)
			if rand.Float64() < 0.04 {
				v += rand.Float64() * 0.3
			}
			if v > 1 {
				v = 1
			}
			row[col] = v
		}
		out[r] = row
	}
	return out
}
