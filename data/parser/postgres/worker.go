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

type Candidate struct {
	TickIndex int
	HeroName  string
}

func SaveWorker(db *sql.DB, dbChan <-chan FullMatch, done chan<- bool) {
	for match := range dbChan {
		err := saveMatch(db, match)
		if err != nil {
			log.Printf("ERROR: Ошибка сохранения матча %d: %v", match.MatchId, err)
		} else {
			log.Printf("SUCCESS: Матч %d успешно сохранен", match.MatchId)
		}
	}
	done <- true
}

func saveMatch(db *sql.DB, fm FullMatch) error {
	maxTicks := len(fm.General)
	if len(fm.VisionDire) < maxTicks {
		maxTicks = len(fm.VisionDire)
	}
	if len(fm.VisionRadiant) < maxTicks {
		maxTicks = len(fm.VisionRadiant)
	}

	saveMap := make(map[int]map[string]bool)
	for i := 0; i < maxTicks; i++ {
		saveMap[i] = make(map[string]bool)
	}

	var heroes []string
	for i := 0; i < maxTicks; i++ {
		if fm.General[i].GameTime >= 0 {
			for _, h := range fm.General[i].Heroes {
				heroes = append(heroes, h.HeroName)
			}
			break
		}
	}

	var safeCandidates []Candidate
	pickOneRandomTick := func(ticks []int, hero string) {
		if len(ticks) > 0 {
			randomIdx := rand.Intn(len(ticks))
			saveMap[ticks[randomIdx]][hero] = true
		}
	}

	for _, heroName := range heroes {
		var ticks20, ticks15, ticks10, ticks5, ticks1 []int
		wasDying := false

		for i := 0; i < maxTicks; i++ {
			genState := fm.General[i]
			if genState.GameTime < 0 {
				continue
			}

			heroFound := false
			var isDead1s, isDead5s, isDead10s, isDead15s, isDead20s bool

			for _, h := range genState.Heroes {
				if h.HeroName == heroName {
					isDead1s, isDead5s, isDead10s, isDead15s, isDead20s = (h.IsDead1s == 1), (h.IsDead5s == 1), (h.IsDead10s == 1), (h.IsDead15s == 1), (h.IsDead20s == 1)
					heroFound = true
					break
				}
			}

			if !heroFound {
				continue
			}

			willDie := isDead1s || isDead5s || isDead10s || isDead15s || isDead20s

			if willDie {
				wasDying = true
				if isDead1s {
					ticks1 = append(ticks1, i)
				} else if isDead5s {
					ticks5 = append(ticks5, i)
				} else if isDead10s {
					ticks10 = append(ticks10, i)
				} else if isDead15s {
					ticks15 = append(ticks15, i)
				} else if isDead20s {
					ticks20 = append(ticks20, i)
				}
			} else {
				if wasDying {
					pickOneRandomTick(ticks20, heroName)
					pickOneRandomTick(ticks15, heroName)
					pickOneRandomTick(ticks10, heroName)
					pickOneRandomTick(ticks5, heroName)
					pickOneRandomTick(ticks1, heroName)
					ticks20, ticks15, ticks10, ticks5, ticks1 = nil, nil, nil, nil, nil
					wasDying = false
				}
				safeCandidates = append(safeCandidates, Candidate{TickIndex: i, HeroName: heroName})
			}
		}
	}

	rand.Shuffle(len(safeCandidates), func(i, j int) {
		safeCandidates[i], safeCandidates[j] = safeCandidates[j], safeCandidates[i]
	})
	for k := 0; k < 50 && k < len(safeCandidates); k++ {
		saveMap[safeCandidates[k].TickIndex][safeCandidates[k].HeroName] = true
	}

	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	query := `
    INSERT INTO dataset.match_features (
        match_id, game_time, is_day, is_radiant, radiant_score, dire_score,
        hero_id, level, kills, deaths, assists, last_hits, denies,
        gold, net_worth, x, y, square, xp, health, mana, max_health, max_mana,
        agility, intellect, strength, magical_resistance, armor, movespeed, bkb_cooldown,
        ability1_level, ability1_castrange, ability1_manacost, ability1_cooldown,
        ability2_level, ability2_castrange, ability2_manacost, ability2_cooldown,
        ability3_level, ability3_castrange, ability3_manacost, ability3_cooldown,
        ability4_level, ability4_castrange, ability4_manacost, ability4_cooldown,
        nearest_ally_tower_distance, nearest_enemy_tower_distance,
        slot_1_id, enemy_1_name, enemy_1_last_seen_x, enemy_1_last_seen_y, enemy_1_last_seen_sqare, enemy_1_last_seen_distance, enemy_1_last_seen_time,
        slot_2_id, enemy_2_name, enemy_2_last_seen_x, enemy_2_last_seen_y, enemy_2_last_seen_sqare, enemy_2_last_seen_distance, enemy_2_last_seen_time,
        slot_3_id, enemy_3_name, enemy_3_last_seen_x, enemy_3_last_seen_y, enemy_3_last_seen_sqare, enemy_3_last_seen_distance, enemy_3_last_seen_time,
        slot_4_id, enemy_4_name, enemy_4_last_seen_x, enemy_4_last_seen_y, enemy_4_last_seen_sqare, enemy_4_last_seen_distance, enemy_4_last_seen_time,
        slot_5_id, enemy_5_name, enemy_5_last_seen_x, enemy_5_last_seen_y, enemy_5_last_seen_sqare, enemy_5_last_seen_distance, enemy_5_last_seen_time,
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
        $101, $102, $103, $104, $105
    )`

	stmt, err := tx.Prepare(query)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 0; i < maxTicks; i++ {
		genState := fm.General[i]
		for _, hero := range genState.Heroes {
			if !saveMap[i][hero.HeroName] {
				continue
			}

			// Определяем источник данных обзора
			var sourceArray []utils.UnitVisionData
			if hero.IsRadiant != 1 {
				sourceArray = fm.VisionDire[i].Unit
			} else {
				sourceArray = fm.VisionRadiant[i].Unit
			}

			var vData utils.UnitVisionData
			targetName := utils.NormalizeName(hero.HeroName)
			for _, u := range sourceArray {
				if u.Name == targetName {
					vData = u
					break
				}
			}

			// ЛОГИКА ПРИВЯЗКИ К СЛОТАМ
			// Создаем контейнер для 5 врагов
			type Enemy struct {
				ID             int
				Name           string
				X, Y, Sq, Time int
				Dist           float32
			}
			slots := make(map[int]Enemy)

			// Проходим по всем героям в тике, чтобы найти врагов и их TeamSlot
			for _, h := range genState.Heroes {
				if h.IsRadiant != hero.IsRadiant { // что тут такое?
					ts := (h.TeamSlot % 5) + 1 // Получаем 1, 2, 3, 4 или 5

					// По умолчанию слот пустой, но если в vData есть данные для этого имени - берем их
					e := Enemy{ID: ts, Name: h.HeroName}

					if h.HeroName == vData.Enemy1Name {
						e.X, e.Y, e.Sq, e.Dist, e.Time = int(vData.Enemy1LastSeenX), int(vData.Enemy1LastSeenY), vData.Enemy1LastSeenSq, vData.Enemy1LastSeenDist, int(vData.Enemy1LastSeenTime)
					} else if h.HeroName == vData.Enemy2Name {
						e.X, e.Y, e.Sq, e.Dist, e.Time = int(vData.Enemy2LastSeenX), int(vData.Enemy2LastSeenY), vData.Enemy2LastSeenSq, vData.Enemy2LastSeenDist, int(vData.Enemy2LastSeenTime)
					} else if h.HeroName == vData.Enemy3Name {
						e.X, e.Y, e.Sq, e.Dist, e.Time = int(vData.Enemy3LastSeenX), int(vData.Enemy3LastSeenY), vData.Enemy3LastSeenSq, vData.Enemy3LastSeenDist, int(vData.Enemy3LastSeenTime)
					} else if h.HeroName == vData.Enemy4Name {
						e.X, e.Y, e.Sq, e.Dist, e.Time = int(vData.Enemy4LastSeenX), int(vData.Enemy4LastSeenY), vData.Enemy4LastSeenSq, vData.Enemy4LastSeenDist, int(vData.Enemy4LastSeenTime)
					} else if h.HeroName == vData.Enemy5Name {
						e.X, e.Y, e.Sq, e.Dist, e.Time = int(vData.Enemy5LastSeenX), int(vData.Enemy5LastSeenY), vData.Enemy5LastSeenSq, vData.Enemy5LastSeenDist, int(vData.Enemy5LastSeenTime)
					}
					slots[ts] = e
				}
			}

			_, err = stmt.Exec(
				genState.MatchID, int(genState.GameTime), genState.IsDaytime, hero.IsRadiant, genState.RadiantScore, genState.DireScore,
				hero.HeroID, hero.Level, hero.Kills, hero.Deaths, hero.Assists, hero.LastHits, hero.Denies,
				hero.Gold, hero.Networth, int(hero.X), int(hero.Y), int(hero.Square), int(hero.XP), int(hero.Health), int(hero.Mana), int(hero.MaxHealth), int(hero.MaxMana),
				int(hero.Agility), int(hero.Intellect), int(hero.Strength), int(hero.MagicResist), int(hero.Armor), int(hero.MoveSpeed), int(hero.BKBcooldown),
				hero.Ability1Level, int(hero.Ability1CastRange), int(hero.Ability1ManaCost), int(hero.Ability1Cooldown),
				hero.Ability2Level, int(hero.Ability2CastRange), int(hero.Ability2ManaCost), int(hero.Ability2Cooldown),
				hero.Ability3Level, int(hero.Ability3CastRange), int(hero.Ability3ManaCost), int(hero.Ability3Cooldown),
				hero.Ability4Level, int(hero.Ability4CastRange), int(hero.Ability4ManaCost), int(hero.Ability4Cooldown),
				int(vData.NearestAllyTowerDistance), int(vData.NearestEnemyTowerDistance),

				slots[1].ID, slots[1].Name, slots[1].X, slots[1].Y, slots[1].Sq, int(slots[1].Dist), slots[1].Time,
				slots[2].ID, slots[2].Name, slots[2].X, slots[2].Y, slots[2].Sq, int(slots[2].Dist), slots[2].Time,
				slots[3].ID, slots[3].Name, slots[3].X, slots[3].Y, slots[3].Sq, int(slots[3].Dist), slots[3].Time,
				slots[4].ID, slots[4].Name, slots[4].X, slots[4].Y, slots[4].Sq, int(slots[4].Dist), slots[4].Time,
				slots[5].ID, slots[5].Name, slots[5].X, slots[5].Y, slots[5].Sq, int(slots[5].Dist), slots[5].Time,

				hero.ItemBlackKingBar, hero.ItemBlink, hero.ItemForceStaff, hero.ItemBasher, hero.ItemAbyssalBlade,
				hero.ItemNullifier, hero.ItemLotusOrb, hero.ItemTravelBoots, hero.ItemTpscroll, hero.ItemPhaseBoots,
				hero.ItemSilverEdge, hero.ItemHeart, hero.ItemSphere, hero.ItemManta, hero.ItemBladeMail, hero.ItemAeonDisk, hero.ItemPipe,
				hero.IsDead1s, hero.IsDead5s, hero.IsDead10s, hero.IsDead15s, hero.IsDead20s,
			)

			if err != nil {
				return err
			}
		}
	}

	return tx.Commit()
}
