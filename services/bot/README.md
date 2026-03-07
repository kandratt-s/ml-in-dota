# Telegram Bot Service

Telegram бот для ML-in-Dota проекта с регистрацией пользователей и управлением токенами.

## Структура проекта

```
services/bot/
├── scr/                     # Исходный код приложения
│   ├── handlers/           # Обработчики сообщений
│   ├── models/            # SQLAlchemy модели
│   ├── schemas/           # Pydantic схемы
│   ├── config.py          # Конфигурация
│   ├── keyboards.py       # Клавиатуры
│   ├── main.py           # Главный файл приложения
│   ├── states.py         # FSM состояния
│   └── user_token.py     # Генерация токенов
├── db/                    # База данных
│   ├── repos/            # Репозитории
│   └── queries/          # SQL запросы (deprecated)
├── migrations/           # Alembic миграции
├── migrate.py           # Скрипт для управления миграциями
├── alembic.ini         # Конфигурация Alembic
├── pyproject.toml      # Зависимости Poetry
└── Dockerfile          # Docker конфигурация
```

## Зависимости

- **aiogram** - Telegram Bot API
- **SQLAlchemy** - ORM для работы с базой данных
- **Alembic** - Система миграций
- **asyncpg** - Асинхронный драйвер PostgreSQL
- **Pydantic** - Валидация данных

## Установка и запуск

### 1. Локальная разработка

```bash
# Установка зависимостей
poetry install

# Копирование конфигурации
cp .env.example .env
# Отредактируйте .env и добавьте ваш TELEGRAM_BOT_TOKEN

# Запуск миграций
python migrate.py upgrade

# Запуск бота
python scr/main.py
```

### 2. Docker

```bash
# Из корня проекта ml-in-dota
docker-compose up bot
```

## Работа с миграциями

```bash
# Применить все миграции
python migrate.py upgrade

# Создать новую миграцию
python migrate.py create "Описание изменений"

# Посмотреть историю
python migrate.py history

# Посмотреть текущую версию
python migrate.py current

# Откатить к базовой версии
python migrate.py downgrade base
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - (обязательно) |
| `DATABASE_URL` | URL подключения к БД | - (обязательно) |
| `TOKEN_SECRET` | Секрет для генерации токенов | ml-in-dota-default-secret |

## Архитектура

### Модели данных

- **User** - Пользователь с telegram_id и токеном
- **Схемы Pydantic** для валидации входящих/исходящих данных

### Репозитории

- **UserRepository** - Операции с пользователями (создание, поиск, обновление)

### Обработчики

- **registration** - Регистрация пользователей и управление токенами

## Функциональность

1. **Регистрация пользователей**
   - Ввод Steam Account ID
   - Ввод пароля (минимум 4 символа)
   - Генерация уникального токена
   - Сохранение в базу данных

2. **Управление токенами**
   - Просмотр текущего токена
   - Перерегистрация (обновление токена)

3. **Безопасность**
   - HMAC-SHA256 для генерации токенов
   - Валидация данных с помощью Pydantic
   - Защита от SQL-инъекций через SQLAlchemy

## Разработка

### Добавление новых функций

1. Создайте модель в `scr/models/`
2. Создайте Pydantic схемы в `scr/schemas/`
3. Создайте репозиторий в `db/repos/`
4. Создайте обработчики в `scr/handlers/`
5. Создайте миграцию: `python migrate.py create "описание"`

### Линтинг и типизация

```bash
# Проверка кода
poetry run ruff check .
poetry run mypy scr/
```