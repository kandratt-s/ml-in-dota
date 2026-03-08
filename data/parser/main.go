package main

import (
	"fmt"
	"log"
	"runtime"
	"sync"

	"github.com/kandratt-s/ml-in-dota.git/data/parsed/utils"
)

// worker — это "рабочий", который берет задачу из канала и выполняет её
func worker(id int, jobs <-chan string, wq *sync.WaitGroup) {
	for filePath := range jobs {
		fmt.Printf("Воркер #%d взял матч: %s\n", id, filePath)
		makeOneMatch(filePath)
		wq.Done()
	}
}

func makeOneMatch(filePath string) {
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
			return
		}
	}

	visionData := <-visionChan
	itemData := <-itemsChan
	generalData := <-generalChan

	// Здесь будет твоя логика объединения данных (сшивка по game_time)

	fmt.Print(visionData[1000], itemData[1000], generalData[1000])

}

func main() {
	numWorkers := runtime.NumCPU()
	fmt.Printf("Запуск пула на %d воркеров\n", numWorkers)

	jobs := make(chan string, 1000)
	var wq sync.WaitGroup

	for w := 1; w <= numWorkers; w++ {
		go worker(w, jobs, &wq)
	}

	for i := 0; i < 1000; i++ {
		filePath := "input_json/8654087914_parsed.jsonl"
		wq.Add(1)
		jobs <- filePath
	}
	close(jobs)

	wq.Wait()
}
