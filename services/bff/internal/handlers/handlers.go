package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/ml-in-dota/bff/internal/redisclient"
)

type API struct {
	Store redisclient.Store
}

func New(store redisclient.Store) *API {
	return &API{Store: store}
}

type startRequest struct {
	Token  string                     `json:"token"`
	Config redisclient.SessionConfig  `json:"config"`
}

type stopRequest struct {
	Token string `json:"token"`
}

type errorResponse struct {
	Error string `json:"error"`
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, errorResponse{Error: msg})
}

func (a *API) Health(w http.ResponseWriter, r *http.Request) {
	if err := a.Store.Ping(r.Context()); err != nil {
		writeError(w, http.StatusServiceUnavailable, "redis unavailable")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func validateModel(m string) bool {
	return m == "boosting" || m == "logreg"
}

func validateTime(t int) bool {
	switch t {
	case 1, 5, 10, 15, 20:
		return true
	}
	return false
}

func validateInterval(i int) bool {
	switch i {
	case 1, 3, 5:
		return true
	}
	return false
}

func (a *API) Start(w http.ResponseWriter, r *http.Request) {
	var req startRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid json")
		return
	}
	req.Token = strings.TrimSpace(req.Token)
	if req.Token == "" {
		writeError(w, http.StatusBadRequest, "token is required")
		return
	}
	if !validateModel(req.Config.Model) {
		writeError(w, http.StatusBadRequest, "invalid model")
		return
	}
	if !validateTime(req.Config.Time) {
		writeError(w, http.StatusBadRequest, "invalid time")
		return
	}
	if !validateInterval(req.Config.Interval) {
		writeError(w, http.StatusBadRequest, "invalid interval")
		return
	}

	session := redisclient.Session{Token: req.Token, Config: req.Config}
	if err := a.Store.StartSession(r.Context(), session); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to persist session")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"status": "started", "token": req.Token})
}

func (a *API) Stop(w http.ResponseWriter, r *http.Request) {
	var req stopRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid json")
		return
	}
	req.Token = strings.TrimSpace(req.Token)
	if req.Token == "" {
		writeError(w, http.StatusBadRequest, "token is required")
		return
	}
	if err := a.Store.StopSession(r.Context(), req.Token); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to stop session")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "stopped"})
}
