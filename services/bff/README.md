# BFF

Go backend-for-frontend that sits between the React UI and Redis. Responsible
for translating Start/Stop actions into Redis session state and streaming
predictions over a websocket.

## Endpoints

| Method | Path               | Purpose                                       |
| ------ | ------------------ | --------------------------------------------- |
| GET    | `/health`          | Reports Redis reachability                    |
| POST   | `/api/start`       | Persist `active:{token}` with config payload  |
| POST   | `/api/stop`        | Delete `active:{token}`                       |
| GET    | `/ws/predictions`  | Websocket stream of prediction frames         |

## Run

```bash
go run ./cmd/server
```

Environment:

- `BFF_ADDR` (default `:8080`)
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `PREDICTION_KEY_PREFIX` (default `predictions`)
- `PREDICTION_POLL_MS` (default `1000`)

## Tests

```bash
go test ./...
```
