package redisclient

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
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
	// GetHeatmap returns the global heatmap (legacy).
	GetHeatmap(ctx context.Context) ([][]float64, error)
	// GetHeatmapForToken returns token-scoped heatmap written by inference.
	GetHeatmapForToken(ctx context.Context, token string) ([][]float64, error)
	// SetPredictionConfig stores per-token prediction config for inference to read.
	SetPredictionConfig(ctx context.Context, token string, cfg SessionConfig) error
	Ping(ctx context.Context) error
	Close() error
}

type RedisStore struct {
	rdb        *redis.Client
	heatmapKey string
}

const (
	activeKeyTTL        = 60 * time.Minute
	predictionConfigTTL = 60 * time.Minute
)

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

func predictionConfigKey(token string) string { return "prediction-config:" + token }

func tokenHeatmapKey(baseKey, token string) string {
	if token == "" || token == "default" {
		return baseKey
	}
	return fmt.Sprintf("%s:%s", baseKey, token)
}

func snapshotKeyPattern(token string) string { return fmt.Sprintf("snapshot:%s:*", token) }

func (r *RedisStore) StartSession(ctx context.Context, s Session) error {
	if s.Token == "" {
		return errors.New("empty token")
	}
	data, err := json.Marshal(s)
	if err != nil {
		return fmt.Errorf("marshal session: %w", err)
	}
	return r.rdb.Set(ctx, activeKey(s.Token), data, activeKeyTTL).Err()
}

func (r *RedisStore) StopSession(ctx context.Context, token string) error {
	if token == "" {
		return errors.New("empty token")
	}
	keys := []string{
		activeKey(token),
		predictionConfigKey(token),
		tokenHeatmapKey(r.heatmapKey, token),
	}
	if err := r.rdb.Del(ctx, keys...).Err(); err != nil {
		return err
	}
	iter := r.rdb.Scan(ctx, 0, snapshotKeyPattern(token), 0).Iterator()
	var snapshotKeys []string
	for iter.Next(ctx) {
		snapshotKeys = append(snapshotKeys, iter.Val())
	}
	if err := iter.Err(); err != nil {
		return err
	}
	if len(snapshotKeys) > 0 {
		if err := r.rdb.Del(ctx, snapshotKeys...).Err(); err != nil {
			return err
		}
	}
	// Additionally, scan for any other keys containing the token and delete them.
	// This is aggressive by design because the user requested removing all
	// redis artifacts related to the token. Use a SCAN iterator to avoid
	// blocking Redis on large keyspaces and delete in batches.
	pattern := "*" + token + "*"
	it := r.rdb.Scan(ctx, 0, pattern, 0).Iterator()
	var toDelete []string
	for it.Next(ctx) {
		k := it.Val()
		// Skip if already collected
		toDelete = append(toDelete, k)
		if len(toDelete) >= 500 {
			if err := r.rdb.Del(ctx, toDelete...).Err(); err != nil {
				return err
			}
			toDelete = toDelete[:0]
		}
	}
	if err := it.Err(); err != nil {
		return err
	}
	if len(toDelete) > 0 {
		if err := r.rdb.Del(ctx, toDelete...).Err(); err != nil {
			return err
		}
	}

	// Remove matching entries from known Redis streams (inference input/output).
	streams := []string{"inference:input", "inference:output"}
	for _, stream := range streams {
		entries, err := r.rdb.XRange(ctx, stream, "-", "+").Result()
		if err != nil {
			// If the stream does not exist, skip
			if err == redis.Nil {
				continue
			}
			return err
		}
		var idsToDel []string
		for _, e := range entries {
			// Expect field 'data' holding JSON payload; check for token substring.
			for _, v := range e.Values {
				s, ok := v.(string)
				if !ok {
					continue
				}
				if strings.Contains(s, token) {
					idsToDel = append(idsToDel, e.ID)
					break
				}
			}
			if len(idsToDel) >= 500 {
				if err := r.rdb.XDel(ctx, stream, idsToDel...).Err(); err != nil {
					return err
				}
				// attempt to ack in consumer group if present
				_ = r.rdb.XAck(ctx, stream, stream+":group", idsToDel...).Err()
				idsToDel = idsToDel[:0]
			}
		}
		if len(idsToDel) > 0 {
			if err := r.rdb.XDel(ctx, stream, idsToDel...).Err(); err != nil {
				return err
			}
			_ = r.rdb.XAck(ctx, stream, stream+":group", idsToDel...).Err()
		}
	}
	return nil
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

func (r *RedisStore) GetHeatmapForToken(ctx context.Context, token string) ([][]float64, error) {
	key := r.heatmapKey
	if token != "" && token != "default" {
		key = fmt.Sprintf("%s:%s", r.heatmapKey, token)
	}
	val, err := r.rdb.Get(ctx, key).Result()
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

func (r *RedisStore) SetPredictionConfig(ctx context.Context, token string, cfg SessionConfig) error {
	if token == "" {
		return errors.New("empty token")
	}
	key := predictionConfigKey(token)
	data, err := json.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("marshal prediction config: %w", err)
	}
	return r.rdb.Set(ctx, key, data, predictionConfigTTL).Err()
}

func (r *RedisStore) Ping(ctx context.Context) error { return r.rdb.Ping(ctx).Err() }
func (r *RedisStore) Close() error                   { return r.rdb.Close() }
