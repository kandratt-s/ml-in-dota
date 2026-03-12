package utils

import (
	"encoding/json"
	"os"
	"strings"
)

type rawItemLine struct {
	Type      string  `json:"type"`
	Time      float64 `json:"time"`
	MatchID   int64   `json:"match_id"`
	Target    string  `json:"targetname"`
	Value     string  `json:"valuename"`
	Inflictor string  `json:"inflictor"`
	Slot      int     `json:"slot"`
	Unit      string  `json:"unit"`
}

type ItemHeroData struct {
	HeroID      string   `json:"hero_id"`
	Items       []string `json:"items"`
	BKBCooldown float32  `json:"bkb_cooldown"`
}

type ItemsGameState struct {
	MatchID  int64          `json:"match_id"`
	GameTime int            `json:"game_time"`
	Heroes   []ItemHeroData `json:"heroes"`
}

type inventoryState struct {
	items           []string
	lastBKBUsedTime float64
}

func ParseItemsWorker(filePath string) ([]ItemsGameState, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	results := make([]ItemsGameState, 0, 3500)
	var currentFrame *ItemsGameState

	var currentMatchID int64
	inventories := make(map[string]*inventoryState, 10)
	slotToHero := make(map[int]string, 10)
	lastProcessedTime := -99999

	consumables := map[string]struct{}{
		"item_tango": {}, "item_clarity": {}, "item_flask": {},
		"item_enchanted_mango": {}, "item_ward_observer": {},
		"item_ward_sentry": {}, "item_tpscroll": {},
	}

	decoder := json.NewDecoder(file)
	for decoder.More() {
		var line rawItemLine
		if err := decoder.Decode(&line); err != nil {
			continue
		}

		lineTime := int(line.Time)
		if lastProcessedTime != -99999 && lineTime > lastProcessedTime+1 {
			for t := lastProcessedTime + 1; t < lineTime; t++ {
				results = append(results, ItemsGameState{
					MatchID:  currentMatchID,
					GameTime: t,
					Heroes:   []ItemHeroData{},
				})
			}
		}

		if line.Type != "" && (currentFrame == nil || currentFrame.GameTime != lineTime) {
			if currentFrame != nil {
				results = append(results, *currentFrame)
			}
			currentFrame = &ItemsGameState{
				MatchID:  currentMatchID,
				GameTime: lineTime,
				Heroes:   make([]ItemHeroData, 0, 10),
			}
			lastProcessedTime = lineTime
		}

		switch line.Type {
		case "match_id":
			currentMatchID = line.MatchID
			if currentFrame != nil {
				currentFrame.MatchID = currentMatchID
			}

		case "DOTA_COMBATLOG_PURCHASE":
			heroName := normalizeHeroName(line.Target)
			if heroName != "" {
				inv, ok := inventories[heroName]
				if !ok {
					inv = &inventoryState{items: make([]string, 0, 12)}
					inventories[heroName] = inv
				}
				inv.items = append(inv.items, line.Value)
			}

		case "DOTA_COMBATLOG_ITEM_USED":
			heroName := normalizeHeroName(line.Target)
			if inv, ok := inventories[heroName]; ok {
				if strings.Contains(line.Inflictor, "black_king_bar") {
					inv.lastBKBUsedTime = line.Time
				}
				if _, isConsumable := consumables[line.Inflictor]; isConsumable {
					inv.items = removeFromSlice(inv.items, line.Inflictor)
				}
			}

		case "interval":
			var heroName string
			if line.Unit != "" && strings.Contains(line.Unit, "Hero") {
				heroName = normalizeHeroName(line.Unit)
				slotToHero[line.Slot] = heroName
			} else {
				heroName = slotToHero[line.Slot]
			}

			if heroName == "" || currentFrame == nil {
				continue
			}

			var itemsSnapshot []string
			var bkbCd float32 = 0

			if inv, ok := inventories[heroName]; ok {
				if len(inv.items) > 0 {
					itemsSnapshot = make([]string, len(inv.items))
					copy(itemsSnapshot, inv.items)
				}

				timeSinceBKB := float32(line.Time - inv.lastBKBUsedTime)
				if inv.lastBKBUsedTime > 0 && timeSinceBKB < 90 {
					bkbCd = 90 - timeSinceBKB
				}
			}

			currentFrame.Heroes = append(currentFrame.Heroes, ItemHeroData{
				HeroID:      heroName,
				Items:       itemsSnapshot,
				BKBCooldown: bkbCd,
			})
		}
	}

	if currentFrame != nil {
		results = append(results, *currentFrame)
	}

	return results, nil
}

func normalizeHeroName(name string) string {
	if name == "" || name == "dota_unknown" {
		return ""
	}
	return strings.ToLower(strings.Replace(name, "CDOTA_Unit_Hero_", "npc_dota_hero_", 1))
}

func removeFromSlice(slice []string, val string) []string {
	for i, item := range slice {
		if item == val {
			return append(slice[:i], slice[i+1:]...)
		}
	}
	return slice
}
