CREATE SCHEMA IF NOT EXISTS train;

CREATE TABLE train.dataset(
    id BIGSERIAL PRIMARY KEY,

    -- game info
    account_id BIGINT,
    match_id BIGINT,
    game_time INT,

    is_day BOOLEAN,

    is_radiant BOOLEAN,

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

    x FLOAT,
    y FLOAT,
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
    armor FLOAT,

    bkb_cooldown INT,

    movespeed INT,

    -- abilities (пример для 4)
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
    nearest_ally_distance FLOAT,
    nearest_enemy_distance FLOAT,

    nearest_ally_tp_place_distance FLOAT,
    nearest_ally_tower_distance FLOAT,
    nearest_enemy_tower_distance FLOAT,

    nearest_enemy_last_seen_x FLOAT,
    nearest_enemy_last_seen_y FLOAT,
    nearest_enemy_last_seen_time INT,

    -- active(?) safe items
    item_bkb BOOLEAN,
    item_blink BOOLEAN,
    item_force_staff BOOLEAN,
    item_skull_basher BOOLEAN,
    item_abyssal_blade BOOLEAN,
    item_nullifier BOOLEAN,
    item_lotus_orb BOOLEAN,
    item_travel_boots BOOLEAN,
    item_tpscroll BOOLEAN,
    item_phase_boots BOOLEAN,
    item_silver_edge BOOLEAN,
    item_heart BOOLEAN,
    item_linkens BOOLEAN,
    item_manta BOOLEAN,
    item_blade_mail BOOLEAN,
    item_aeon_disk BOOLEAN,
    item_pipe BOOLEAN

    -- target variable
    dead_in_1 BOOLEAN,
    dead_in_5 BOOLEAN,
    dead_in_10 BOOLEAN,
    dead_in_15 BOOLEAN,
    dead_in_20 BOOLEAN,
);

ALTER ROLE app SET search_path TO train, public;