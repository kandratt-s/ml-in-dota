from typing import Any

from scr.schemas.dota_input import Ability, GSIRequest, Item, MinimapObject
from scr.infra.redis import EnemyStateRepository, ActiveTokensRepository, InferenceQueueRepository, SnapshotStateRepository
from scr.infra.config import settings
from scr.infra.catalog import JsonCatalog
from scr.schemas.dota_output import EnemySnapshot, GameStateRequest, HeroStatsSnapshot, CalculatedFeatures, AbilitySnapshot
from scr.infra.formulas import cell_id, euclidean_distance
from scr.schemas.inference_queue import InferenceRecord
from scr.schemas.snapshot import EnemyPositionSnapshot, SnapshotState

import json
from pathlib import Path

class GSIProcessorService:
    def __init__(
        self,
        abilities_catalog: JsonCatalog,
        hero_stats_catalog: JsonCatalog,
        items_catalog: JsonCatalog,
        enemy_state_repo: EnemyStateRepository,
        active_token_repo: ActiveTokensRepository,
        inference_queue_repo: InferenceQueueRepository,
        snapshot_state_repo: SnapshotStateRepository,
    ) -> None:
        self.abilities_catalog = abilities_catalog
        self.hero_stats_catalog = hero_stats_catalog
        self.items_catalog = items_catalog
        self.enemy_state_repo = enemy_state_repo
        self.active_token_repo = active_token_repo
        self.inference_queue_repo = inference_queue_repo
        self.snapshot_state_repo = snapshot_state_repo

    async def process_gsi_data(self, data: GSIRequest) -> GameStateRequest:
        token = data.auth.token
        if not await self.active_token_repo.is_active(token):
            raise PermissionError("Token is not active")

        # Load previous snapshot (n-1) for comparison with current state (n)
        previous_snapshot = await self.snapshot_state_repo.get_previous_snapshot(token)

        is_radiant = self._is_radiant(data.player.team_name)
        x = data.hero.xpos
        y = data.hero.ypos

        hero_stats = self._get_character_stats(data.hero.id, data.hero.level, data.items)
        abilities = self._get_abilities_stats(data.abilities)
        enemies = await self.build_enemy_snapshots(
            token=token,
            minimap_info=data.minimap,
            is_radiant=is_radiant,
            hero_x=x,
            hero_y=y,
            previous_snapshot=previous_snapshot,
        )

        nearest_ally_tower_distance, nearest_enemy_tower_distance = self._get_nearest_towers_distance(
            minimap_info=data.minimap,
            is_radiant=is_radiant,
            x=x,
            y=y,
        )

        features = CalculatedFeatures(
            hero=HeroStatsSnapshot(**hero_stats),
            magical_resistance=self._get_magical_resistance(hero_stats["intellect"], data.items),
            armor=self._get_armor(data.hero.id, hero_stats["agility"], data.items),
            movespeed=self._get_move_speed(data.hero.id, data.items),
            bkb_cooldown=self._get_bkb_cooldown(data.items),
            net_worth=self._get_net_worth(data.player.gold, data.items),
            nearest_ally_tower_distance=nearest_ally_tower_distance,
            nearest_enemy_tower_distance=nearest_enemy_tower_distance,
            abilities=abilities,
            enemies=enemies,
            save_items=self._get_bool_items(data.items),
        )

        # TODO: Add delta/comparison features based on previous_snapshot
        # previous_snapshot contains the (n-1) state for this token
        # Use it to compute features that require state comparison:
        # - Position delta (movement distance, direction)
        # - Health/mana changes
        # - Level/gold changes
        # - Item/ability changes
        # - Enemy distance changes
        # Example:
        #   if previous_snapshot:
        #       prev_x = previous_snapshot.get("x")
        #       prev_y = previous_snapshot.get("y")
        #       movement_distance = euclidean_distance(x, y, prev_x, prev_y)
        #       # Add computed delta features to payload below
        delta_features = await self._compute_delta_features(
            current_state=data,
            current_features=features,
            previous_snapshot=previous_snapshot,
            token=token,
        )

        # в плоскость для модели
        payload: dict[str, Any] = {
            "account_id": data.player.accountid,
            "match_id": data.map.matchid,
            "game_time": data.map.game_time,
            "is_day": data.map.daytime,
            "is_radiant": is_radiant,
            "radiant_score": data.map.radiant_score,
            "dire_score": data.map.dire_score,
            "hero_id": data.hero.id,
            "level": data.hero.level,
            "kills": data.player.kills,
            "deaths": data.player.deaths,
            "assists": data.player.assists,
            "last_hits": data.player.last_hits,
            "denies": data.player.denies,
            "gold": data.player.gold,
            "net_worth": features.net_worth,
            "x": x,
            "y": y,
            "square": cell_id(x, y),
            "xp": data.hero.xp,
            "health": data.hero.health,
            "mana": data.hero.mana,
            "max_health": data.hero.max_health,
            "max_mana": data.hero.max_mana,
            "agility": features.hero.agility,
            "intellect": features.hero.intellect,
            "strength": features.hero.strength,
            "magical_resistance": features.magical_resistance,
            "armor": features.armor,
            "bkb_cooldown": features.bkb_cooldown,
            "movespeed": features.movespeed,
            "nearest_ally_tower_distance": features.nearest_ally_tower_distance,
            "nearest_enemy_tower_distance": features.nearest_enemy_tower_distance,
        }

        payload.update(self._pack_abilities(features.abilities))
        payload.update(self._pack_enemies(features.enemies))
        payload.update(self._pack_items(features.save_items))
        # Include delta features computed from previous snapshot
        #payload.update(delta_features)

        game_state = GameStateRequest.model_validate(payload)

        record_id = f"{payload['match_id']}:{payload['account_id']}:{game_state.game_time}"
        await self.inference_queue_repo.enqueue_request(
            InferenceRecord(record_id=record_id, payload=game_state.model_dump(mode="json"))
        )

        # Save current state as snapshot for next GSI event (becomes n-1)
        # Store only enemy positions keyed by hero name
        enemies_dict: dict[str, EnemyPositionSnapshot] = {
            str(enemy.name): EnemyPositionSnapshot(
                enemy_last_seen_time=enemy.time,
                enemy_last_seen_x=enemy.x,
                enemy_last_seen_y=enemy.y,
            )
            for enemy in features.enemies
            if enemy.name
        }
        current_snapshot = SnapshotState(enemies=enemies_dict)
        await self.snapshot_state_repo.save_current_snapshot(token, current_snapshot)

        return game_state

    def _pack_abilities(self, abilities: list[AbilitySnapshot]) -> dict[str, int]:
        payload: dict[str, int] = {}
        for idx, ability in enumerate(abilities[:4]):
            payload[f"ability{idx}_level"] = ability.level
            payload[f"ability{idx}_castrange"] = ability.cast_range
            payload[f"ability{idx}_manacost"] = ability.mana_cost
            payload[f"ability{idx}_cooldown"] = ability.cooldown
        return payload

    def _pack_enemies(self, enemies: list[EnemySnapshot]) -> dict[str, int]:
        payload: dict[str, int] = {}
        for idx, enemy in enumerate(enemies[:5], start=1):
            payload[f"enemy_{idx}_last_seen_x"] = enemy.x
            payload[f"enemy_{idx}_last_seen_y"] = enemy.y
            payload[f"enemy_{idx}_last_seen_sqare"] = enemy.square
            payload[f"enemy_{idx}_last_seen_distance"] = enemy.distance
            payload[f"enemy_{idx}_last_seen_time"] = enemy.time
        return payload

    def _pack_items(self, save_items: list[bool]) -> dict[str, bool]:
        item_keys = [
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
        return {key: save_items[idx] for idx, key in enumerate(item_keys)}

    async def _compute_delta_features(
        self,
        current_state: GSIRequest,
        current_features: CalculatedFeatures,
        previous_snapshot: SnapshotState | None,
        token: str,
    ) -> dict[str, Any]:
        """
        Compute features that require comparison with previous snapshot.
        
        This method computes delta/change-based features by comparing the current
        GSI state (n) with the previous snapshot (n-1) stored in Redis.
        
        Args:
            current_state: Current GSI data (n)
            current_features: Computed features for current state
            previous_snapshot: Previous state snapshot (n-1) or None if first event
            token: Player session token
            
        Returns:
            Dictionary of delta features to add to the payload
            
        TODO: Fill in the logic for computing delta features
        Examples:
            - Movement speed (distance traveled in time delta)
            - Health/mana changes
            - Level/gold/XP gains
            - Kill/death/assist changes
            - Item purchases/removals
            - Ability cooldown changes
            - Enemy position changes
            - Combat engagement (health loss, item usage)
        """
        delta_features: dict[str, Any] = {}
        
        if previous_snapshot is None:
            # First event - no previous state to compare
            # TODO: Set sensible defaults for first event (all deltas = 0)
            pass
        else:

            

            # TODO: Implement delta feature computation
            # Note: previous_snapshot only contains enemy position data (enemies: dict[int, EnemyPositionSnapshot])
            # Can compute features for enemy position changes:
            # Example structure:
            # prev_enemies = previous_snapshot.enemies  # dict[int, EnemyPositionSnapshot]
            # current_enemies = current_features.enemies  # list[EnemySnapshot]
            # 
            # for enemy_id, prev_enemy_data in prev_enemies.items():
            #     if enemy_id < len(current_enemies):
            #         curr_enemy = current_enemies[enemy_id]
            #         enemy_position_change = euclidean_distance(
            #             curr_enemy.x, curr_enemy.y,
            #             prev_enemy_data.enemy_last_seen_x, prev_enemy_data.enemy_last_seen_y
            #         )
            #         delta_features[f"enemy_{enemy_id}_position_change"] = enemy_position_change
            # 
            # ... add more delta features based on current state comparisons
            pass
        
        return delta_features

    def _get_abilities_stats(self, abilities: dict[str, Ability]) -> list[AbilitySnapshot]:
        abilities_catalog: dict[str, dict[str, Any]] = self.abilities_catalog.as_dict()
        result: list[AbilitySnapshot] = []

        for i in range(4):
            ability = abilities.get(f"ability{i}", Ability(name="", level=0, cooldown=0))
            ability_data = abilities_catalog.get(ability.name, {})
            cast_range = self._extract_cast_range(ability_data)
            mana_cost = self._extract_mana_cost(ability_data, ability.level)

            result.append(
                AbilitySnapshot(
                    level=ability.level,
                    cast_range=cast_range,
                    mana_cost=mana_cost,
                    cooldown=ability.cooldown,
                )
            )

        return result

    def _extract_cast_range(self, ability_data: dict[str, Any]) -> int:
        attributes: dict[int, dict[str, Any]] = ability_data.get("attributes", {})
        for attr in attributes.values():
            key = str(attr.get("key", "")).lower()
            header = str(attr.get("header", "")).lower()
            if "range" in key or "range" in header:
                return int(attr.get("value", 0))
        return 0

    def _extract_mana_cost(self, ability_data: dict[str, Any], ability_level: int) -> int:
        mc = ability_data.get("mc", [])
        if isinstance(mc, str):
            try:
                return int(mc)
            except ValueError:
                return 0

        if isinstance(mc, list) and ability_level > 0:
            idx = ability_level - 1
            if 0 <= idx < len(mc):
                try:
                    return int(mc[idx])
                except (TypeError, ValueError):
                    return 0
        return 0

    def _get_nearest_towers_distance(
        self,
        minimap_info: dict[int, MinimapObject],
        is_radiant: bool,
        x: int,
        y: int,
    ) -> tuple[int, int]:
        nearest_ally_tower_distance = 100000
        nearest_enemy_tower_distance = 100000

        for obj in minimap_info.values():
            if not(isinstance(obj.unitname, str)):
                continue

            if "npc_dota_" in obj.unitname and "tower" in obj.unitname:
                distance = euclidean_distance(x, y, obj.xpos, obj.ypos)
                if (is_radiant and obj.team == 2) or (not is_radiant and obj.team == 3):
                    nearest_ally_tower_distance = min(nearest_ally_tower_distance, distance)
                else:
                    nearest_enemy_tower_distance = min(nearest_enemy_tower_distance, distance)

        return nearest_ally_tower_distance, nearest_enemy_tower_distance

    def _get_bkb_cooldown(self, items: dict[str, Item]) -> int:
        for item in items.values():
            if item.name == "item_black_king_bar":
                return item.cooldown
        return 0

    def _get_items_stats(self, items: dict[str, Item]) -> dict[str, int]:
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()

        stat_keys = [
            "bonus_all_stats",
            "bonus_agility",
            "bonus_strength",
            "bonus_intellect",
        ]

        total_stats: dict[str, int] = {key: 0 for key in stat_keys}

        for item in items.values():
            item_data = item_catalog.get(item.name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])
            for attr in attributes:
                key = attr.get("key")
                if key in stat_keys:
                    total_stats[key] += int(attr.get("value", 0))

        all_stats_bonus = total_stats["bonus_all_stats"]
        total_stats["bonus_agility"] += all_stats_bonus
        total_stats["bonus_strength"] += all_stats_bonus
        total_stats["bonus_intellect"] += all_stats_bonus
        total_stats.pop("bonus_all_stats", None)

        return total_stats

    def _get_character_stats(self, hero_id: int, level: int, items: dict[str, Item]) -> dict[str, int]:
        items_stats = self._get_items_stats(items)
        hero_catalog: list[dict[str, Any]] = self.hero_stats_catalog.as_list()

        hero_index = hero_id - 1
        if hero_index < 0 or hero_index >= len(hero_catalog):
            return {
                "strength": items_stats.get("bonus_strength", 0),
                "agility": items_stats.get("bonus_agility", 0),
                "intellect": items_stats.get("bonus_intellect", 0),
            }

        hero_data = hero_catalog[hero_index]

        return {
            "strength": int(hero_data.get("base_str", 0) + hero_data.get("str_gain", 0) * level + items_stats.get("bonus_strength", 0)),
            "agility": int(hero_data.get("base_agi", 0) + hero_data.get("agi_gain", 0) * level + items_stats.get("bonus_agility", 0)),
            "intellect": int(hero_data.get("base_int", 0) + hero_data.get("int_gain", 0) * level + items_stats.get("bonus_intellect", 0)),
        }

    def _get_net_worth(self, gold: int, items: dict[str, Item]) -> int:
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()
        total = gold
        for item in items.values():
            total += int(item_catalog.get(item.name, {}).get("cost", 0))
        return total

    def _get_magical_resistance(self, intellect: int, items: dict[str, Item]) -> int:
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()
        resistance: float = 1 - 0.25

        for item in items.values():
            item_data = item_catalog.get(item.name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])
            for attr in attributes:
                if attr.get("key") == "magic_resistance_aura":
                    resistance *= (1 - float(attr.get("value", 0)) / 100.0)

        resistance += intellect * 0.1 / 100.0
        return int(resistance * 100)

    def _get_armor(self, hero_id: int, agility: int, items: dict[str, Item]) -> int:
        hero_catalog: list[dict[str, Any]] = self.hero_stats_catalog.as_list()
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()

        hero_index = hero_id - 1
        if hero_index < 0 or hero_index >= len(hero_catalog):
            base_armor = 0
        else:
            base_armor = int(hero_catalog[hero_index].get("base_armor", 0))

        items_armor = 0
        for item in items.values():
            item_data = item_catalog.get(item.name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])
            for attr in attributes:
                if attr.get("key") in {"aura_positive_armor", "bonus_armor"}:
                    items_armor += int(attr.get("value", 0))

        return base_armor + int(0.167 * agility) + items_armor

    def _get_move_speed(self, hero_id: int, items: dict[str, Item]) -> int:
        hero_catalog: list[dict[str, Any]] = self.hero_stats_catalog.as_list()
        item_catalog: dict[str, dict[str, Any]] = self.items_catalog.as_dict()

        hero_index = hero_id - 1
        if 0 <= hero_index < len(hero_catalog):
            base_move_speed = int(hero_catalog[hero_index].get("move_speed", 0))
        else:
            base_move_speed = 0

        boots_group = {
            "item_boots",
            "item_arcane_boots",
            "item_travel_boots",
            "item_travel_boots_2",
            "item_phase_boots",
            "item_tranquil_boots",
            "item_force_boots",
        }
        yasha_group = {
            "item_yasha",
            "item_sange_and_yasha",
            "item_manta",
            "item_yasha_and_kaya",
        }
        wind_lace_group = {"item_wind_lace"}

        boots_group_max_speed = 0
        yasha_group_max_speed = 0
        wind_lace_group_max_speed = 0
        other_items_max_speed = 0
        multiplication_coefficient = 1.0

        bonuses = {"bonus_movement_speed", "movement_speed_percent_bonus"}

        for item in items.values():
            item_name = item.name
            item_data = item_catalog.get(item_name, {})
            attributes: list[dict[str, Any]] = item_data.get("attributes", [])

            for attr in attributes:
                key = attr.get("key")
                value = int(attr.get("value", 0))

                if key not in bonuses:
                    continue

                if key == "bonus_movement_speed":
                    if item_name in boots_group:
                        boots_group_max_speed = max(boots_group_max_speed, value)
                    elif item_name in yasha_group:
                        yasha_group_max_speed = max(yasha_group_max_speed, value)
                    elif item_name in wind_lace_group:
                        wind_lace_group_max_speed = max(wind_lace_group_max_speed, value)
                    else:
                        other_items_max_speed = max(other_items_max_speed, value)
                else:
                    multiplication_coefficient += value / 100.0

        result = int(
            (base_move_speed + boots_group_max_speed + yasha_group_max_speed + wind_lace_group_max_speed + other_items_max_speed)
            * multiplication_coefficient
        )
        return min(result, 550)

    def _get_bool_items(self, items: dict[str, Item]) -> list[bool]:
        save_items = [
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
        hero_items = {item.name for item in items.values()}
        return [item in hero_items for item in save_items]

    def _is_radiant(self, team: str) -> bool:
        return team == "radiant"
    
    def _extract_visible_enemies(
        self,
        minimap_info: dict[int, MinimapObject],
        is_radiant: bool,
    ) -> dict[str, tuple[int, int]]:
        enemies: dict[str, tuple[int, int]] = {}

        for obj in minimap_info.values():
            if not(isinstance(obj.unitname, str)):
                continue

            if "npc_dota_hero_" not in obj.unitname:
                continue

            is_enemy = (is_radiant and obj.team == 3) or (not is_radiant and obj.team == 2)
            if is_enemy:
                enemies[obj.unitname] = (obj.xpos, obj.ypos)
                if len(enemies) == 5:
                    break

        return enemies

    async def build_enemy_snapshots(
        self,
        token: str,
        minimap_info: dict[int, MinimapObject],
        is_radiant: bool,
        hero_x: int,
        hero_y: int,
        previous_snapshot: SnapshotState | None = None,
    ) -> list[EnemySnapshot]:
        """
        Build enemy snapshots using n-1 (previous) snapshot to track enemy visibility.
        
        Logic:
        - If enemy is visible in minimap_info: use position from minimap, set time=0
        - If enemy is not visible but was in previous_snapshot: use previous position, increment time
        """
        visible = self._extract_visible_enemies(minimap_info, is_radiant)
        
        # Start with visible enemies (all have time=0, fresh position)
        merged_positions: dict[str, tuple[int, int]] = dict(visible)
        merged_last_seen: dict[str, int] = {enemy: 0 for enemy in visible}
        
        # Merge with previous_snapshot enemies (not currently visible)
        if previous_snapshot:
            for enemy_name, enemy_data in previous_snapshot.enemies.items():
                if enemy_name not in visible:
                    # Enemy not visible now, use previous position and increment time
                    merged_positions[enemy_name] = (enemy_data.enemy_last_seen_x, enemy_data.enemy_last_seen_y)
                    merged_last_seen[enemy_name] = enemy_data.enemy_last_seen_time + 1
        
        # Calculate distances for sorting
        distances: dict[str, int] = {
            enemy: euclidean_distance(hero_x, hero_y, coords[0], coords[1])
            for enemy, coords in merged_positions.items()
        }
        
        # Sort by distance and take 5 closest
        sorted_enemies = sorted(merged_positions.keys(), key=lambda e: distances[e])
        
        BASE_DIR = Path(__file__).resolve().parent / "heroNames.json"
        with open(BASE_DIR, "r") as f:
            hero_names = json.load(f)

        # Build EnemySnapshot list
        snapshots: list[EnemySnapshot] = []
        for enemy in sorted_enemies[:5]:
            x, y = merged_positions[enemy]
            snapshots.append(
                EnemySnapshot(
                    name=hero_names.get(enemy, 0),
                    x=x,
                    y=y,
                    square=cell_id(x, y),
                    distance=distances[enemy],
                    time=merged_last_seen.get(enemy, 0),
                )
            )
        
        # Pad to 5 enemies with empty snapshots
        while len(snapshots) < 5:
            snapshots.append(EnemySnapshot())
        
        # Update Redis state (for backward compatibility with old code if needed)
        # Avoid calling hset with empty mappings (Redis raises DataError)
        if merged_positions:
            await self.enemy_state_repo.write_enemy_positions(token, merged_positions)
        if merged_last_seen:
            await self.enemy_state_repo.write_last_seen(token, merged_last_seen)
        
        return snapshots