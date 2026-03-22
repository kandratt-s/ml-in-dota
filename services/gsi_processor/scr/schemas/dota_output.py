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

    x: float 
    y: float 
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
    armor: float

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
    nearest_ally_distance: float
    nearest_enemy_distance: float

    nearest_ally_tp_place_distance: float
    nearest_ally_tower_distance: float
    nearest_enemy_tower_distance: float

    enemy_last_seen_x: float
    nearest_enemy_last_seen_y: float
    nearest_enemy_last_seen_time: int

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