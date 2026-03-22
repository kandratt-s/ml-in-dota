from typing import Any

from scr.schemas.dota_input import GSIRequest, Item
from scr.infra.redis import RedisClient
from scr.infra.config import settings
from scr.infra.catalog import JsonCatalog
from scr.schemas.dota_output import GameStateRequest


class GSIProcessorService:
    def __init__(self, redis: RedisClient, abilities_catalog: JsonCatalog, hero_stats_catalog: JsonCatalog, items_catalog: JsonCatalog):
        self.redis = redis
        self.abilities_catalog = abilities_catalog
        self.hero_stats_catalog = hero_stats_catalog
        self.items_catalog = items_catalog


    async def process_gsi_data(self, data: GSIRequest) -> GameStateRequest:
        """
        Из GSI потока делаем фичи
        """

        cell_id: int = self._get_cell_id(data.hero.xpos, data.hero.ypos)
        is_radiant: bool = self._is_radiant(data.player.team_name)
        save_items: list[bool] = self._get_bool_items(data.items)
        net_worth: int = self._get_net_worth(data.player.gold, data.items)
        stats : dict[str, int] = self._get_character_stats(data.hero.id, data.hero.level, data.items)
        magical_resistance: int = self._get_magical_resistance(data.hero.id, data.items)
        armor: int = self._get_armor(data.hero.id, data.hero.agility, data.items)
        movespeed: int = self._get_move_speed(data.hero.id, data.items)




    def _get_magical_resistance(self, intellect: int, items: dict[str, Item]) -> int:
        """
        Реализуем упрощенную формулу: https://dota2.fandom.com/ru/wiki/Магическое_сопротивление
            - врожденное сопротивление героя
            - бонус от итемов
        Игнорируем:
            - бафы и дебафы
            - способности, которые дают бонус/штраф, как свои/союзный, так и врагов
            - таланты
        """
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()
        resistance: float = (1 - 0.25) # const для всех героев

        for item in items.values():
            item_data: dict[str, Any] = item_catalog.get(item.name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])
            for attr in attributes:
                if attr.get("key") == "magic_resistance_aura": # aura в развании - пассвное, без - активное
                    resistance *= (1 - attr.get("value", 0) / 100.0)

        # resistance by intellect
        resistance += (1 - intellect * 0.1 / 100.0)

        return int(resistance * 100)

    
    def _get_armor(self, hero_id: int, agility: int, items: dict[str, Item]) -> int:
        """
        Реализуем упрощенную формулу: https://dota2.fandom.com/ru/wiki/Броня
            Не учитываем
                - отрицание брони
        """
        hero_catalog: list[dict[str, Any]] = self.hero_stats_catalog.as_list()
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()
        hero_data: dict[str, Any] = hero_catalog[hero_id - 1]
        base_armor: int = hero_data.get("base_armor", 0)

        items_armor: int = 0
        for item in items.values():
            item_data: dict[str, Any] = item_catalog.get(item.name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])
            for attr in attributes:
                if attr.get("key") == "aura_positive_armor" or attr.get("key") == "bonus_armor":
                    items_armor += attr.get("value", 0)

        return base_armor + int(0.167 * agility) + items_armor


    def _get_move_speed(self, hero_id: int, items: dict[str, Item]) -> int:
        """
        Реализуем упрощенную формулу с https://dota2.fandom.com/ru/wiki/Скорость_передвижения
            - базовая скорость героя
            - бонус от итемов
            Игнорируем:
            - бафы и дебафы
            - способности, которые дают бонус/штраф, как свои/союзный, так и врагов
            - таланты
            - ночные и дневные бонусы
            - бонус реки
        """
        hero_catalog: list[dict[str, Any]] = self.hero_stats_catalog.as_list()
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()
        hero_data: dict[str, Any] = hero_catalog[hero_id - 1] # -1 из-за формата /gsi_processor/local_data/heroStats.json
        base_move_speed: int = hero_data.get("move_speed", 0)
        multiplication_coefficient: float = 1.0

        boots_group: set[str] = {
            "item_boots",
            "item_arcane_boots",
            "item_travel_boots",
            "item_travel_boots_2",
            "item_phase_boots",
            "item_tranquil_boots ",
            "item_force_boots",
        }
        boots_group_max_speed: int = 0

        yasha_group: set[str] = {
            "item_yasha",
            "item_sange_and_yasha",
            "item_manta",
            "item_yasha_and_kaya"
        }
        yasha_group_max_speed: int = 0

        windlancer_group: set[str] = {
            "item_wind_lace",
        }
        windlancer_group_max_speed: int = 0

        other_items_max_speed: int = 0

        bonuses: set[str] = {"bonus_movement_speed", "movement_speed_percent_bonus"}


        for item in items.values():
            item_name: str = item.name
            item_data: dict[str, Any] = item_catalog.get(item_name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])


            for i in attributes:
                key: str | None = i.get("key")
                if key not in bonuses:
                    continue
                
                if key == "bonus_movement_speed":
                    if item_name in boots_group:
                        boots_group_max_speed = max(boots_group_max_speed, i.get("value", 0))
                    elif item_name in yasha_group:
                        yasha_group_max_speed = max(yasha_group_max_speed, i.get("value", 0))
                    elif item_name in windlancer_group:
                        windlancer_group_max_speed = max(windlancer_group_max_speed, i.get("value", 0))
                    else:
                        other_items_max_speed = max(other_items_max_speed, i.get("value", 0))
                else:
                    multiplication_coefficient += i.get("value", 0) / 100.0

        result: int = int((base_move_speed + boots_group_max_speed + yasha_group_max_speed + windlancer_group_max_speed + other_items_max_speed) \
                   * multiplication_coefficient)
        
        if result >= 550:
            return 550

        return result


    def _get_items_stats(self, items: dict[str, Item]) -> dict[str, int]:
        """
        Считаем суммарные статы от итемов
        """

        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()
        stat_keys: list[str] = [
            "bonus_all_stats",
            "bonus_agility",
            "bonus_strength",
            "bonus_intellect"
            ]

        total_stats: dict[str, int] = {key: 0 for key in stat_keys}

        for item in items.values():
            item_data: dict[str, Any] = item_catalog.get(item.name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])
            for attr in attributes:
                if attr.get("key") in stat_keys:
                    total_stats[attr["key"]] += attr.get("value", 0)
        
        all_stats_bonus: int = total_stats.get("bonus_all_stats", 0)
        total_stats["bonus_agility"] += all_stats_bonus
        total_stats["bonus_strength"] += all_stats_bonus
        total_stats["bonus_intellect"] += all_stats_bonus

        total_stats.pop("bonus_all_stats", None)

        return total_stats


    def _get_character_stats(self, hero_id: int, level:int, items: dict[str, Item]) -> dict[str, int]:
        """
        agility, strength, intelligence, magical_resistance, armor, movespeed
        """
        
        items_stats: dict[str, float] = self._get_items_stats(items)
        hero_catalog: list[dict[str, Any]] = self.hero_stats_catalog.as_list()
        hero_data: dict[str, Any] = hero_catalog[hero_id - 1] # -1 из-за формата /gsi_processor/local_data/heroStats.json

        stats: dict[str, int] = {
            "strength" : hero_data.get("base_str") + hero_data.get("str_gain") * level + items_stats.get("bonus_strength", 0.0),
            "agility" : hero_data.get("base_agi") + hero_data.get("agi_gain") * level + items_stats.get("bonus_agility", 0.0),
            "intellect" : hero_data.get("base_int") + hero_data.get("int_gain") * level + items_stats.get("bonus_intellect", 0.0)
        }

        return stats


    def _get_net_worth(self, gold: int, items: dict[str, Item]) -> int:
        total = gold
        for item in items.values():
            total += self.items_catalog.get(item.name, {}).get("cost", 0)
        return total


    def _get_bool_items(self, items: dict[str, Item]) -> list[bool]:
        """
        Проверяем какие сейв итемы есть у игрока
        """
        save_items: list[str] = [
                    "item_black_king_bar",
                    "item_blink",
                    "item_force_staff",
                    "item_basher",
                    "item_abyssal_blade",
                    "item_nullifier",
                    "item_lotus_orb",
                    "item_travel_boots",
                    "item_tpscroll",
                    "item_phase_boots",
                    "item_silver_edge",
                    "item_heart",
                    "item_sphere",
                    "item_manta",
                    "item_blade_mail",
                    "item_aeon_disk",
                    "item_pipe",
                ]

        hero_items: set[str] = set([item.name for item in items.values()])
        return [item in hero_items for item in save_items]


    def _is_radiant(self, team: str) -> bool:
        return team == "radiant"


    def _get_cell_id(self, x: int, y: int) -> int:
        """
        Считаем id ячейки на карте начиная от 0 в левом нижнем углу до 1023 в правом верхнем, при CELLS=32
        Идем итеративно сначала вправо, потом вверх, потом вправо и так далее, пока не дойдем до правого верхнего угла
        """
        
        XMIN, XMAX, YMIN, YMAX, CELLS = settings.XMIN, settings.XMAX, settings.YMIN, settings.YMAX, settings.CELLS

        return int((y - YMIN) / (YMAX - YMIN) * CELLS) * CELLS + int((x - XMIN) / (XMAX - XMIN) * CELLS)