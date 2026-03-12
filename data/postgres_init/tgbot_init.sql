CREATE SCHEMA IF NOT EXISTS bot;

CREATE TABLE IF NOT EXISTS bot.users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    token TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

create schema if not exists dataset;

create table if not exists dataset.match_features (
    row_id SERIAL PRIMARY KEY,
    account_id BIGINT,
    match_id BIGINT NOT NULL,
    game_time INTEGER NOT NULL,
    is_day BOOLEAN,
    is_radiant BOOLEAN,
    radiant_score INTEGER,
    dire_score INTEGER,
    
    heroes_state JSONB,
    -- -- Состояние героя
    -- hero_id VARCHAR(64),
    -- level INTEGER,
    -- kills INTEGER,
    -- deaths INTEGER,
    -- assists INTEGER,
    -- last_hits INTEGER,
    -- denies INTEGER,
    -- gold INTEGER,
    -- xp INTEGER,
    -- x REAL,
    -- y REAL,
    -- health REAL,
    -- max_health REAL,
    -- mana REAL,
    -- max_mana REAL,
    -- agility INTEGER,
    -- intellect INTEGER,
    -- strength INTEGER,
    -- magical_resistance INTEGER,
    -- armor REAL,
    -- bkb_cooldown REAL,
    -- movespeed INTEGER,



    -- abilities JSONB -- (level castrange manacos tcooldown)

    -- -- Окружение и Vision
    -- nearest_ally_distance REAL,
    -- nearest_enemy_distance REAL,
    -- vision
    -- nearest_enemy_last_seen_x REAL,
    -- nearest_enemy_last_seen_y REAL,
    -- nearest_enemy_time_from_last_seen REAL,
    -- nearest_ally_tp_distance REAL,
    -- nearest_ally_tower_distance REAL,
    -- nearest_enemy_tower_distance REAL,

    -- -- Метки смерти (Target Labels для ML)
    -- is_dead_1s BOOLEAN DEFAULT FALSE,
    -- is_dead_5s BOOLEAN DEFAULT FALSE,
    -- is_dead_10s BOOLEAN DEFAULT FALSE,
    -- is_dead_15s BOOLEAN DEFAULT FALSE,
    -- is_dead_20s BOOLEAN DEFAULT FALSE,

    -- -- Предметы (Inventory Flags)
    -- has_bkb BOOLEAN DEFAULT FALSE,
    -- has_blink BOOLEAN DEFAULT FALSE,
    -- has_force_staff BOOLEAN DEFAULT FALSE,
    -- has_basher BOOLEAN DEFAULT FALSE,
    -- has_abyssal BOOLEAN DEFAULT FALSE,
    -- has_nullifier BOOLEAN DEFAULT FALSE,
    -- has_lotus BOOLEAN DEFAULT FALSE,
    -- has_travel_boots BOOLEAN DEFAULT FALSE,
    -- has_tp_scroll BOOLEAN DEFAULT FALSE,
    -- has_phase_boots BOOLEAN DEFAULT FALSE,
    -- has_silver_edge BOOLEAN DEFAULT FALSE,
    -- has_heart BOOLEAN DEFAULT FALSE,
    -- has_linkens BOOLEAN DEFAULT FALSE,
    -- has_manta BOOLEAN DEFAULT FALSE,
    -- has_blade_mail BOOLEAN DEFAULT FALSE,
    -- has_aeon_disk BOOLEAN DEFAULT FALSE,
    -- has_pipe BOOLEAN DEFAULT FALSE

    vision JSONB,

);

create index idx_match_time on dataset.match_features (match_id, game_time);
    