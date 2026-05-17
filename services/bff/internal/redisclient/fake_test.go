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

func TestFakeStore_Heatmap(t *testing.T) {
	ctx := context.Background()
	f := NewFakeStore()

	m, err := f.GetHeatmap(ctx)
	if err != nil || m != nil {
		t.Fatalf("expected nil heatmap initially, got %v err=%v", m, err)
	}

	f.SetHeatmap([][]float64{{0.1, 0.2}, {0.3, 0.4}})
	m, err = f.GetHeatmap(ctx)
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	if len(m) != 2 || m[1][1] != 0.4 {
		t.Fatalf("unexpected heatmap: %+v", m)
	}

	// Mutating the returned copy must not affect stored state.
	m[0][0] = 99.0
	m2, _ := f.GetHeatmap(ctx)
	if m2[0][0] != 0.1 {
		t.Fatalf("FakeStore must return defensive copy, got %f", m2[0][0])
	}
}

func TestFakeStore_StopSessionCleansTokenArtifacts(t *testing.T) {
	ctx := context.Background()
	f := NewFakeStore()

	if err := f.StartSession(ctx, Session{Token: "t1", Config: SessionConfig{Model: "boosting", Time: 10, Interval: 1, FullMap: true}}); err != nil {
		t.Fatalf("start: %v", err)
	}
	if err := f.SetPredictionConfig(ctx, "t1", SessionConfig{Model: "logreg", Time: 5, Interval: 3, FullMap: false}); err != nil {
		t.Fatalf("set prediction config: %v", err)
	}
	f.SetHeatmapForToken("t1", [][]float64{{1}})
	f.SetSnapshotKey("t1")

	if err := f.StopSession(ctx, "t1"); err != nil {
		t.Fatalf("stop: %v", err)
	}

	if f.HasSession("t1") {
		t.Fatalf("session should be removed")
	}
	if _, ok := f.heatmapsPerToken["t1"]; ok {
		t.Fatalf("token heatmap should be removed")
	}
	if _, ok := f.predictionConfigs["t1"]; ok {
		t.Fatalf("prediction config should be removed")
	}
	if len(f.snapshotKeys) != 0 {
		t.Fatalf("snapshot keys should be removed, got %d", len(f.snapshotKeys))
	}
}
