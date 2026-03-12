package postgres

import (
	"database/sql"
	"fmt"
	"log"
	"time"
)

func ConnectDB() *sql.DB {
	dsn := "postgres://app:passwoappassrd@localhost:5432/app_db"

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
