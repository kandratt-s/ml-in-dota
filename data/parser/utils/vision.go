/*
варды, крипы, юниты, тавера, предметы, абилки, лес

z координата?
*/

package utils

import (
	"encoding/json"
	"math"
	"os"
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
	TreeBlockRadius   float32 = 100.0
	HighGroundLimit   float32 = 150.0
)

var GridSize float32 = 512.0
var MapMin float32 = -8000.0
var MapMax float32 = 8000.0
var GridColumns = int((MapMax-MapMin)/GridSize) + 1

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
	Name                      string     `json:"name"`
	IsVisible                 bool       `json:"is_visible"`
	IsLastKnown               bool       `json:"is_last_known"`
	X, Y, Z                   float32    `json:"x,y,z"`
	NearestAllyDistance       float32    `json:"nearest_ally_distance"`
	NearestEnemyDistance      float32    `json:"nearest_enemy_distance"`
	LastSeenPosition          [3]float32 `json:"last_seen_position"`
	TimeFromLastSeen          float32    `json:"time_from_last_seen"`
	NearestAllyTPDistance     float32    `json:"nearest_ally_tp_place_distance"`
	NearestAllyTowerDistance  float32    `json:"nearest_ally_tower_distance"`
	NearestEnemyTowerDistance float32    `json:"nearest_enemy_tower_distance"`
}

type UnitState struct {
	Name             string
	Team             int
	X, Y, Z          float32
	IsAlive          bool
	Modifiers        map[string]bool
	CurrentlyVisible bool
	LastSeenX        float32
	LastSeenY        float32
	LastSeenZ        float32
	LastSeenTime     float64
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

func getGridIdx(x, y float32) int {
	gx := int((x - MapMin) / GridSize)
	gy := int((y - MapMin) / GridSize)
	return gx*GridColumns + gy
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

	if mapData, err := os.ReadFile("mapdata.json"); err == nil {
		gs.InitMap(mapData)
	}

	result := make([]VisionEnemeyTeam, 0, 3500)
	lastTimeInt := -9999

	decoder := json.NewDecoder(file)
	for decoder.More() {
		var line InputLogLine
		if err := decoder.Decode(&line); err != nil {
			continue
		}

		gs.Update(line)

		currentTimeInt := int(line.Time)
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
		if strings.Contains(line.TargetName, "creep") {
			if attacker, ok := gs.Heroes[line.AttackerName]; ok && attacker.Team != gs.MyTeam {
				attacker.X, attacker.Y, attacker.Z = ToWorld(line.X), ToWorld(line.Y), line.Z
				attacker.LastSeenTime = line.Time
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

	for _, h := range gs.Heroes {
		if h.Team == gs.MyTeam && h.IsAlive {
			visionSources = append(visionSources, h)
		}
	}
	for _, t := range gs.Towers {
		if t.Team == gs.MyTeam && t.IsAlive {
			visionSources = append(visionSources, t)
			trueSightSources = append(trueSightSources, t)
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

	for _, enemy := range gs.Heroes {
		if enemy.Team == gs.MyTeam {
			continue
		}

		visibleNow := false
		if enemy.IsAlive {
			visibleNow = gs.IsUnitVisible(enemy, visionSources, obsWards, trueSightSources)
		}
		enemy.CurrentlyVisible = visibleNow

		if visibleNow {
			enemy.LastSeenX, enemy.LastSeenY, enemy.LastSeenZ = enemy.X, enemy.Y, enemy.Z
			enemy.LastSeenTime = gs.CurrentTime
		}

		if enemy.LastSeenTime > 0 {
			data := UnitVisionData{
				Name: enemy.Name, IsVisible: visibleNow, IsLastKnown: !visibleNow && enemy.IsAlive,
				NearestAllyDistance:       gs.getNearestHeroDist(enemy.X, enemy.Y, enemy.Team, true),
				NearestEnemyDistance:      gs.getNearestHeroDist(enemy.X, enemy.Y, enemy.Team, false),
				NearestAllyTowerDistance:  gs.getNearestTowerDist(enemy.X, enemy.Y, enemy.Team),
				NearestEnemyTowerDistance: gs.getNearestTowerDist(enemy.X, enemy.Y, gs.MyTeam),
				TimeFromLastSeen:          float32(gs.CurrentTime - enemy.LastSeenTime),
			}
			if visibleNow {
				data.X, data.Y, data.Z = enemy.X, enemy.Y, enemy.Z
			} else {
				data.X, data.Y, data.Z = enemy.LastSeenX, enemy.LastSeenY, enemy.LastSeenZ
			}
			data.LastSeenPosition = [3]float32{enemy.LastSeenX, enemy.LastSeenY, enemy.LastSeenZ}
			data.NearestAllyTPDistance = data.NearestAllyTowerDistance
			snapshot.Unit = append(snapshot.Unit, data)
		}
	}
	return snapshot
}

func (gs *GameState) IsUnitVisible(enemy *UnitState, visionUnits []*UnitState, obsWards []*WardState, trueSight []*UnitState) bool {
	isInvis := false
	for mod := range enemy.Modifiers {
		if strings.Contains(mod, "invisible") || strings.Contains(mod, "smoke") {
			isInvis = true
			break
		}
	}
	if isInvis {
		hasTS := false
		for _, ts := range trueSight {
			if GetDistSq(ts.X, ts.Y, enemy.X, enemy.Y) < SentryTrueSight*SentryTrueSight {
				hasTS = true
				break
			}
		}
		if !hasTS {
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

	for x := minX; x <= maxX+GridSize; x += GridSize {
		for y := minY; y <= maxY+GridSize; y += GridSize {
			idx := getGridIdx(x, y)
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
		idx := getGridIdx(tr.X, tr.Y)
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
