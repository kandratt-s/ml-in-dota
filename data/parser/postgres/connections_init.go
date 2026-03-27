package postgres

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"
)

func ConnectDB() *sql.DB {
	dsn := "postgres://app:appass@localhost:5432/app_db?sslmode=disable"

	db, err := sql.Open("pgx", dsn)
	if err != nil {
		log.Fatalf("Ошибка конфигурации БД: %v", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(25)
	db.SetConnMaxLifetime(5 * time.Minute)

	err = db.Ping()
	if err != nil {
		log.Fatalf("Не удалось подключиться к Postgres: %v", err)
		return nil
	}

	fmt.Println("Успешное подключение к PostgreSQL!")
	return db
}
