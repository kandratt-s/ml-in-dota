package main

import (
	"fmt"
	"log"
	"runtime"
	"sync"

	"github.com/kandratt-s/ml-in-dota.git/data/parsed/postgres"
	"github.com/kandratt-s/ml-in-dota.git/data/parsed/utils"
)

func workerParse(id int, jobs <-chan string, dbChan chan<- postgres.FullMatch, wq *sync.WaitGroup) {
	for filePath := range jobs {
		fmt.Printf("Воркер #%d взял матч: %s\n", id, filePath)
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

	visionChan := make(chan []utils.VisionEnemeyTeam, 1)
	itemsChan := make(chan []utils.ItemsGameState, 1)
	generalChan := make(chan []utils.GeneralGameState, 1)
	errChan := make(chan error, 3)

	wgParse.Add(3)

	go func() {
		defer wgParse.Done()
		data, err := utils.ParseVisionWorker(filePath, 2)
		if err != nil {
			errChan <- err
			return
		}
		visionChan <- data
	}()

	go func() {
		defer wgParse.Done()
		data, err := utils.ParseItemsWorker(filePath)
		if err != nil {
			errChan <- err
			return
		}
		itemsChan <- data
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
		wgParse.Wait()
		close(visionChan)
		close(itemsChan)
		close(generalChan)
		close(errChan)
	}()

	for err := range errChan {
		if err != nil {
			log.Printf("Ошибка в матче %s: %v", filePath, err)
			return postgres.FullMatch{}, err
		}
	}

	visionData := <-visionChan
	itemData := <-itemsChan
	generalData := <-generalChan

	return postgres.FullMatch{
		MatchId: generalData[0].MatchID,
		General: generalData,
		Items:   itemData,
		Vision:  visionData,
	}, nil

}

func main() {
	db := postgres.ConnectDB()
	if db == nil {
		fmt.Printf("ne udalos conn db")
		return
	}
	defer db.Close()

	dbChan := make(chan postgres.FullMatch, 20)
	dbDone := make(chan bool)

	go postgres.SaveWorker(db, dbChan, dbDone)

	numWorkers := runtime.NumCPU()
	jobs := make(chan string, 1000)
	var wq sync.WaitGroup

	for w := 1; w <= numWorkers; w++ {
		go workerParse(w, jobs, dbChan, &wq)
	}

	for i := 0; i < 1000; i++ {
		filePath := "input_json/8654087914_parsed.jsonl"
		wq.Add(1)
		jobs <- filePath
	}
	close(jobs)

	wq.Wait()

	close(dbChan)
	<-dbDone
}
