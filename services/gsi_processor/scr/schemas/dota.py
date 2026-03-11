from pydantic import BaseModel, computed_field


class Map(BaseModel):
    matchid: int
    game_time: int
    daytime: bool
    radiant_score: int
    dire_score: int


class Player(BaseModel):
    accountid: int
    kills: int
    deaths: int
    assists: int
    last_hits: int
    denies: int
    gold: int

    @computed_field
    @property
    def networth(self) -> int:
        pass


class Hero(BaseModel):
    xpos: int
    ypos: int
    id: int
    level: int
    health: int
    max_health: int
    mana: int
    max_mana: int

    @computed_field
    @property
    def sqare() -> int:
        pass

    @computed_field
    @property
    def agility() -> int:
        pass

    @computed_field
    @property
    def intellect() -> int:
        pass

    @computed_field
    @property
    def strength() -> int:
        pass
    
    @computed_field
    @property
    def magical_resistance() -> int:
        pass

    @computed_field
    @property
    def armor() -> int:
        pass

    @computed_field
    @property
    def bkb_cooldown() -> int:
        pass

    @computed_field
    @property
    def movespeed() -> int:
        pass
    

class Ability(BaseModel):
    name: str
    level: int
    can_cast: bool
    passive: bool
    cooldown: int
    max_cooldown: int
    ultimate: bool


class Item(BaseModel):
    name: str


class Building(BaseModel):
    health: int
    max_health: int


class MinimapObject(BaseModel):
    xpos: int
    ypos: int
    name: str


class AuthToken(BaseModel):
    token: str


class GSIDota(BaseModel):
    map: Map
    player: Player
    hero: Hero
    abilities: dict[str, Ability]
    items: dict[str, Item]
    buildings: dict[str, dict[str, Building]]
    minimap: dict[str, MinimapObject]