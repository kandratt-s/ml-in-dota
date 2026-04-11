package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"

	"github.com/kandratt-s/ml-in-dota.git/data/parsed/postgres"
	"github.com/kandratt-s/ml-in-dota.git/data/parsed/utils"
)

func workerParse(id int, jobs <-chan string, dbChan chan<- postgres.FullMatch, wq *sync.WaitGroup) {
	for filePath := range jobs {

		fmt.Println("воркер ", id, "взял задачу")

		fm, err := makeOneMatch(filePath)

		if err != nil {
			fmt.Print("ne poluchilos u make one match main26")
		} else {
			dbChan <- fm
		}

		wq.Done()
	}
}

func makeOneMatch(filePath string) (postgres.FullMatch, error) {
	var wgParse sync.WaitGroup

	visionChanDire := make(chan []utils.VisionEnemeyTeam, 1)
	visionChanRadiant := make(chan []utils.VisionEnemeyTeam, 1)
	generalChan := make(chan []utils.GeneralGameState, 1)
	errChan := make(chan error, 3)

	wgParse.Add(3)

	go func() {
		defer wgParse.Done()
		data, err := utils.ParseVisionWorker(filePath, 3) // 2-radiant
		if err != nil {
			errChan <- err
			return
		}
		visionChanDire <- data
	}()

	go func() {
		defer wgParse.Done()
		data, err := utils.ParseGeneralWorker(filePath)
		if err != nil {
			errChan <- err
			return
		}
		generalChan <- data
	}()

	go func() {
		defer wgParse.Done()
		data, err := utils.ParseVisionWorker(filePath, 2) // 3 - dire
		if err != nil {
			errChan <- err
			return
		}
		visionChanRadiant <- data
	}()

	go func() {
		wgParse.Wait()
		close(visionChanRadiant)
		close(visionChanDire)
		close(generalChan)
		close(errChan)
	}()

	for err := range errChan {
		if err != nil {
			log.Printf("Ошибка в матче %s: %v", filePath, err)
			return postgres.FullMatch{}, err
		}
	}

	visionDataRadiant := <-visionChanRadiant
	visionDataDire := <-visionChanDire
	generalData := <-generalChan

	// utils.BeautifulPrint(generalData[3072])
	// utils.TestBKBcooldown(generalData)
	// fmt.Println(len(generalData))
	// utils.TestCompatibility(generalData, visionDataDire)

	return postgres.FullMatch{
		MatchId:       generalData[0].MatchID,
		General:       generalData,
		VisionRadiant: visionDataRadiant,
		VisionDire:    visionDataDire,
	}, nil

}

func main() {
	dbURL := os.Getenv("DB_URL")
	if dbURL == "" {
		dbURL = "postgres://app:appass@localhost:5432/app_db?sslmode=disable"
	}

	db := postgres.ConnectDB(dbURL)
	if db == nil {
		fmt.Printf("ne udalos conn db")
		return
	}
	defer db.Close()

	dbChan := make(chan postgres.FullMatch, 20)
	dbDone := make(chan bool)

	go postgres.SaveWorker(db, dbChan, dbDone)

	matchesDir := os.Getenv("MATCHES_DIR")
	if matchesDir == "" {
		matchesDir = "/data"
	}

	files, err1 := os.ReadDir(matchesDir)
	if err1 != nil {
		log.Fatalf("Критическая ошибка: не удалось прочитать папку %s: %v", matchesDir, err1)
	}

	err := utils.LoadGameData(
		"dotadata/heroStats.json",
		"dotadata/items.json",
		"dotadata/abilities.json",
		"dotadata/hero_abilities.json",
	)
	if err != nil {
		log.Fatal(err)
	}

	numWorkers := runtime.NumCPU()
	jobs := make(chan string, 1000)
	var wq sync.WaitGroup

	for w := 1; w <= numWorkers; w++ {
		go workerParse(w, jobs, dbChan, &wq)
	}

	for _, file := range files {
		if !file.IsDir() && (strings.HasSuffix(file.Name(), ".json") || strings.HasSuffix(file.Name(), ".jsonl")) {
			filePath := filepath.Join(matchesDir, file.Name())
			wq.Add(1)
			jobs <- filePath
		}
	}
	close(jobs)

	wq.Wait()

	close(dbChan)
	<-dbDone
}
