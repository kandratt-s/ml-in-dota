FROM golang:1.24-alpine AS build
WORKDIR /src

COPY services/bff/go.mod services/bff/go.sum ./
RUN go mod download

COPY services/bff/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/bff ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
COPY --from=build /out/bff /app/bff
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/app/bff"]
