package utils

import (
	"encoding/json"
	"math"
	"os"
	"sort"
	"strings"
)

const (
	CoordOffset float32 = 128.0
	CoordScale  float32 = 64.0

	VisionRadiusDay   float32 = 1800.0
	VisionRadiusNight float32 = 800.0
	VisionRadiusWard  float32 = 1600.0
	TowerTrueSight    float32 = 900.0
	SentryTrueSight   float32 = 900.0

	SmokeBreakRadius float32 = 1025.0

	TreeBlockRadius float32 = 100.0
	HighGroundLimit float32 = 150.0

	GridXMin  float32 = -9400.0
	GridXMax  float32 = 8000.0
	GridYMin  float32 = -8500.0
	GridYMax  float32 = 8500.0
	GridCells int     = 32
)

var InvisibilityModifiers = map[string]bool{
	"modifier_rune_invis":                 true,
	"modifier_bounty_hunter_wind_walk":    true,
	"modifier_clinkz_wind_walk":           true,
	"modifier_item_glimmer_cape_fade":     true,
	"modifier_item_invis_sword":           true,
	"modifier_item_silver_edge":           true,
	"modifier_invoker_ghost_walk_enemy":   true,
	"modifier_nyx_assassin_vendetta":      true,
	"modifier_sandking_sand_storm_invis":  true,
	"modifier_templar_assassin_meld":      true,
	"modifier_treant_nature_guise":        true,
	"modifier_weaver_shukuchi":            true,
	"modifier_winter_wyvern_cold_embrace": true,
}

const ModifierSmoke = "modifier_smoke_of_deceit"

type InputLogLine struct {
	Time         float64 `json:"time"`
	Type         string  `json:"type"`
	Slot         int     `json:"slot,omitempty"`
	X            float32 `json:"x,omitempty"`
	Y            float32 `json:"y,omitempty"`
	Z            float32 `json:"z,omitempty"`
	UnitLongName string  `json:"unit,omitempty"`
	LifeState    int     `json:"life_state,omitempty"`
	Ehandle      int     `json:"ehandle,omitempty"`
	EntityLeft   bool    `json:"entityleft,omitempty"`
	AttackerName string  `json:"attackername,omitempty"`
	TargetName   string  `json:"targetname,omitempty"`
	Inflictor    string  `json:"inflictor,omitempty"`
}

type Tree struct{ X, Y float32 }

type VisionEnemeyTeam struct {
	Time int              `json:"time"`
	Unit []UnitVisionData `json:"units"`
}

type UnitVisionData struct {
	Name      string `json:"name"`
	IsVisible bool   `json:"is_visible"`

	X float32 `json:"x"`
	Y float32 `json:"y"`
	Z float32 `json:"z"`

	NearestAllyDistance       float32 `json:"nearest_ally_distance"`
	NearestEnemyDistance      float32 `json:"nearest_enemy_distance"`
	NearestAllyTowerDistance  float32 `json:"nearest_ally_tower_distance"`
	NearestEnemyTowerDistance float32 `json:"nearest_enemy_tower_distance"`
	TimeFromLastSeen          float32 `json:"time_from_last_seen"`

	Enemy1Name         string  `json:"enemy_1_name"`
	Enemy1LastSeenX    int     `json:"enemy_1_last_seen_x"`
	Enemy1LastSeenY    int     `json:"enemy_1_last_seen_y"`
	Enemy1LastSeenSq   int     `json:"enemy_1_last_seen_sqare"`
	Enemy1LastSeenDist float32 `json:"enemy_1_last_seen_distance"`
	Enemy1LastSeenTime int     `json:"enemy_1_last_seen_time"`

	Enemy2Name         string  `json:"enemy_2_name"`
	Enemy2LastSeenX    int     `json:"enemy_2_last_seen_x"`
	Enemy2LastSeenY    int     `json:"enemy_2_last_seen_y"`
	Enemy2LastSeenSq   int     `json:"enemy_2_last_seen_sqare"`
	Enemy2LastSeenDist float32 `json:"enemy_2_last_seen_distance"`
	Enemy2LastSeenTime int     `json:"enemy_2_last_seen_time"`

	Enemy3Name         string  `json:"enemy_3_name"`
	Enemy3LastSeenX    int     `json:"enemy_3_last_seen_x"`
	Enemy3LastSeenY    int     `json:"enemy_3_last_seen_y"`
	Enemy3LastSeenSq   int     `json:"enemy_3_last_seen_sqare"`
	Enemy3LastSeenDist float32 `json:"enemy_3_last_seen_distance"`
	Enemy3LastSeenTime int     `json:"enemy_3_last_seen_time"`

	Enemy4Name         string  `json:"enemy_4_name"`
	Enemy4LastSeenX    int     `json:"enemy_4_last_seen_x"`
	Enemy4LastSeenY    int     `json:"enemy_4_last_seen_y"`
	Enemy4LastSeenSq   int     `json:"enemy_4_last_seen_sqare"`
	Enemy4LastSeenDist float32 `json:"enemy_4_last_seen_distance"`
	Enemy4LastSeenTime int     `json:"enemy_4_last_seen_time"`

	Enemy5Name         string  `json:"enemy_5_name"`
	Enemy5LastSeenX    int     `json:"enemy_5_last_seen_x"`
	Enemy5LastSeenY    int     `json:"enemy_5_last_seen_y"`
	Enemy5LastSeenSq   int     `json:"enemy_5_last_seen_sqare"`
	Enemy5LastSeenDist float32 `json:"enemy_5_last_seen_distance"`
	Enemy5LastSeenTime int     `json:"enemy_5_last_seen_time"`
}

type UnitState struct {
	Name             string
	Team             int
	X, Y, Z          float32
	IsAlive          bool
	Modifiers        map[string]bool
	CurrentlyVisible bool

	LastSeenX    float32
	LastSeenY    float32
	LastSeenZ    float32
	LastSeenTime float64
}

type WardState struct {
	Ehandle    int
	Team       int
	X, Y, Z    float32
	IsObserver bool
	EndTime    float64
}

type GameState struct {
	CurrentTime float64
	IsDaytime   bool
	Heroes      map[string]*UnitState
	ActiveWards []*WardState
	MyTeam      int
	Towers      []*UnitState
	TreeGrid    map[int][]Tree
}

func getGridID(x, y float32) int {
	offset := -GridXMin

	totalWidth := GridXMax - GridXMin
	cellSize := totalWidth / float32(GridCells)

	col := int((x + offset) / cellSize)
	row := int((y + (-GridYMin)) / ((GridYMax - GridYMin) / float32(GridCells)))

	if col < 0 {
		col = 0
	}
	if col >= GridCells {
		col = GridCells - 1
	}
	if row < 0 {
		row = 0
	}
	if row >= GridCells {
		row = GridCells - 1
	}

	return row*GridCells + col
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

func NormalizeName(name string) string {
	return strings.ToLower(strings.Replace(name, "CDOTA_Unit_Hero_", "npc_dota_hero_", 1))
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

func ParseVisionWorker(filePath string, myTeam int) ([]VisionEnemeyTeam, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	gs := &GameState{
		Heroes:   make(map[string]*UnitState, 10),
		TreeGrid: make(map[int][]Tree),
		MyTeam:   myTeam,
	}

	if mapData, err := os.ReadFile("dotadata/mapdata.json"); err == nil {
		gs.InitMap(mapData)
	}

	result := make([]VisionEnemeyTeam, 0, 4000)
	lastTimeInt := -9999

	decoder := json.NewDecoder(file)
	for decoder.More() {
		var line InputLogLine
		if err := decoder.Decode(&line); err != nil {
			continue
		}

		gs.Update(line)

		currentTimeInt := int(line.Time)
		if lastTimeInt != -9999 && currentTimeInt > lastTimeInt+1 {
			for t := lastTimeInt + 1; t < currentTimeInt; t++ {
				result = append(result, VisionEnemeyTeam{Time: t, Unit: []UnitVisionData{}})
			}
		}
		if currentTimeInt > lastTimeInt {
			snapshot := gs.CalculateVisibility(currentTimeInt)
			result = append(result, snapshot)
			lastTimeInt = currentTimeInt
		}
	}
	return result, nil
}

func (gs *GameState) Update(line InputLogLine) {
	gs.CurrentTime = line.Time
	if line.Time >= 0 {
		gs.IsDaytime = (int(line.Time) % 600) < 300
	}

	switch line.Type {
	case "interval":
		if strings.Contains(line.UnitLongName, "Hero") {
			name := NormalizeName(line.UnitLongName)
			hero, exists := gs.Heroes[name]
			if !exists {
				team := 2
				if line.Slot >= 5 {
					team = 3
				}
				hero = &UnitState{Name: name, Team: team, Modifiers: make(map[string]bool)}
				gs.Heroes[name] = hero
			}
			hero.X, hero.Y, hero.Z = ToWorld(line.X), ToWorld(line.Y), line.Z
			hero.IsAlive = (line.LifeState == 0)
		}

	case "obs", "sen":
		gs.RemoveWard(line.Ehandle)
		if line.EntityLeft {
			return
		}
		team := 2
		if line.Slot >= 5 {
			team = 3
		}
		gs.ActiveWards = append(gs.ActiveWards, &WardState{
			Ehandle: line.Ehandle, Team: team, X: ToWorld(line.X), Y: ToWorld(line.Y),
			Z: line.Z, IsObserver: line.Type == "obs", EndTime: line.Time + 360.0,
		})

	case "DOTA_COMBATLOG_DAMAGE":
		if attacker, ok := gs.Heroes[line.AttackerName]; ok {
			if strings.Contains(line.TargetName, "creep") {
				targetIsGood := strings.Contains(line.TargetName, "goodguys")
				attackerTeam := attacker.Team

				revealed := false
				if targetIsGood && attackerTeam == 3 {
					revealed = true
				} else if !targetIsGood && attackerTeam == 2 {
					revealed = true
				}

				if revealed {
					attacker.X, attacker.Y, attacker.Z = ToWorld(line.X), ToWorld(line.Y), line.Z
					attacker.LastSeenTime = line.Time
					attacker.LastSeenX, attacker.LastSeenY, attacker.LastSeenZ = attacker.X, attacker.Y, attacker.Z
				}
			}
		}

	case "DOTA_COMBATLOG_MODIFIER_ADD":
		if hero, ok := gs.Heroes[line.TargetName]; ok {
			hero.Modifiers[line.Inflictor] = true
		}

	case "DOTA_COMBATLOG_MODIFIER_REMOVE":
		if hero, ok := gs.Heroes[line.TargetName]; ok {
			delete(hero.Modifiers, line.Inflictor)
		}
	}
}

func (gs *GameState) CalculateVisibility(timeSec int) VisionEnemeyTeam {
	snapshot := VisionEnemeyTeam{Time: timeSec, Unit: make([]UnitVisionData, 0, 5)}

	var visionSources []*UnitState
	var trueSightSources []*UnitState
	var obsWards []*WardState
	var towers []*UnitState

	for _, h := range gs.Heroes {
		if h.Team == gs.MyTeam && h.IsAlive {
			visionSources = append(visionSources, h)
		}
	}
	for _, t := range gs.Towers {
		if t.Team == gs.MyTeam && t.IsAlive {
			visionSources = append(visionSources, t)
			trueSightSources = append(trueSightSources, t)
			towers = append(towers, t)
		}
	}
	for _, w := range gs.ActiveWards {
		if w.Team == gs.MyTeam && gs.CurrentTime < w.EndTime {
			if w.IsObserver {
				obsWards = append(obsWards, w)
			} else {
				trueSightSources = append(trueSightSources, &UnitState{X: w.X, Y: w.Y, Z: w.Z})
			}
		}
	}

	enemyHeroes := make([]*UnitState, 0, 5)
	for _, enemy := range gs.Heroes {
		if enemy.Team == gs.MyTeam {
			continue
		}
		enemyHeroes = append(enemyHeroes, enemy)

		visibleNow := false
		if enemy.IsAlive {
			visibleNow = gs.IsUnitVisible(enemy, visionSources, obsWards, trueSightSources, towers)
		}

		if gs.CurrentTime-enemy.LastSeenTime < 0.1 {
			visibleNow = true
		}

		enemy.CurrentlyVisible = visibleNow
		if visibleNow {
			enemy.LastSeenX, enemy.LastSeenY, enemy.LastSeenZ = enemy.X, enemy.Y, enemy.Z
			enemy.LastSeenTime = gs.CurrentTime
		}
	}

	sort.Slice(enemyHeroes, func(i, j int) bool {
		return enemyHeroes[i].Name < enemyHeroes[j].Name
	})

	for _, targetEnemy := range enemyHeroes {
		if targetEnemy.LastSeenTime <= 0 {
			continue
		}

		data := UnitVisionData{
			Name:                      targetEnemy.Name,
			IsVisible:                 targetEnemy.CurrentlyVisible,
			NearestAllyDistance:       gs.getNearestHeroDist(targetEnemy.X, targetEnemy.Y, targetEnemy.Team, true),
			NearestEnemyDistance:      gs.getNearestHeroDist(targetEnemy.X, targetEnemy.Y, targetEnemy.Team, false),
			NearestAllyTowerDistance:  gs.getNearestTowerDist(targetEnemy.X, targetEnemy.Y, targetEnemy.Team),
			NearestEnemyTowerDistance: gs.getNearestTowerDist(targetEnemy.X, targetEnemy.Y, gs.MyTeam),
			TimeFromLastSeen:          float32(gs.CurrentTime - targetEnemy.LastSeenTime),
		}

		if data.IsVisible {
			data.X, data.Y, data.Z = targetEnemy.X, targetEnemy.Y, targetEnemy.Z
		} else {
			data.X, data.Y, data.Z = targetEnemy.LastSeenX, targetEnemy.LastSeenY, targetEnemy.LastSeenZ
		}

		fillEnemyData := func(idx int, enemy *UnitState) {
			dist := GetDist(data.X, data.Y, enemy.LastSeenX, enemy.LastSeenY)
			lsTime := int(gs.CurrentTime - enemy.LastSeenTime)
			if enemy.LastSeenTime == 0 {
				lsTime = 99999
			}

			sq := getGridID(enemy.LastSeenX, enemy.LastSeenY)

			switch idx {
			case 0:
				data.Enemy1Name = enemy.Name
				data.Enemy1LastSeenX, data.Enemy1LastSeenY = int(enemy.LastSeenX), int(enemy.LastSeenY)
				data.Enemy1LastSeenSq = sq
				data.Enemy1LastSeenDist = dist
				data.Enemy1LastSeenTime = lsTime
			case 1:
				data.Enemy2Name = enemy.Name
				data.Enemy2LastSeenX, data.Enemy2LastSeenY = int(enemy.LastSeenX), int(enemy.LastSeenY)
				data.Enemy2LastSeenSq = sq
				data.Enemy2LastSeenDist = dist
				data.Enemy2LastSeenTime = lsTime
			case 2:
				data.Enemy3Name = enemy.Name
				data.Enemy3LastSeenX, data.Enemy3LastSeenY = int(enemy.LastSeenX), int(enemy.LastSeenY)
				data.Enemy3LastSeenSq = sq
				data.Enemy3LastSeenDist = dist
				data.Enemy3LastSeenTime = lsTime
			case 3:
				data.Enemy4Name = enemy.Name
				data.Enemy4LastSeenX, data.Enemy4LastSeenY = int(enemy.LastSeenX), int(enemy.LastSeenY)
				data.Enemy4LastSeenSq = sq
				data.Enemy4LastSeenDist = dist
				data.Enemy4LastSeenTime = lsTime
			case 4:
				data.Enemy5Name = enemy.Name
				data.Enemy5LastSeenX, data.Enemy5LastSeenY = int(enemy.LastSeenX), int(enemy.LastSeenY)
				data.Enemy5LastSeenSq = sq
				data.Enemy5LastSeenDist = dist
				data.Enemy5LastSeenTime = lsTime
			}
		}

		for i, e := range enemyHeroes {
			if i < 5 {
				fillEnemyData(i, e)
			}
		}

		snapshot.Unit = append(snapshot.Unit, data)
	}
	return snapshot
}

func (gs *GameState) IsUnitVisible(enemy *UnitState, visionUnits []*UnitState, obsWards []*WardState, trueSight []*UnitState, towers []*UnitState) bool {
	if enemy.Modifiers[ModifierSmoke] {
		for _, v := range visionUnits {
			if GetDistSq(v.X, v.Y, enemy.X, enemy.Y) <= SmokeBreakRadius*SmokeBreakRadius {
				return true
			}
		}
		return false
	}

	isInvis := false
	for mod := range enemy.Modifiers {
		if InvisibilityModifiers[mod] {
			isInvis = true
			break
		}
	}

	if isInvis {
		isRevealed := false
		for _, ts := range trueSight {
			if GetDistSq(ts.X, ts.Y, enemy.X, enemy.Y) <= SentryTrueSight*SentryTrueSight {
				isRevealed = true
				break
			}
		}
		if !isRevealed {
			return false
		}
	}

	radSq := VisionRadiusDay * VisionRadiusDay
	if !gs.IsDaytime {
		radSq = VisionRadiusNight * VisionRadiusNight
	}

	for _, ally := range visionUnits {
		if GetDistSq(ally.X, ally.Y, enemy.X, enemy.Y) <= radSq {
			if enemy.Z <= ally.Z+HighGroundLimit && !gs.IsPathBlockedByTrees(ally.X, ally.Y, enemy.X, enemy.Y) {
				return true
			}
		}
	}
	for _, ward := range obsWards {
		if GetDistSq(ward.X, ward.Y, enemy.X, enemy.Y) <= VisionRadiusWard*VisionRadiusWard {
			if enemy.Z <= ward.Z+HighGroundLimit && !gs.IsPathBlockedByTrees(ward.X, ward.Y, enemy.X, enemy.Y) {
				return true
			}
		}
	}
	return false
}

func (gs *GameState) IsPathBlockedByTrees(x1, y1, x2, y2 float32) bool {
	minX, maxX := minF(x1, x2)-TreeBlockRadius, maxF(x1, x2)+TreeBlockRadius
	minY, maxY := minF(y1, y2)-TreeBlockRadius, maxF(y1, y2)+TreeBlockRadius

	startGX := int((minX - (-8000.0)) / 512.0)
	endGX := int((maxX - (-8000.0)) / 512.0)
	startGY := int((minY - (-8000.0)) / 512.0)
	endGY := int((maxY - (-8000.0)) / 512.0)
	cols := int(16000/512) + 1

	for gx := startGX; gx <= endGX; gx++ {
		for gy := startGY; gy <= endGY; gy++ {
			idx := gx*cols + gy
			if trees, ok := gs.TreeGrid[idx]; ok {
				for _, tree := range trees {
					if isPointNearSegment(tree.X, tree.Y, x1, y1, x2, y2, TreeBlockRadius) {
						return true
					}
				}
			}
		}
	}
	return false
}

func isPointNearSegment(px, py, x1, y1, x2, y2, threshold float32) bool {
	dx, dy := x2-x1, y2-y1
	if dx == 0 && dy == 0 {
		return false
	}
	t := ((px-x1)*dx + (py-y1)*dy) / (dx*dx + dy*dy)
	if t < 0 || t > 1 {
		return false
	}
	nearestX, nearestY := x1+t*dx, y1+t*dy
	return (px-nearestX)*(px-nearestX)+(py-nearestY)*(py-nearestY) < threshold*threshold
}

func (gs *GameState) InitMap(mapDataJSON []byte) {
	var raw struct {
		Data struct {
			Towers []map[string]interface{} `json:"npc_dota_tower"`
			Trees  []map[string]interface{} `json:"ent_dota_tree"`
		} `json:"data"`
	}
	json.Unmarshal(mapDataJSON, &raw)
	for _, t := range raw.Data.Towers {
		tx, ty := float32(t["x"].(float64)), float32(t["y"].(float64))
		team := 2
		if tx > 0 || ty > 0 {
			team = 3
		}
		gs.Towers = append(gs.Towers, &UnitState{Name: "tower", X: tx, Y: ty, Z: 128, Team: team, IsAlive: true})
	}
	for _, t := range raw.Data.Trees {
		tr := Tree{X: float32(t["x"].(float64)), Y: float32(t["y"].(float64))}
		idx := getTreeGridIdx(tr.X, tr.Y)
		gs.TreeGrid[idx] = append(gs.TreeGrid[idx], tr)
	}
}

func (gs *GameState) getNearestHeroDist(x, y float32, team int, wantAlly bool) float32 {
	var minDist float32 = 99999
	for _, h := range gs.Heroes {
		if !h.IsAlive || (h.X == x && h.Y == y) {
			continue
		}
		if (wantAlly && h.Team != team) || (!wantAlly && h.Team == team) {
			continue
		}
		if d := GetDist(x, y, h.X, h.Y); d < minDist {
			minDist = d
		}
	}
	return minDist
}

func (gs *GameState) getNearestTowerDist(x, y float32, team int) float32 {
	var minDist float32 = 99999
	for _, t := range gs.Towers {
		if t.Team == team && t.IsAlive {
			if d := GetDist(x, y, t.X, t.Y); d < minDist {
				minDist = d
			}
		}
	}
	return minDist
}

func (gs *GameState) RemoveWard(ehandle int) {
	for i, w := range gs.ActiveWards {
		if w.Ehandle == ehandle {
			gs.ActiveWards = append(gs.ActiveWards[:i], gs.ActiveWards[i+1:]...)
			return
		}
	}
}
