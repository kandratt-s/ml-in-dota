package utils

import (
	"encoding/json"
	"math"
	"os"
	"strconv"
	"strings"
)

var (
	HeroStatsMap     map[string]HeroStatsDefinition
	ItemStatsMap     map[string]ItemDefinition
	AbilityStatsMap  map[string]AbilityDefinition
	HeroAbilitiesMap map[string]HeroAbilitiesDefinition
)

var ConsumableItems = map[string]int{
	"tango": 1, "clarity": 1, "enchanted_mango": 1, "faerie_fire": 1,
	"flask": 1, "ward_observer": 1, "ward_sentry": 1, "smoke_of_deceit": 1,
	"dust": 1, "tpscroll": 1, "cheese": 1, "refresher_shard": 1, "aegis": 1,
}

const BKBTotalCooldown = 95.0

type HeroStatsDefinition struct {
	ID          int     `json:"id"`
	Name        string  `json:"name"`
	PrimaryAttr string  `json:"primary_attr"`
	BaseHealth  float32 `json:"base_health"`
	BaseMana    float32 `json:"base_mana"`
	BaseArmor   float32 `json:"base_armor"`
	BaseMr      int     `json:"base_mr"`
	BaseStr     int     `json:"base_str"`
	BaseAgi     int     `json:"base_agi"`
	BaseInt     int     `json:"base_int"`
	StrGain     float32 `json:"str_gain"`
	AgiGain     float32 `json:"agi_gain"`
	IntGain     float32 `json:"int_gain"`
	MoveSpeed   int     `json:"move_speed"`
}

type HeroAbilitiesDefinition struct {
	Abilities []string `json:"abilities"`
}

type ItemAttribute struct {
	Key   string      `json:"key"`
	Value interface{} `json:"value"`
}

type ItemDefinition struct {
	ID     int             `json:"id"`
	Dname  string          `json:"dname"`
	Attrib []ItemAttribute `json:"attrib"`
}

type AbilityDefinition struct {
	ID        int             `json:"id"`
	Dname     string          `json:"dname"`
	Attrib    []ItemAttribute `json:"attrib"`
	ManaCost  interface{}     `json:"mc"`
	Cooldown  interface{}     `json:"cd"`
	CastRange interface{}     `json:"cast_range"`
}

type HeroGeneralData struct {
	HeroID      int     `json:"hero_id"`
	HeroName    string  `json:"hero_name"`
	IsRadiant   int     `json:"is_radiant"`
	TeamSlot    int     `json:"team_slot"`
	Level       int     `json:"level"`
	Kills       int     `json:"kills"`
	Deaths      int     `json:"deaths"`
	Assists     int     `json:"assists"`
	LastHits    int     `json:"last_hits"`
	Denies      int     `json:"denies"`
	Gold        int     `json:"gold"`
	X           float32 `json:"x"`
	Y           float32 `json:"y"`
	XP          int     `json:"xp"`
	Square      int     `json:"square"`
	Networth    int     `json:"networth"`
	Health      float32 `json:"health"`
	MaxHealth   float32 `json:"max_health"`
	Mana        float32 `json:"mana"`
	MaxMana     float32 `json:"max_mana"`
	Agility     int     `json:"agility"`
	Intellect   int     `json:"intellect"`
	Strength    int     `json:"strength"`
	MagicResist int     `json:"magical_resistance"`
	Armor       float32 `json:"armor"`
	MoveSpeed   int     `json:"movespeed"`
	BKBcooldown int     `json:"bkb_cooldown"`

	ItemBlackKingBar int `json:"item_black_king_bar"`
	ItemBlink        int `json:"item_blink"`
	ItemForceStaff   int `json:"item_force_staff"`
	ItemBasher       int `json:"item_basher"`
	ItemAbyssalBlade int `json:"item_abyssal_blade"`
	ItemNullifier    int `json:"item_nullifier"`
	ItemLotusOrb     int `json:"item_lotus_orb"`
	ItemTravelBoots  int `json:"item_travel_boots"`
	ItemTpscroll     int `json:"item_tpscroll"`
	ItemPhaseBoots   int `json:"item_phase_boots"`
	ItemSilverEdge   int `json:"item_silver_edge"`
	ItemHeart        int `json:"item_heart"`
	ItemSphere       int `json:"item_sphere"`
	ItemManta        int `json:"item_manta"`
	ItemBladeMail    int `json:"item_blade_mail"`
	ItemAeonDisk     int `json:"item_aeon_disk"`
	ItemPipe         int `json:"item_pipe"`

	// Ability
	Ability1Level     int `json:"ability1_level"`
	Ability1CastRange int `json:"ability1_castrange"`
	Ability1ManaCost  int `json:"ability1_manacost"`
	Ability1Cooldown  int `json:"ability1_cooldown"`

	Ability2Level     int `json:"ability2_level"`
	Ability2CastRange int `json:"ability2_castrange"`
	Ability2ManaCost  int `json:"ability2_manacost"`
	Ability2Cooldown  int `json:"ability2_cooldown"`

	Ability3Level     int `json:"ability3_level"`
	Ability3CastRange int `json:"ability3_castrange"`
	Ability3ManaCost  int `json:"ability3_manacost"`
	Ability3Cooldown  int `json:"ability3_cooldown"`

	Ability4Level     int `json:"ability4_level"`
	Ability4CastRange int `json:"ability4_castrange"`
	Ability4ManaCost  int `json:"ability4_manacost"`
	Ability4Cooldown  int `json:"ability4_cooldown"`

	IsDead20s int
	IsDead15s int
	IsDead10s int
	IsDead5s  int
	IsDead1s  int
}

type rawLine struct {
	Type         string  `json:"type"`
	Time         float64 `json:"time"`
	MatchID      int64   `json:"match_id"`
	HeroID       int     `json:"hero_id"`
	TargetHero   bool    `json:"targethero"`
	TargetName   string  `json:"targetname"`
	Inflictor    string  `json:"inflictor"`
	AttackerName string  `json:"attackername"`
	Slot         int     `json:"slot"`
	Unit         string  `json:"unit"`
	Level        int     `json:"level"`
	Kills        int     `json:"kills"`
	Deaths       int     `json:"deaths"`
	Assists      int     `json:"assists"`
	LH           int     `json:"lh"`
	Denies       int     `json:"denies"`
	Gold         int     `json:"gold"`
	XP           int     `json:"xp"`
	X            float32 `json:"x"`
	Y            float32 `json:"y"`
	ValueName    string  `json:"valuename"`
	AbilityLevel int     `json:"abilitylevel"`
	Networth     int     `json:"networth"`
}

type GeneralGameState struct {
	MatchID      int64             `json:"match_id"`
	GameTime     int               `json:"game_time"`
	IsDaytime    int               `json:"day"`
	RadiantScore int               `json:"radiant_score"`
	DireScore    int               `json:"dire_score"`
	Heroes       []HeroGeneralData `json:"heroes"`
}

func parseAbilityValue(raw interface{}, level int) int {
	if raw == nil || level <= 0 {
		return 0
	}
	idx := level - 1

	switch v := raw.(type) {
	case float64:
		return int(v)
	case string:
		parts := strings.Fields(v)
		if len(parts) == 0 {
			return 0
		}
		if idx >= len(parts) {
			idx = len(parts) - 1
		}
		res, _ := strconv.ParseFloat(parts[idx], 32)
		return int(res)
	case []interface{}:
		if len(v) == 0 {
			return 0
		}
		if idx >= len(v) {
			idx = len(v) - 1
		}
		return parseAbilityValue(v[idx], 1)
	}
	return 0
}

func getAbilityAttribute(def AbilityDefinition, key string, level int) int {
	for _, attr := range def.Attrib {
		if attr.Key == key || attr.Key == "ability"+key || attr.Key == "ability_"+key {
			return parseAbilityValue(attr.Value, level)
		}
	}
	return 0
}

func fillAbilityData(heroData *HeroGeneralData, abilityName string, slotIndex int, level int) {
	if level == 0 {
		return
	}

	abDef, ok := AbilityStatsMap[abilityName]
	if !ok {
		return
	}

	castRange := getAbilityAttribute(abDef, "castrange", level)
	if castRange == 0 {
		castRange = getAbilityAttribute(abDef, "cast_range", level)
	}
	if castRange == 0 {
		castRange = parseAbilityValue(abDef.CastRange, level)
	}

	manaCost := parseAbilityValue(abDef.ManaCost, level)
	if manaCost == 0 {
		manaCost = getAbilityAttribute(abDef, "manacost", level)
	}
	if manaCost == 0 {
		manaCost = getAbilityAttribute(abDef, "mana_cost", level)
	}

	cooldown := parseAbilityValue(abDef.Cooldown, level)
	if cooldown == 0 {
		cooldown = getAbilityAttribute(abDef, "cooldown", level)
	}

	switch slotIndex {
	case 0:
		heroData.Ability1Level = level
		heroData.Ability1CastRange = castRange
		heroData.Ability1ManaCost = manaCost
		heroData.Ability1Cooldown = cooldown
	case 1:
		heroData.Ability2Level = level
		heroData.Ability2CastRange = castRange
		heroData.Ability2ManaCost = manaCost
		heroData.Ability2Cooldown = cooldown
	case 2:
		heroData.Ability3Level = level
		heroData.Ability3CastRange = castRange
		heroData.Ability3ManaCost = manaCost
		heroData.Ability3Cooldown = cooldown
	case 3:
		heroData.Ability4Level = level
		heroData.Ability4CastRange = castRange
		heroData.Ability4ManaCost = manaCost
		heroData.Ability4Cooldown = cooldown
	}
}

type calculatedStats struct {
	Str, Agi, Int     int
	Health, MaxHealth float32
	Mana, MaxMana     float32
	Armor             float32
	MagicResist       int
	MoveSpeed         int
}

func calculateHeroStats(heroName string, level int, inventory []string) calculatedStats {
	base, ok := HeroStatsMap[heroName]
	if !ok {
		return calculatedStats{}
	}
	lvlIndex := float32(level - 1)
	if lvlIndex < 0 {
		lvlIndex = 0
	}

	str := float32(base.BaseStr) + (base.StrGain * lvlIndex)
	agi := float32(base.BaseAgi) + (base.AgiGain * lvlIndex)
	intel := float32(base.BaseInt) + (base.IntGain * lvlIndex)
	var bonusStr, bonusAgi, bonusInt float32
	var bonusHealth, bonusMana, bonusArmor, bonusMS float32
	var bonusMagicResist int

	for _, itemName := range inventory {
		item, exists := ItemStatsMap[itemName]
		if !exists {
			continue
		}
		for _, attr := range item.Attrib {
			val := parseAbilityValue(attr.Value, 1)
			val32 := float32(val)
			switch attr.Key {
			case "bonus_strength":
				bonusStr += val32
			case "bonus_agility":
				bonusAgi += val32
			case "bonus_intellect":
				bonusInt += val32
			case "bonus_health":
				bonusHealth += val32
			case "bonus_mana":
				bonusMana += val32
			case "bonus_armor":
				bonusArmor += val32
			case "movement_speed", "bonus_movement_speed":
				bonusMS += val32
			case "magical_resistance", "bonus_magical_resistance":
				bonusMagicResist += int(val)
			}
		}
	}
	totalStr := int(math.Floor(float64(str + bonusStr)))
	totalAgi := int(math.Floor(float64(agi + bonusAgi)))
	totalInt := int(math.Floor(float64(intel + bonusInt)))
	maxHealth := base.BaseHealth + (float32(totalStr) * 22.0) + bonusHealth
	maxMana := base.BaseMana + (float32(totalInt) * 12.0) + bonusMana
	armor := base.BaseArmor + (float32(totalAgi) * 0.167) + bonusArmor
	magicResist := base.BaseMr + int(float32(totalInt)*0.1) + bonusMagicResist
	moveSpeed := base.MoveSpeed + int(bonusMS)

	return calculatedStats{
		Str: totalStr, Agi: totalAgi, Int: totalInt,
		Health: maxHealth, MaxHealth: maxHealth,
		Mana: maxMana, MaxMana: maxMana,
		Armor: armor, MagicResist: magicResist,
		MoveSpeed: moveSpeed,
	}
}

func setItemFlags(hero *HeroGeneralData, inventory []string) {
	hero.ItemBlackKingBar = 0
	hero.ItemBlink = 0
	hero.ItemForceStaff = 0
	hero.ItemBasher = 0
	hero.ItemAbyssalBlade = 0
	hero.ItemNullifier = 0
	hero.ItemLotusOrb = 0
	hero.ItemTravelBoots = 0
	hero.ItemTpscroll = 0
	hero.ItemPhaseBoots = 0
	hero.ItemSilverEdge = 0
	hero.ItemHeart = 0
	hero.ItemSphere = 0
	hero.ItemManta = 0
	hero.ItemBladeMail = 0
	hero.ItemAeonDisk = 0
	hero.ItemPipe = 0

	for _, item := range inventory {
		switch item {
		case "black_king_bar":
			hero.ItemBlackKingBar = 1
		case "blink", "overwhelming_blink", "swift_blink", "arcane_blink":
			hero.ItemBlink = 1
		case "force_staff", "hurricane_pike":
			hero.ItemForceStaff = 1
		case "basher":
			hero.ItemBasher = 1
		case "abyssal_blade":
			hero.ItemAbyssalBlade = 1
		case "nullifier":
			hero.ItemNullifier = 1
		case "lotus_orb":
			hero.ItemLotusOrb = 1
		case "travel_boots", "travel_boots_2":
			hero.ItemTravelBoots = 1
		case "tpscroll":
			hero.ItemTpscroll = 1
		case "phase_boots":
			hero.ItemPhaseBoots = 1
		case "silver_edge":
			hero.ItemSilverEdge = 1
		case "heart":
			hero.ItemHeart = 1
		case "sphere":
			hero.ItemSphere = 1
		case "manta":
			hero.ItemManta = 1
		case "blade_mail":
			hero.ItemBladeMail = 1
		case "aeon_disk":
			hero.ItemAeonDisk = 1
		case "pipe":
			hero.ItemPipe = 1
		}
	}
}

func ParseGeneralWorker(filePath string) ([]GeneralGameState, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	currentMatchID := fetchMatchIDFromEpilogue(filePath)

	heroToIsRadiant := make(map[string]int)

	results := make([]GeneralGameState, 0, 4000)
	var currentFrame *GeneralGameState
	slotToHero := make(map[int]string, 10)
	heroInventory := make(map[string][]string)
	heroAbilityLevels := make(map[string]map[string]int)
	heroBkbLastUsed := make(map[string]int)
	var radiantScore, direScore int
	lastProcessedTime := -99999

	decoder := json.NewDecoder(file)

	for decoder.More() {
		var line rawLine
		if err := decoder.Decode(&line); err != nil {
			continue
		}

		lineTime := int(line.Time)

		if lastProcessedTime == -99999 {
			lastProcessedTime = lineTime
		}

		if lineTime < 0 && lastProcessedTime > 0 {
			continue
		}

		if line.Type != "" && (currentFrame == nil || currentFrame.GameTime != lineTime) {

			if currentFrame != nil {
				results = append(results, *currentFrame)
				lastProcessedTime = currentFrame.GameTime
			}

			if lineTime > lastProcessedTime+1 {
				for t := lastProcessedTime + 1; t < lineTime; t++ {
					results = append(results, GeneralGameState{
						MatchID:      currentMatchID,
						GameTime:     t,
						IsDaytime:    isDaylight(float64(t)),
						RadiantScore: radiantScore,
						DireScore:    direScore,
						Heroes:       []HeroGeneralData{},
					})
				}
			}
			currentFrame = &GeneralGameState{
				MatchID:      currentMatchID,
				GameTime:     lineTime,
				IsDaytime:    isDaylight(line.Time),
				RadiantScore: radiantScore,
				DireScore:    direScore,
				Heroes:       make([]HeroGeneralData, 0, 10),
			}
			lastProcessedTime = lineTime
		}

		switch line.Type {
		case "match_id":
			currentMatchID = line.MatchID
			if currentFrame != nil {
				currentFrame.MatchID = currentMatchID
			}

		case "DOTA_COMBATLOG_DEATH":
			if line.TargetHero {
				attacker := NormalizeHeroName(line.AttackerName)
				isRadiantKiller, exists := heroToIsRadiant[attacker]
				if exists == true {
					if isRadiantKiller == 1 {
						radiantScore++
					} else {
						direScore++
					}
				} else {
					if strings.Contains(line.TargetName, "goodguys") {
						direScore++
					} else if strings.Contains(line.TargetName, "badguys") {
						radiantScore++
					}
				}
				if currentFrame != nil {
					currentFrame.RadiantScore = radiantScore
					currentFrame.DireScore = direScore
				}
				appendDeathPredict(results, line.TargetName, lineTime)
			}

		case "DOTA_COMBATLOG_PURCHASE":
			if line.TargetName != "" && line.ValueName != "" {
				target := NormalizeHeroName(line.TargetName)
				itemName := strings.TrimPrefix(line.ValueName, "item_")
				heroInventory[target] = append(heroInventory[target], itemName)
			}

		case "DOTA_COMBATLOG_ITEM", "DOTA_COMBATLOG_ITEM_USED":
			if line.AttackerName != "" && line.Inflictor != "" {
				heroName := NormalizeHeroName(line.AttackerName)
				itemToRemove := strings.TrimPrefix(line.Inflictor, "item_")
				if ConsumableItems[itemToRemove] == 1 {
					inventory := heroInventory[heroName]
					for i, item := range inventory {
						if item == itemToRemove {
							heroInventory[heroName] = append(inventory[:i], inventory[i+1:]...)
							break
						}
					}
				}
			}

		case "DOTA_ABILITY_LEVEL":
			if line.TargetName != "" && line.ValueName != "" {
				heroName := NormalizeHeroName(line.TargetName)
				if strings.HasPrefix(line.ValueName, "special_bonus") {
					continue
				}
				if heroAbilityLevels[heroName] == nil {
					heroAbilityLevels[heroName] = make(map[string]int)
				}
				heroAbilityLevels[heroName][line.ValueName] = line.AbilityLevel
			}

		case "DOTA_COMBATLOG_MODIFIER_ADD":
			if line.Inflictor == "modifier_black_king_bar_immune" {
				heroName := NormalizeHeroName(line.TargetName)
				if heroName == "" {
					heroName = NormalizeHeroName(line.AttackerName)
				}

				heroBkbLastUsed[heroName] = lineTime
			}

		case "interval":
			var heroName string
			if line.Unit != "" && strings.Contains(line.Unit, "Hero") {
				heroName = NormalizeHeroName(line.Unit)
				slotToHero[line.Slot] = heroName
			} else {
				heroName = slotToHero[line.Slot]
			}
			if heroName == "" || currentFrame == nil {
				continue
			}

			bkbCooldown := 0
			if lastUsed, ok := heroBkbLastUsed[heroName]; ok {
				elapsed := lineTime - lastUsed
				if elapsed < int(BKBTotalCooldown) {
					bkbCooldown = int(BKBTotalCooldown) - elapsed
				}
			}

			stats := calculateHeroStats(heroName, line.Level, heroInventory[heroName])

			isRadiantVal := 0
			if line.Slot < 5 {
				isRadiantVal = 1
			}

			teamSlot := (line.Slot % 5) + 1

			X, Y := ToWorld(line.X), ToWorld(line.Y)

			heroData := HeroGeneralData{
				HeroName:    heroName,
				HeroID:      line.HeroID,
				IsRadiant:   isRadiantVal,
				TeamSlot:    teamSlot, // Добавляем вычисленный индекс
				Level:       line.Level,
				Kills:       line.Kills,
				Deaths:      line.Deaths,
				Assists:     line.Assists,
				LastHits:    line.LH,
				Denies:      line.Denies,
				Gold:        line.Gold,
				XP:          line.XP,
				X:           X,
				Y:           Y,
				Square:      GetGridID(X, Y),
				Health:      stats.Health,
				MaxHealth:   stats.MaxHealth,
				Mana:        stats.Mana,
				MaxMana:     stats.MaxMana,
				Agility:     stats.Agi,
				Intellect:   stats.Int,
				Strength:    stats.Str,
				MagicResist: stats.MagicResist,
				Armor:       stats.Armor,
				MoveSpeed:   stats.MoveSpeed,
				Networth:    line.Networth,
				BKBcooldown: bkbCooldown,
			}
			setItemFlags(&heroData, heroInventory[heroName])
			heroDef, ok := HeroAbilitiesMap[heroName]
			if ok {
				var mainAbilities []string
				for _, ab := range heroDef.Abilities {
					if ab != "generic_hidden" {
						mainAbilities = append(mainAbilities, ab)
					}
				}

				for i := 0; i < 4; i++ {
					if i < len(mainAbilities) {
						abilityName := mainAbilities[i]

						lvl := 0
						if heroAbilityLevels[heroName] != nil {
							lvl = heroAbilityLevels[heroName][abilityName]
						}

						fillAbilityData(&heroData, abilityName, i, lvl)
					}
				}
			}

			currentFrame.Heroes = append(currentFrame.Heroes, heroData)
			heroName = NormalizeHeroName(heroName)
			heroToIsRadiant[heroName] = isRadiantVal
		}
	}
	if currentFrame != nil {
		results = append(results, *currentFrame)
	}
	return results, nil
}

func isDaylight(gameTime float64) int {
	if gameTime < 0 {
		return 1
	}
	if (int(gameTime) % 600) < 300 {
		return 1
	}
	return 0
}

func appendDeathPredict(results []GeneralGameState, heroName string, deathTime int) {
	if len(results) == 0 {
		return
	}
	firstTime := results[0].GameTime
	deathIndex := deathTime - firstTime
	for i := 1; i <= 20; i++ {
		idx := deathIndex - i
		if idx < 0 || idx >= len(results) {
			continue
		}
		for hIdx := range results[idx].Heroes {
			if results[idx].Heroes[hIdx].HeroName == heroName {
				hero := &results[idx].Heroes[hIdx]
				if i <= 1 {
					hero.IsDead1s = 1
				}
				if i <= 5 {
					hero.IsDead5s = 1
				}
				if i <= 10 {
					hero.IsDead10s = 1
				}
				if i <= 15 {
					hero.IsDead15s = 1
				}
				if i <= 20 {
					hero.IsDead20s = 1
				}
				break
			}
		}
	}
}

func fetchMatchIDFromEpilogue(filePath string) int64 {
	file, err := os.Open(filePath)
	if err != nil {
		return 0
	}
	defer file.Close()

	stat, _ := file.Stat()
	filesize := stat.Size()
	if filesize == 0 {
		return 0
	}

	readSize := int64(8192)
	if filesize < readSize {
		readSize = filesize
	}

	buf := make([]byte, readSize)
	_, err = file.ReadAt(buf, filesize-readSize)
	if err != nil {
		return 0
	}

	s := string(buf)

	target := "matchId_"
	idx := strings.LastIndex(s, target)
	if idx == -1 {
		return 0
	}

	start := idx + len(target)

	for start < len(s) && (s[start] < '0' || s[start] > '9') {
		start++
	}

	end := start
	for end < len(s) && s[end] >= '0' && s[end] <= '9' {
		end++
	}

	if start == end {
		return 0
	}

	id, _ := strconv.ParseInt(s[start:end], 10, 64)
	return id
}
