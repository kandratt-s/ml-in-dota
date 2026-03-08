package utils

import (
	"encoding/json"
	"os"
	"strings"
)

type HeroGeneralData struct {
	HeroID      string  `json:"hero_id"`
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
}

type rawLine struct {
	Type         string  `json:"type"`
	Time         float64 `json:"time"`
	MatchID      int64   `json:"match_id"`
	TargetHero   bool    `json:"targethero"`
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

func ParseGeneralWorker(filePath string) ([]GeneralGameState, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	results := make([]GeneralGameState, 0, 3500)
	var currentFrame *GeneralGameState

	var currentMatchID int64
	slotToHero := make(map[int]string, 10)
	var radiantScore, direScore int

	decoder := json.NewDecoder(file)

	for decoder.More() {
		var line rawLine
		if err := decoder.Decode(&line); err != nil {
			continue
		}

		lineTime := int(line.Time)

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
		}

		switch line.Type {
		case "match_id":
			currentMatchID = line.MatchID
			if currentFrame != nil {
				currentFrame.MatchID = currentMatchID
			}

		case "DOTA_COMBATLOG_DEATH":
			if line.TargetHero {
				if strings.Contains(line.AttackerName, "goodguys") {
					radiantScore++
				} else {
					direScore++
				}
				if currentFrame != nil {
					currentFrame.RadiantScore = radiantScore
					currentFrame.DireScore = direScore
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

			currentFrame.Heroes = append(currentFrame.Heroes, HeroGeneralData{
				HeroID:      heroName,
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
				Health:      line.Health,
				MaxHealth:   line.MaxHealth,
				Mana:        line.Mana,
				MaxMana:     line.MaxMana,
				Agility:     line.Agility,
				Intellect:   line.Intellect,
				Strength:    line.Strength,
				MagicResist: line.MagResist,
				Armor:       line.Armor,
				MoveSpeed:   line.Movespeed,
			})
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
