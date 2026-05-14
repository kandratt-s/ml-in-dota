from pydantic import BaseModel, Field, AliasPath


class GameStateRequest(BaseModel):
    # game info
    # account_id: int
    # match_id: int
    game_time: int

    is_day: bool
    is_radiant: bool

    radiant_score: int
    dire_score: int

    # hero
    hero_id: int 
    level: int 

    kills: int 
    deaths: int
    assists: int
    last_hits: int
    denies: int 

    gold: int 
    net_worth: int

    x: int 
    y: int 
    square: int

    xp: int 

    health: int 
    mana: int 

    max_health: int 
    max_mana: int 

    agility: int
    intellect: int
    strength: int

    magical_resistance: int
    armor: int

    bkb_cooldown: int
    movespeed: int

    # abilities
    ability1_level: int = 0
    ability1_castrange: int = 0
    ability1_manacost: int = 0
    ability1_cooldown: int = 0

    ability2_level: int = 0
    ability2_castrange: int = 0
    ability2_manacost: int = 0
    ability2_cooldown: int = 0

    ability3_level: int = 0
    ability3_castrange: int = 0
    ability3_manacost: int = 0
    ability3_cooldown: int = 0

    ability4_level: int = 0
    ability4_castrange: int = 0
    ability4_manacost: int = 0
    ability4_cooldown: int = 0


    # distances
    # nearest_ally_distance: float
    # nearest_enemy_distance: float

    # nearest_ally_tp_place_distance: float
    nearest_ally_tower_distance: int
    nearest_enemy_tower_distance: int

    enemy_1_name: int = 0
    enemy_1_last_seen_x: int
    enemy_1_last_seen_y: int
    enemy_1_last_seen_sqare: int
    enemy_1_last_seen_distance: int
    enemy_1_last_seen_time: int

    enemy_2_name: int = 0
    enemy_2_last_seen_x: int
    enemy_2_last_seen_y: int
    enemy_2_last_seen_sqare: int
    enemy_2_last_seen_distance: int
    enemy_2_last_seen_time: int

    enemy_3_name: int = 0
    enemy_3_last_seen_x: int
    enemy_3_last_seen_y: int
    enemy_3_last_seen_sqare: int
    enemy_3_last_seen_distance: int
    enemy_3_last_seen_time: int

    enemy_4_name: int = 0
    enemy_4_last_seen_x: int
    enemy_4_last_seen_y: int
    enemy_4_last_seen_sqare: int
    enemy_4_last_seen_distance: int
    enemy_4_last_seen_time: int

    enemy_5_name: int = 0
    enemy_5_last_seen_x: int
    enemy_5_last_seen_y: int
    enemy_5_last_seen_sqare: int
    enemy_5_last_seen_distance: int
    enemy_5_last_seen_time: int


    # items
    item_black_king_bar: bool
    item_blink: bool
    item_force_staff: bool
    item_basher: bool
    item_abyssal_blade: bool
    item_nullifier: bool
    item_lotus_orb: bool
    item_travel_boots: bool
    item_tpscroll: bool
    item_phase_boots: bool
    item_silver_edge: bool
    item_heart: bool
    item_sphere: bool
    item_manta: bool
    item_blade_mail: bool
    item_aeon_disk: bool
    item_pipe: bool


class AbilitySnapshot(BaseModel):
    level: int = 0
    cast_range: int = 0
    mana_cost: int = 0
    cooldown: int = 0


class EnemySnapshot(BaseModel):
    name: int = 0
    x: int = 0
    y: int = 0
    square: int = 0
    distance: int = 0
    time: int = 0


class HeroStatsSnapshot(BaseModel):
    strength: int = 0
    agility: int = 0
    intellect: int = 0


class CalculatedFeatures(BaseModel):
    hero: HeroStatsSnapshot
    magical_resistance: int = 0
    armor: int = 0
    movespeed: int = 0
    bkb_cooldown: int = 0
    net_worth: int = 0
    nearest_ally_tower_distance: int = 100000
    nearest_enemy_tower_distance: int = 100000
    abilities: list[AbilitySnapshot] = Field(default_factory=list)
    enemies: list[EnemySnapshot] = Field(default_factory=list)
    save_items: list[bool] = Field(default_factory=list)