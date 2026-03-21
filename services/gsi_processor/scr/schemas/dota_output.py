from pydantic import BaseModel, Field, AliasPath
    

class GameStateRequest(BaseModel):
    # game info
    account_id: int = Field(validation_alias=AliasPath("player", "accountid"))
    match_id: int = Field(validation_alias=AliasPath("map", "matchid"))
    game_time: int = Field(validation_alias=AliasPath("map", "game_time"))

    is_day: bool = Field(validation_alias=AliasPath("map", "daytime"))
    is_radiant: bool

    radiant_score: int = Field(validation_alias=AliasPath("map", "radiant_score"))
    dire_score: int = Field(validation_alias=AliasPath("map", "dire_score"))

    # hero
    hero_id: int = Field(validation_alias=AliasPath("hero", "id"))
    level: int = Field(validation_alias=AliasPath("hero", "level"))

    kills: int = Field(validation_alias=AliasPath("player", "kills"))
    deaths: int = Field(validation_alias=AliasPath("player", "deaths"))
    assists: int = Field(validation_alias=AliasPath("player", "assists"))
    last_hits: int = Field(validation_alias=AliasPath("player", "last_hits"))
    denies: int = Field(validation_alias=AliasPath("player", "denies"))

    gold: int = Field(validation_alias=AliasPath("player", "gold"))
    net_worth: int

    x: float = Field(validation_alias=AliasPath("hero", "xpos"))
    y: float = Field(validation_alias=AliasPath("hero", "ypos"))
    square: int

    xp: int = Field(validation_alias=AliasPath("hero", "xp"))

    health: int = Field(validation_alias=AliasPath("hero", "health"))
    mana: int = Field(validation_alias=AliasPath("hero", "mana"))

    max_health: int = Field(validation_alias=AliasPath("hero", "max_health"))
    max_mana: int = Field(validation_alias=AliasPath("hero", "max_mana"))

    agility: int
    intellect: int
    strength: int

    magical_resistance: int
    armor: float

    bkb_cooldown: int
    movespeed: int

    # abilities
    level0: int = Field(validation_alias=AliasPath("abilities", "ability0", "level"))
    castrange0: int 
    manacost0: int = Field(validation_alias=AliasPath("abilities", "ability0", "manacost"))
    cooldown0: int = Field(validation_alias=AliasPath("abilities", "ability0", "cooldown"))

    level1: int = Field(validation_alias=AliasPath("abilities", "ability1", "level"))
    castrange1: int 
    manacost1: int = Field(validation_alias=AliasPath("abilities", "ability1", "manacost"))
    cooldown1: int = Field(validation_alias=AliasPath("abilities", "ability1", "cooldown"))

    level2: int = Field(validation_alias=AliasPath("abilities", "ability2", "level"))
    castrange2: int 
    manacost2: int = Field(validation_alias=AliasPath("abilities", "ability2", "manacost"))
    cooldown2: int = Field(validation_alias=AliasPath("abilities", "ability2", "cooldown"))

    level3: int = Field(validation_alias=AliasPath("abilities", "ability3", "level"))
    castrange3: int
    manacost3: int = Field(validation_alias=AliasPath("abilities", "ability3", "manacost"))
    cooldown3: int = Field(validation_alias=AliasPath("abilities", "ability3", "cooldown"))


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
    item_bkb: bool
    item_blink: bool
    item_force_staff: bool
    item_skull_basher: bool
    item_abyssal_blade: bool
    item_nullifier: bool
    item_lotus_orb: bool
    item_travel_boots: bool
    item_tpscroll: bool
    item_phase_boots: bool
    item_silver_edge: bool
    item_heart: bool
    item_linkens: bool
    item_manta: bool
    item_blade_mail: bool
    item_aeon_disk: bool
    item_pipe: bool