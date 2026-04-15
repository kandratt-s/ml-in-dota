CREATE SCHEMA IF NOT EXISTS bot;

CREATE TABLE IF NOT EXISTS bot.users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    token TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);


ALTER ROLE app SET search_path TO bot, public;

create schema if not exists dataset;

CREATE TABLE IF NOT EXISTS dataset.match_features (
    id BIGSERIAL PRIMARY KEY,

    -- game info
    account_id BIGINT,
    match_id BIGINT,
    game_time INT,

    is_day INT,           -- 0 или 1
    is_radiant INT,       -- 0 или 1

    radiant_score INT,
    dire_score INT,

    -- hero info
    hero_id INT,
    level INT,

    kills INT,
    deaths INT,
    assists INT,

    last_hits INT,
    denies INT,

    gold INT,
    net_worth INT,

    x INT,
    y INT,
    square INT,

    xp INT,

    health INT,
    mana INT,

    max_health INT,
    max_mana INT,

    agility INT,
    intellect INT,
    strength INT,

    magical_resistance INT,
    armor INT,

    bkb_cooldown INT,

    movespeed INT,

    -- abilities 
    ability1_level INT,
    ability1_castrange INT,
    ability1_manacost INT,
    ability1_cooldown INT,

    ability2_level INT,
    ability2_castrange INT,
    ability2_manacost INT,
    ability2_cooldown INT,

    ability3_level INT,
    ability3_castrange INT,
    ability3_manacost INT,
    ability3_cooldown INT,

    ability4_level INT,
    ability4_castrange INT,
    ability4_manacost INT,
    ability4_cooldown INT,

    -- enemies and allies
    nearest_ally_tower_distance INT,
    nearest_enemy_tower_distance INT,

    slot_1_id INT,
    enemy_1_name VARCHAR,
    enemy_1_last_seen_x INT,
    enemy_1_last_seen_y INT,
    enemy_1_last_seen_sqare INT,
    enemy_1_last_seen_distance INT,
    enemy_1_last_seen_time INT,

    slot_2_id INT,
    enemy_2_name VARCHAR,
    enemy_2_last_seen_x INT,
    enemy_2_last_seen_y INT,
    enemy_2_last_seen_sqare INT,
    enemy_2_last_seen_distance INT,
    enemy_2_last_seen_time INT,

    slot_3_id INT,
    enemy_3_name VARCHAR,
    enemy_3_last_seen_x INT,
    enemy_3_last_seen_y INT,
    enemy_3_last_seen_sqare INT,
    enemy_3_last_seen_distance INT,
    enemy_3_last_seen_time INT,

    slot_4_id INT,
    enemy_4_name VARCHAR,
    enemy_4_last_seen_x INT,
    enemy_4_last_seen_y INT,
    enemy_4_last_seen_sqare INT,
    enemy_4_last_seen_distance INT,
    enemy_4_last_seen_time INT,

    slot_5_id INT,
    enemy_5_name VARCHAR,
    enemy_5_last_seen_x INT,
    enemy_5_last_seen_y INT,
    enemy_5_last_seen_sqare INT,
    enemy_5_last_seen_distance INT,
    enemy_5_last_seen_time INT,

    -- active items (0 or 1)
    item_black_king_bar INT,
    item_blink INT,
    item_force_staff INT,
    item_basher INT,
    item_abyssal_blade INT,
    item_nullifier INT,
    item_lotus_orb INT,
    item_travel_boots INT,
    item_tpscroll INT,
    item_phase_boots INT,
    item_silver_edge INT,
    item_heart INT,
    item_sphere INT,
    item_manta INT,
    item_blade_mail INT,
    item_aeon_disk INT,
    item_pipe INT,

    -- target variable (0 or 1)
    dead_in_1 INT,
    dead_in_5 INT,
    dead_in_10 INT,
    dead_in_15 INT,
    dead_in_20 INT
);

create index idx_match_time on dataset.match_features (match_id, game_time);
    
