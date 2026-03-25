from pydantic import BaseModel


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
    team_name: str

class Hero(BaseModel):
    xpos: int
    ypos: int
    id: int
    level: int
    health: int
    max_health: int
    mana: int
    max_mana: int
    xp: int
    

class Ability(BaseModel):
    name: str
    level: int
    cooldown: int


class Item(BaseModel):
    name: str
    cooldown: int = 0


# class Building(BaseModel):
#     health: int
#     max_health: int


class MinimapObject(BaseModel):
    xpos: int
    ypos: int
    unitname: str | None = None
    team: int | None = None


class AuthToken(BaseModel):
    token: str


class GSIRequest(BaseModel):
    map: Map
    player: Player
    hero: Hero
    abilities: dict[str, Ability]
    items: dict[str, Item]
    # buildings: dict[str, dict[str, Building]]
    minimap: dict[str, MinimapObject]
    auth: AuthToken