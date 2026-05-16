package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	HTTPAddr        string
	RedisAddr       string
	RedisPassword   string
	RedisDB         int
	PredictionKey   string
	PollInterval    time.Duration
	AllowedOrigins  []string
	ShutdownTimeout time.Duration
}

func Load() Config {
	return Config{
		HTTPAddr:        env("BFF_ADDR", ":8080"),
		RedisAddr:       env("REDIS_ADDR", env("REDIS_HOST", "redis")+":"+env("REDIS_PORT", "6379")),
		RedisPassword:   os.Getenv("REDIS_PASSWORD"),
		RedisDB:         envInt("REDIS_DB", 0),
		PredictionKey:   env("PREDICTION_KEY_PREFIX", "predictions"),
		PollInterval:    time.Duration(envInt("PREDICTION_POLL_MS", 1000)) * time.Millisecond,
		AllowedOrigins:  []string{"*"},
		ShutdownTimeout: 10 * time.Second,
	}
}

func env(k, def string) string {
	if v, ok := os.LookupEnv(k); ok && v != "" {
		return v
	}
	return def
}

func envInt(k string, def int) int {
	if v, ok := os.LookupEnv(k); ok && v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}
