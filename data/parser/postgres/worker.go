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

// Вспомогательная структура для хранения "кандидатов" на сохранение
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
	// 1. Определяем безопасные границы длины массивов, чтобы не было паники (index out of range)
	maxTicks := len(fm.General)
	if len(fm.VisionDire) < maxTicks {
		maxTicks = len(fm.VisionDire)
	}
	if len(fm.VisionRadiant) < maxTicks {
		maxTicks = len(fm.VisionRadiant)
	}

	// Карта: какие тики для каких героев мы решили сохранить
	// saveMap[tickIndex][heroName] = true
	saveMap := make(map[int]map[string]bool)
	for i := 0; i < maxTicks; i++ {
		saveMap[i] = make(map[string]bool)
	}

	// 2. Находим все уникальные имена героев в матче
	var heroes []string
	for i := 0; i < maxTicks; i++ {
		if fm.General[i].GameTime >= 0 {
			for _, h := range fm.General[i].Heroes {
				heroes = append(heroes, h.HeroName)
			}
			break // Нам нужен только один тик, чтобы собрать всех 10 героев
		}
	}

	var safeCandidates []Candidate

	// Замыкание для выбора одной случайной строки из массива тиков
	pickOneRandomTick := func(ticks []int, hero string) {
		if len(ticks) > 0 {
			randomIdx := rand.Intn(len(ticks))
			saveMap[ticks[randomIdx]][hero] = true
		}
	}

	// 3. ПЕРВЫЙ ПРОХОД: Анализируем окна смертей и собираем кандидатов
	for _, heroName := range heroes {
		// Эксклюзивные "корзины" для каждого этапа приближения смерти
		var ticks20, ticks15, ticks10, ticks5, ticks1 []int
		wasDying := false

		for i := 0; i < maxTicks; i++ {
			genState := fm.General[i]
			if genState.GameTime < 0 {
				continue
			}

			// Ищем нашего героя в текущем тике
			heroFound := false
			var isDead1s, isDead5s, isDead10s, isDead15s, isDead20s bool

			for _, h := range genState.Heroes {
				if h.HeroName == heroName {
					isDead1s = (h.IsDead1s == 1)
					isDead5s = (h.IsDead5s == 1)
					isDead10s = (h.IsDead10s == 1)
					isDead15s = (h.IsDead15s == 1)
					isDead20s = (h.IsDead20s == 1)
					heroFound = true
					break
				}
			}

			if !heroFound {
				continue
			}

			// Герой находится в процессе "умирания"
			willDie := isDead1s || isDead5s || isDead10s || isDead15s || isDead20s

			if willDie {
				wasDying = true

				// Распределяем тик по эксклюзивным корзинам (от самой близкой смерти к дальней).
				// Конструкция else if гарантирует, что тик попадет только в одну категорию.
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
				// Если флаг упал, значит герой только что умер (или это спокойное время)
				if wasDying {
					// Выбираем ровно по 1 рандомной строке из каждого окна
					pickOneRandomTick(ticks20, heroName)
					pickOneRandomTick(ticks15, heroName)
					pickOneRandomTick(ticks10, heroName)
					pickOneRandomTick(ticks5, heroName)
					pickOneRandomTick(ticks1, heroName)

					// Очищаем корзины для следующей смерти этого же героя
					ticks20, ticks15, ticks10, ticks5, ticks1 = nil, nil, nil, nil, nil
					wasDying = false
				}

				// Если герою вообще ничего не угрожает, добавляем в список безопасных кандидатов
				safeCandidates = append(safeCandidates, Candidate{TickIndex: i, HeroName: heroName})
			}
		}

		// Обработка последнего окна, если игра закончилась прямо во время смерти героя
		if wasDying {
			pickOneRandomTick(ticks20, heroName)
			pickOneRandomTick(ticks15, heroName)
			pickOneRandomTick(ticks10, heroName)
			pickOneRandomTick(ticks5, heroName)
			pickOneRandomTick(ticks1, heroName)
		}
	}

	// 4. Выбираем ровно 50 рандомных "живых" состояний со всего матча
	rand.Shuffle(len(safeCandidates), func(i, j int) {
		safeCandidates[i], safeCandidates[j] = safeCandidates[j], safeCandidates[i]
	})
	safeLimit := 50
	if len(safeCandidates) < 50 {
		safeLimit = len(safeCandidates)
	}
	for k := 0; k < safeLimit; k++ {
		c := safeCandidates[k]
		saveMap[c.TickIndex][c.HeroName] = true
	}

	// 5. ВТОРОЙ ПРОХОД: Сохранение в БД
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

	for i := 0; i < maxTicks; i++ {
		genState := fm.General[i]
		if genState.GameTime < 0 {
			continue
		}

		for _, hero := range genState.Heroes {
			if !saveMap[i][hero.HeroName] {
				continue
			}

			var sourceArray []utils.UnitVisionData
			if hero.IsRadiant == 1 {
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

			_, err = stmt.Exec(
				0, genState.MatchID, int(genState.GameTime), genState.IsDaytime, hero.IsRadiant, genState.RadiantScore, genState.DireScore,
				hero.HeroID, hero.Level, hero.Kills, hero.Deaths, hero.Assists, hero.LastHits, hero.Denies,
				hero.Gold, hero.Networth, int(hero.X), int(hero.Y), int(hero.Square), int(hero.XP), int(hero.Health), int(hero.Mana), int(hero.MaxHealth), int(hero.MaxMana),
				int(hero.Agility), int(hero.Intellect), int(hero.Strength), int(hero.MagicResist), int(hero.Armor), int(hero.MoveSpeed), int(hero.BKBcooldown),
				hero.Ability1Level, int(hero.Ability1CastRange), int(hero.Ability1ManaCost), int(hero.Ability1Cooldown),
				hero.Ability2Level, int(hero.Ability2CastRange), int(hero.Ability2ManaCost), int(hero.Ability2Cooldown),
				hero.Ability3Level, int(hero.Ability3CastRange), int(hero.Ability3ManaCost), int(hero.Ability3Cooldown),
				hero.Ability4Level, int(hero.Ability4CastRange), int(hero.Ability4ManaCost), int(hero.Ability4Cooldown),
				int(vData.NearestAllyTowerDistance), int(vData.NearestEnemyTowerDistance),
				vData.Enemy1Name, int(vData.Enemy1LastSeenX), int(vData.Enemy1LastSeenY), vData.Enemy1LastSeenSq, int(vData.Enemy1LastSeenDist), int(vData.Enemy1LastSeenTime),
				vData.Enemy2Name, int(vData.Enemy2LastSeenX), int(vData.Enemy2LastSeenY), vData.Enemy2LastSeenSq, int(vData.Enemy2LastSeenDist), int(vData.Enemy2LastSeenTime),
				vData.Enemy3Name, int(vData.Enemy3LastSeenX), int(vData.Enemy3LastSeenY), vData.Enemy3LastSeenSq, int(vData.Enemy3LastSeenDist), int(vData.Enemy3LastSeenTime),
				vData.Enemy4Name, int(vData.Enemy4LastSeenX), int(vData.Enemy4LastSeenY), vData.Enemy4LastSeenSq, int(vData.Enemy4LastSeenDist), int(vData.Enemy4LastSeenTime),
				vData.Enemy5Name, int(vData.Enemy5LastSeenX), int(vData.Enemy5LastSeenY), vData.Enemy5LastSeenSq, int(vData.Enemy5LastSeenDist), int(vData.Enemy5LastSeenTime),
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
