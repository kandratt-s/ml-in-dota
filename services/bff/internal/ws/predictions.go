package ws

import (
	"context"
	"encoding/json"
	"log"
	"math/rand"
	"net/http"
	"time"

	"github.com/ml-in-dota/bff/internal/redisclient"
	"nhooyr.io/websocket"
)

type Hub struct {
	Store    redisclient.Store
	Interval time.Duration
}

func NewHub(store redisclient.Store, interval time.Duration) *Hub {
	if interval <= 0 {
		interval = time.Second
	}
	return &Hub{Store: store, Interval: interval}
}

type predictionFrame struct {
	Token     string    `json:"token"`
	Timestamp time.Time `json:"timestamp"`
	// Probability of radiant win (0..1). When live predictions are present in
	// Redis we forward those verbatim instead.
	RadiantWinProb float64 `json:"radiant_win_prob"`
	Source         string  `json:"source"`
}

// ServeHTTP upgrades the connection to a websocket and streams prediction
// frames for the token passed via ?token=... query string. If a real
// prediction blob is present in Redis it is forwarded as-is; otherwise a
// mocked frame is sent so the UI has something to react to during development.
func (h *Hub) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	if token == "" {
		http.Error(w, "token query parameter required", http.StatusBadRequest)
		return
	}

	c, err := websocket.Accept(w, r, &websocket.AcceptOptions{
		InsecureSkipVerify: true, // origins are constrained by the CORS middleware
	})
	if err != nil {
		log.Printf("ws accept: %v", err)
		return
	}
	defer c.Close(websocket.StatusInternalError, "stream ended")

	ctx := r.Context()
	ticker := time.NewTicker(h.Interval)
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

	if payload, err := h.Store.GetPrediction(ctx, token); err == nil && payload != "" {
		return c.Write(sendCtx, websocket.MessageText, []byte(payload))
	}

	frame := predictionFrame{
		Token:          token,
		Timestamp:      time.Now().UTC(),
		RadiantWinProb: mockProb(),
		Source:         "mock",
	}
	b, _ := json.Marshal(frame)
	return c.Write(sendCtx, websocket.MessageText, b)
}

func mockProb() float64 {
	// Simple bounded random walk around 0.5 keeps the UI looking lively.
	return 0.5 + (rand.Float64()-0.5)*0.4
}
