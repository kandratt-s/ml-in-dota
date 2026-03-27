package postgres

import (
	"database/sql"
	"log"
	"math/rand"

	"github.com/kandratt-s/ml-in-dota.git/data/parsed/utils"
)

type FullMatch struct {
	MatchId       int64
	General       []utils.GeneralGameState
	VisionDire    []utils.VisionEnemeyTeam
	VisionRadiant []utils.VisionEnemeyTeam
}

const (
	GridXMin  float32 = -9400.0
	GridXMax  float32 = 8000.0
	GridYMin  float32 = -8500.0
	GridYMax  float32 = 8500.0
	GridCells int     = 32

	NegativeSampleRate float64 = 0.1
)

func SaveWorker(db *sql.DB, dbChan <-chan FullMatch, done chan<- bool) {
	for match := range dbChan {
		err := saveMatch(db, match)
		if err != nil {
			log.Printf("ERROR: Ошибка сохранения матча %d: %v", match.MatchId, err)
		} else {
			log.Printf("SUCCESS: Матч %d успешно сохранен (%d тиков)", match.MatchId, len(match.General))
		}
	}
	done <- true
}

func shouldSampleNegative() bool {
	return rand.Float64() < NegativeSampleRate
}

func saveMatch(db *sql.DB, fm FullMatch) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	query := `
    INSERT INTO dataset.match_features (
        account_id, match_id, game_time, is_day, is_radiant, radiant_score, dire_score,
        hero_id, level, kills, deaths, assists, last_hits, denies,
        gold, net_worth, x, y, square, xp, health, mana, max_health, max_mana,
        agility, intellect, strength, magical_resistance, armor, movespeed, bkb_cooldown,

        ability1_level, ability1_castrange, ability1_manacost, ability1_cooldown,
        ability2_level, ability2_castrange, ability2_manacost, ability2_cooldown,
        ability3_level, ability3_castrange, ability3_manacost, ability3_cooldown,
        ability4_level, ability4_castrange, ability4_manacost, ability4_cooldown,

        nearest_ally_tower_distance, nearest_enemy_tower_distance,

        enemy_1_name, enemy_1_last_seen_x, enemy_1_last_seen_y, enemy_1_last_seen_sqare, enemy_1_last_seen_distance, enemy_1_last_seen_time,
        enemy_2_name, enemy_2_last_seen_x, enemy_2_last_seen_y, enemy_2_last_seen_sqare, enemy_2_last_seen_distance, enemy_2_last_seen_time,
        enemy_3_name, enemy_3_last_seen_x, enemy_3_last_seen_y, enemy_3_last_seen_sqare, enemy_3_last_seen_distance, enemy_3_last_seen_time,
        enemy_4_name, enemy_4_last_seen_x, enemy_4_last_seen_y, enemy_4_last_seen_sqare, enemy_4_last_seen_distance, enemy_4_last_seen_time,
        enemy_5_name, enemy_5_last_seen_x, enemy_5_last_seen_y, enemy_5_last_seen_sqare, enemy_5_last_seen_distance, enemy_5_last_seen_time,

        item_black_king_bar, item_blink, item_force_staff, item_basher, item_abyssal_blade,
        item_nullifier, item_lotus_orb, item_travel_boots, item_tpscroll, item_phase_boots,
        item_silver_edge, item_heart, item_sphere, item_manta, item_blade_mail, item_aeon_disk, item_pipe,

        dead_in_1, dead_in_5, dead_in_10, dead_in_15, dead_in_20
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
        $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39, $40,
        $41, $42, $43, $44, $45, $46, $47, $48, $49, $50, $51, $52, $53, $54, $55, $56, $57, $58, $59, $60,
        $61, $62, $63, $64, $65, $66, $67, $68, $69, $70, $71, $72, $73, $74, $75, $76, $77, $78, $79, $80,
        $81, $82, $83, $84, $85, $86, $87, $88, $89, $90, $91, $92, $93, $94, $95, $96, $97, $98, $99, $100,
        $101
    )`

	stmt, err := tx.Prepare(query)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i, genState := range fm.General {

		if i >= len(fm.VisionRadiant) || i >= len(fm.VisionDire) {
			continue
		}

		for _, hero := range genState.Heroes {

			willDie := hero.IsDead1s || hero.IsDead5s || hero.IsDead10s || hero.IsDead15s || hero.IsDead20s

			if !willDie && !shouldSampleNegative() {
				continue
			}

			var sourceArray []utils.UnitVisionData

			if hero.IsRadiant {
				sourceArray = fm.VisionDire[i].Unit
			} else {
				sourceArray = fm.VisionRadiant[i].Unit
			}

			var vData utils.UnitVisionData
			found := false
			targetName := utils.NormalizeName(hero.HeroName)

			for _, u := range sourceArray {
				if u.Name == targetName {
					vData = u
					found = true
					break
				}
			}

			if !found {
			}

			_, err = stmt.Exec(
				// (7)
				0, genState.MatchID, genState.GameTime, genState.IsDaytime, hero.IsRadiant, genState.RadiantScore, genState.DireScore,

				// (22)
				hero.HeroID, hero.Level, hero.Kills, hero.Deaths, hero.Assists, hero.LastHits, hero.Denies,
				hero.Gold, hero.Networth, hero.X, hero.Y, utils.GetGridID(hero.X, hero.Y), hero.XP, int(hero.Health), int(hero.Mana), int(hero.MaxHealth), int(hero.MaxMana),
				hero.Agility, hero.Intellect, hero.Strength, hero.MagicResist, hero.Armor, hero.MoveSpeed, hero.BKBcooldown,

				// (16)
				hero.Ability1Level, hero.Ability1CastRange, hero.Ability1ManaCost, hero.Ability1Cooldown,
				hero.Ability2Level, hero.Ability2CastRange, hero.Ability2ManaCost, hero.Ability2Cooldown,
				hero.Ability3Level, hero.Ability3CastRange, hero.Ability3ManaCost, hero.Ability3Cooldown,
				hero.Ability4Level, hero.Ability4CastRange, hero.Ability4ManaCost, hero.Ability4Cooldown,

				// (2)
				vData.NearestAllyTowerDistance,
				vData.NearestEnemyTowerDistance,

				// (30)
				vData.Enemy1Name, vData.Enemy1LastSeenX, vData.Enemy1LastSeenY, vData.Enemy1LastSeenSq, vData.Enemy1LastSeenDist, vData.Enemy1LastSeenTime,
				vData.Enemy2Name, vData.Enemy2LastSeenX, vData.Enemy2LastSeenY, vData.Enemy2LastSeenSq, vData.Enemy2LastSeenDist, vData.Enemy2LastSeenTime,
				vData.Enemy3Name, vData.Enemy3LastSeenX, vData.Enemy3LastSeenY, vData.Enemy3LastSeenSq, vData.Enemy3LastSeenDist, vData.Enemy3LastSeenTime,
				vData.Enemy4Name, vData.Enemy4LastSeenX, vData.Enemy4LastSeenY, vData.Enemy4LastSeenSq, vData.Enemy4LastSeenDist, vData.Enemy4LastSeenTime,
				vData.Enemy5Name, vData.Enemy5LastSeenX, vData.Enemy5LastSeenY, vData.Enemy5LastSeenSq, vData.Enemy5LastSeenDist, vData.Enemy5LastSeenTime,

				// (17)
				hero.ItemBlackKingBar, hero.ItemBlink, hero.ItemForceStaff, hero.ItemBasher, hero.ItemAbyssalBlade,
				hero.ItemNullifier, hero.ItemLotusOrb, hero.ItemTravelBoots, hero.ItemTpscroll, hero.ItemPhaseBoots,
				hero.ItemSilverEdge, hero.ItemHeart, hero.ItemSphere, hero.ItemManta, hero.ItemBladeMail, hero.ItemAeonDisk, hero.ItemPipe,

				// (5)
				hero.IsDead1s, hero.IsDead5s, hero.IsDead10s, hero.IsDead15s, hero.IsDead20s,
			)

			if err != nil {
				return err
			}
		}
	}

	return tx.Commit()
}
