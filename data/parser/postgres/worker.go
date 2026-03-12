package postgres

import (
	"database/sql"

	"github.com/kandratt-s/ml-in-dota.git/data/parsed/utils"
)

type FullMatch struct {
	MatchId int64
	General []utils.GeneralGameState
	Items   []utils.ItemsGameState
	Vision  []utils.VisionEnemeyTeam
}

func SaveWorker(db *sql.DB, dbChan <-chan FullMatch, done chan<- bool) {

}
