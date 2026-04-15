package utils

import (
	"encoding/json"
	"math"
	"os"
	"strings"
)

func LoadGameData(heroStatsPath, itemsPath, abilitiesPath, heroAbilitiesPath string) error {
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

	aContent, err := os.ReadFile(abilitiesPath)
	if err != nil {
		return err
	}
	AbilityStatsMap = make(map[string]AbilityDefinition)
	if err := json.Unmarshal(aContent, &AbilityStatsMap); err != nil {
		return err
	}

	haContent, err := os.ReadFile(heroAbilitiesPath)
	if err != nil {
		return err
	}
	HeroAbilitiesMap = make(map[string]HeroAbilitiesDefinition)
	if err := json.Unmarshal(haContent, &HeroAbilitiesMap); err != nil {
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

func NormalizeName(name string) string {
	return strings.ToLower(strings.Replace(name, "CDOTA_Unit_Hero_", "npc_dota_hero_", 1))
}

func GetGridID(x, y float32) int {
	return int((y-GridYMin)/(GridYMax-GridYMin)*float32(GridCells))*GridCells + int((x-GridXMin)/(GridXMax-GridXMin)*float32(GridCells))
}

func getTreeGridIdx(x, y float32) int {
	MapMin := float32(-8000.0)
	GridSize := float32(512.0)
	cols := int((8000.0-(-8000.0))/GridSize) + 1
	gx := int((x - MapMin) / GridSize)
	gy := int((y - MapMin) / GridSize)
	return gx*cols + gy
}

func ToWorld(val float32) float32 { return (val - CoordOffset) * CoordScale }

func GetDistSq(x1, y1, x2, y2 float32) float32 {
	return (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2)
}

func GetDist(x1, y1, x2, y2 float32) float32 {
	return float32(math.Sqrt(float64(GetDistSq(x1, y1, x2, y2))))
}

func minF(a, b float32) float32 {
	if a < b {
		return a
	}
	return b
}
func maxF(a, b float32) float32 {
	if a > b {
		return a
	}
	return b
}
