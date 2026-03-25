package utils

import (
	"encoding/json"
	"math"
	"os"
	"strconv"
	"strings"
)

var heroToIsRadiant = make(map[string]bool)

var ConsumableItems = map[string]bool{
	"tango":           true,
	"clarity":         true,
	"enchanted_mango": true,
	"faerie_fire":     true,
	"flask":           true,
	"ward_observer":   true,
	"ward_sentry":     true,
	"smoke_of_deceit": true,
	"dust":            true,
	"tpscroll":        true,
	"cheese":          true,
	"refresher_shard": true,
	"aegis":           true,
}

type HeroStatsDefinition struct {
	ID              int     `json:"id"`
	Name            string  `json:"name"`
	PrimaryAttr     string  `json:"primary_attr"`
	BaseHealth      float32 `json:"base_health"`
	BaseMana        float32 `json:"base_mana"`
	BaseArmor       float32 `json:"base_armor"`
	BaseMr          int     `json:"base_mr"`
	BaseStr         int     `json:"base_str"`
	BaseAgi         int     `json:"base_agi"`
	BaseInt         int     `json:"base_int"`
	StrGain         float32 `json:"str_gain"`
	AgiGain         float32 `json:"agi_gain"`
	IntGain         float32 `json:"int_gain"`
	MoveSpeed       int     `json:"move_speed"`
	BaseHealthRegen float32 `json:"base_health_regen"`
	BaseManaRegen   float32 `json:"base_mana_regen"`
}

type ItemAttribute struct {
	Key   string `json:"key"`
	Value string `json:"value"`
}

type ItemDefinition struct {
	ID     int             `json:"id"`
	Dname  string          `json:"dname"`
	Attrib []ItemAttribute `json:"attrib"`
}

var (
	HeroStatsMap map[string]HeroStatsDefinition
	ItemStatsMap map[string]ItemDefinition
)

type HeroGeneralData struct {
	HeroID      int     `json:"hero_id"`
	HeroName    string  `json:"hero_name"`
	IsRadiant   bool    `json:"is_radiant"`
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

	// Items flags
	ItemBlackKingBar bool `json:"item_black_king_bar"`
	ItemBlink        bool `json:"item_blink"`
	ItemForceStaff   bool `json:"item_force_staff"`
	ItemBasher       bool `json:"item_basher"`
	ItemAbyssalBlade bool `json:"item_abyssal_blade"`
	ItemNullifier    bool `json:"item_nullifier"`
	ItemLotusOrb     bool `json:"item_lotus_orb"`
	ItemTravelBoots  bool `json:"item_travel_boots"`
	ItemTpscroll     bool `json:"item_tpscroll"`
	ItemPhaseBoots   bool `json:"item_phase_boots"`
	ItemSilverEdge   bool `json:"item_silver_edge"`
	ItemHeart        bool `json:"item_heart"`
	ItemSphere       bool `json:"item_sphere"`
	ItemManta        bool `json:"item_manta"`
	ItemBladeMail    bool `json:"item_blade_mail"`
	ItemAeonDisk     bool `json:"item_aeon_disk"`
	ItemPipe         bool `json:"item_pipe"`

	IsDead20s bool
	IsDead15s bool
	IsDead10s bool
	IsDead5s  bool
	IsDead1s  bool
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
	Health       float32 `json:"health"`
	MaxHealth    float32 `json:"max_health"`
	Mana         float32 `json:"mana"`
	MaxMana      float32 `json:"max_mana"`
	Agility      int     `json:"agility"`
	Intellect    int     `json:"intellect"`
	Strength     int     `json:"strength"`
	MagResist    int     `json:"magical_resistance"`
	Armor        float32 `json:"armor"`
	Movespeed    int     `json:"movespeed"`
}

type GeneralGameState struct {
	MatchID      int64             `json:"match_id"`
	GameTime     int               `json:"game_time"`
	IsDaytime    bool              `json:"day"`
	RadiantScore int               `json:"radiant_score"`
	DireScore    int               `json:"dire_score"`
	Heroes       []HeroGeneralData `json:"heroes"`
}

func LoadGameData(heroStatsPath, itemsPath string) error {
	hContent, err := os.ReadFile(heroStatsPath)
	if err != nil {
		return err
	}
	var heroes []HeroStatsDefinition
	if err := json.Unmarshal(hContent, &heroes); err != nil {
		return err
	}
	HeroStatsMap = make(map[string]HeroStatsDefinition)
	for _, h := range heroes {
		HeroStatsMap[h.Name] = h
	}

	iContent, err := os.ReadFile(itemsPath)
	if err != nil {
		return err
	}
	ItemStatsMap = make(map[string]ItemDefinition)
	if err := json.Unmarshal(iContent, &ItemStatsMap); err != nil {
		return err
	}

	return nil
}

func NormalizeHeroName(name string) string {
	s := strings.ToLower(name)
	if strings.Contains(s, "cdota_unit_hero_") {
		return strings.Replace(s, "cdota_unit_hero_", "npc_dota_hero_", 1)
	}
	return s
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
			val, err := strconv.ParseFloat(attr.Value, 32)
			if err != nil {
				continue
			}

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
	for _, item := range inventory {
		switch item {
		case "black_king_bar":
			hero.ItemBlackKingBar = true
		case "blink", "overwhelming_blink", "swift_blink", "arcane_blink":
			hero.ItemBlink = true
		case "force_staff", "hurricane_pike":
			hero.ItemForceStaff = true
		case "basher":
			hero.ItemBasher = true
		case "abyssal_blade":
			hero.ItemAbyssalBlade = true
		case "nullifier":
			hero.ItemNullifier = true
		case "lotus_orb":
			hero.ItemLotusOrb = true
		case "travel_boots", "travel_boots_2":
			hero.ItemTravelBoots = true
		case "tpscroll":
			hero.ItemTpscroll = true
		case "phase_boots":
			hero.ItemPhaseBoots = true
		case "silver_edge":
			hero.ItemSilverEdge = true
		case "heart":
			hero.ItemHeart = true
		case "sphere":
			hero.ItemSphere = true
		case "manta":
			hero.ItemManta = true
		case "blade_mail":
			hero.ItemBladeMail = true
		case "aeon_disk":
			hero.ItemAeonDisk = true
		case "pipe":
			hero.ItemPipe = true
		}
	}
}

func ParseGeneralWorker(filePath string) ([]GeneralGameState, error) {

	if len(HeroStatsMap) == 0 {
		LoadGameData("dotadata/heroStats.json", "dotadata/items.json")
	}

	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	results := make([]GeneralGameState, 0, 3500)
	var currentFrame *GeneralGameState

	var currentMatchID int64
	slotToHero := make(map[int]string, 10)
	heroInventory := make(map[string][]string)

	var radiantScore, direScore int
	lastProcessedTime := -99999

	decoder := json.NewDecoder(file)

	for decoder.More() {
		var line rawLine
		if err := decoder.Decode(&line); err != nil {
			continue
		}

		lineTime := int(line.Time)
		if lastProcessedTime != -99999 && lineTime > lastProcessedTime+1 {
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

		if line.Type != "" && (currentFrame == nil || currentFrame.GameTime != lineTime) {
			if currentFrame != nil {
				results = append(results, *currentFrame)
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

				if exists {
					if isRadiantKiller {
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

				if ConsumableItems[itemToRemove] {
					inventory := heroInventory[heroName]
					for i, item := range inventory {
						if item == itemToRemove {
							heroInventory[heroName] = append(inventory[:i], inventory[i+1:]...)
							break
						}
					}
				}
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
			stats := calculateHeroStats(heroName, line.Level, heroInventory[heroName])

			heroData := HeroGeneralData{
				HeroName:    heroName,
				HeroID:      line.HeroID,
				IsRadiant:   line.Slot < 5,
				Level:       line.Level,
				Kills:       line.Kills,
				Deaths:      line.Deaths,
				Assists:     line.Assists,
				LastHits:    line.LH,
				Denies:      line.Denies,
				Gold:        line.Gold,
				XP:          line.XP,
				X:           line.X,
				Y:           line.Y,
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
			}

			setItemFlags(&heroData, heroInventory[heroName])

			currentFrame.Heroes = append(currentFrame.Heroes, heroData)

			heroName = NormalizeHeroName(heroName)
			heroToIsRadiant[heroName] = line.Slot < 5
		}

	}

	if currentFrame != nil {
		results = append(results, *currentFrame)
	}

	return results, nil
}

func isDaylight(gameTime float64) bool {
	if gameTime < 0 {
		return true
	}
	return (int(gameTime) % 600) < 300
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
					hero.IsDead1s = true
				}
				if i <= 5 {
					hero.IsDead5s = true
				}
				if i <= 10 {
					hero.IsDead10s = true
				}
				if i <= 15 {
					hero.IsDead15s = true
				}
				if i <= 20 {
					hero.IsDead20s = true
				}
				break
			}
		}
	}
}
