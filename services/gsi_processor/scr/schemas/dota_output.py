from pydantic import BaseModel, Field, AliasPath


class GameStateRequest(BaseModel):
    # game info
    account_id: int
    match_id: int
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
    level0: int 
    castrange0: int 
    manacost0: int 
    cooldown0: int 

    level1: int 
    castrange1: int 
    manacost1: int 
    cooldown1: int 

    level2: int 
    castrange2: int 
    manacost2: int
    cooldown2: int

    level3: int
    castrange3: int
    manacost3: int
    cooldown3: int


    # distances
    # nearest_ally_distance: float
    # nearest_enemy_distance: float

    # nearest_ally_tp_place_distance: float
    nearest_ally_tower_distance: int
    nearest_enemy_tower_distance: int

    enemy_1_last_seen_x: int
    enemy_1_last_seen_y: int
    enemy_1_last_seen_square: int
    enemy_1_last_seen_distance: int
    enemy_1_last_seen_time: int

    enemy_2_last_seen_x: int
    enemy_2_last_seen_y: int
    enemy_2_last_seen_square: int
    enemy_2_last_seen_distance: int
    enemy_2_last_seen_time: int

    enemy_3_last_seen_x: int
    enemy_3_last_seen_y: int
    enemy_3_last_seen_square: int
    enemy_3_last_seen_distance: int
    enemy_3_last_seen_time: int

    enemy_4_last_seen_x: int
    enemy_4_last_seen_y: int
    enemy_4_last_seen_square: int
    enemy_4_last_seen_distance: int
    enemy_4_last_seen_time: int

    enemy_5_last_seen_x: int
    enemy_5_last_seen_y: int
    enemy_5_last_seen_square: int
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
    name: str = ""
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