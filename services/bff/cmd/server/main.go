package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"github.com/ml-in-dota/bff/internal/config"
	"github.com/ml-in-dota/bff/internal/handlers"
	"github.com/ml-in-dota/bff/internal/redisclient"
	"github.com/ml-in-dota/bff/internal/ws"
)

func main() {
	cfg := config.Load()

	store := redisclient.New(cfg.RedisAddr, cfg.RedisPassword, cfg.RedisDB, cfg.PredictionKey)
	defer store.Close()

	if err := store.Ping(context.Background()); err != nil {
		log.Printf("warning: redis ping failed at startup (%s): %v", cfg.RedisAddr, err)
	}

	api := handlers.New(store)
	hub := ws.NewHub(store, cfg.PollInterval)

	r := buildRouter(api, hub, cfg.AllowedOrigins)

	srv := &http.Server{
		Addr:         cfg.HTTPAddr,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 0, // websocket streams need unbounded writes
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("bff listening on %s", cfg.HTTPAddr)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("http server: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop
	log.Println("shutting down")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Printf("shutdown: %v", err)
	}
}

func buildRouter(api *handlers.API, hub *ws.Hub, allowed []string) http.Handler {
	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(30 * time.Second))
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   allowed,
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: false,
		MaxAge:           300,
	}))

	r.Get("/health", api.Health)
	r.Route("/api", func(r chi.Router) {
		r.Post("/start", api.Start)
		r.Post("/stop", api.Stop)
	})
	r.Handle("/ws/predictions", hub)
	return r
}
