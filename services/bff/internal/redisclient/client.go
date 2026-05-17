package redisclient

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type SessionConfig struct {
	Model    string `json:"model"`
	Time     int    `json:"time"`
	Interval int    `json:"interval"`
	FullMap  bool   `json:"full_map"`
}

type Session struct {
	Token  string        `json:"token"`
	Config SessionConfig `json:"config"`
}

// Store is the minimal Redis surface the BFF needs. Defining it as an interface
// lets handlers and tests swap in an in-memory fake.
type Store interface {
	StartSession(ctx context.Context, s Session) error
	StopSession(ctx context.Context, token string) error
	GetSession(ctx context.Context, token string) (*Session, error)
	GetHeatmap(ctx context.Context) ([][]float64, error)
	Ping(ctx context.Context) error
	Close() error
}

type RedisStore struct {
	rdb        *redis.Client
	heatmapKey string
}

func New(addr, password string, db int, heatmapKey string) *RedisStore {
	rdb := redis.NewClient(&redis.Options{
		Addr:         addr,
		Password:     password,
		DB:           db,
		DialTimeout:  3 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
	})
	return &RedisStore{rdb: rdb, heatmapKey: heatmapKey}
}

func activeKey(token string) string { return "active:" + token }

func (r *RedisStore) StartSession(ctx context.Context, s Session) error {
	if s.Token == "" {
		return errors.New("empty token")
	}
	data, err := json.Marshal(s)
	if err != nil {
		return fmt.Errorf("marshal session: %w", err)
	}
	return r.rdb.Set(ctx, activeKey(s.Token), data, 0).Err()
}

func (r *RedisStore) StopSession(ctx context.Context, token string) error {
	if token == "" {
		return errors.New("empty token")
	}
	return r.rdb.Del(ctx, activeKey(token)).Err()
}

func (r *RedisStore) GetSession(ctx context.Context, token string) (*Session, error) {
	val, err := r.rdb.Get(ctx, activeKey(token)).Result()
	if err != nil {
		if errors.Is(err, redis.Nil) {
			return nil, nil
		}
		return nil, err
	}
	var s Session
	if err := json.Unmarshal([]byte(val), &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func (r *RedisStore) GetHeatmap(ctx context.Context) ([][]float64, error) {
	val, err := r.rdb.Get(ctx, r.heatmapKey).Result()
	if err != nil {
		if errors.Is(err, redis.Nil) {
			return nil, nil
		}
		return nil, err
	}
	var matrix [][]float64
	if err := json.Unmarshal([]byte(val), &matrix); err != nil {
		return nil, fmt.Errorf("decode heatmap: %w", err)
	}
	return matrix, nil
}

func (r *RedisStore) Ping(ctx context.Context) error { return r.rdb.Ping(ctx).Err() }
func (r *RedisStore) Close() error                   { return r.rdb.Close() }
