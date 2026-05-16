package redisclient

import (
	"context"
	"testing"
)

func TestFakeStore_StartStop(t *testing.T) {
	ctx := context.Background()
	f := NewFakeStore()

	if err := f.StartSession(ctx, Session{
		Token:  "t1",
		Config: SessionConfig{Model: "boosting", Time: 10, Interval: 1, FullMap: true},
	}); err != nil {
		t.Fatalf("start: %v", err)
	}

	got, err := f.GetSession(ctx, "t1")
	if err != nil || got == nil {
		t.Fatalf("expected session, err=%v session=%v", err, got)
	}
	if got.Config.Model != "boosting" {
		t.Fatalf("unexpected model: %s", got.Config.Model)
	}

	if err := f.StopSession(ctx, "t1"); err != nil {
		t.Fatalf("stop: %v", err)
	}
	got, _ = f.GetSession(ctx, "t1")
	if got != nil {
		t.Fatalf("expected nil after stop, got %+v", got)
	}
}

func TestFakeStore_RejectsEmptyToken(t *testing.T) {
	ctx := context.Background()
	f := NewFakeStore()
	if err := f.StartSession(ctx, Session{Token: ""}); err == nil {
		t.Fatalf("expected error on empty token")
	}
	if err := f.StopSession(ctx, ""); err == nil {
		t.Fatalf("expected error on empty token")
	}
}

func TestFakeStore_PredictionFallback(t *testing.T) {
	ctx := context.Background()
	f := NewFakeStore()
	f.SetPrediction("__latest__", `{"radiant_win_prob":0.7}`)
	v, err := f.GetPrediction(ctx, "missing-token")
	if err != nil {
		t.Fatalf("unexpected err: %v", err)
	}
	if v == "" {
		t.Fatalf("expected fallback prediction value")
	}
}
