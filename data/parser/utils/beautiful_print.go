//на это забей

package utils

import (
	"encoding/json"
	"fmt"
)

func BeautifulPrint[T any](data T) {
	fmt.Println("================================================================================")
	fmt.Printf("SNAPSHOT TYPE: %T\n", data)
	fmt.Println("--------------------------------------------------------------------------------")
	prettyJSON, err := json.MarshalIndent(data, "", "    ")
	if err != nil {
		fmt.Printf("Error formatting data: %v\n", err)
		return
	}

	fmt.Println(string(prettyJSON))
	fmt.Println("================================================================================\n")
}

func TestBKBcooldown(a []GeneralGameState) {
	for _, oneGeneral := range a {
		for i, hero := range oneGeneral.Heroes {
			if hero.BKBcooldown != 0 {
				fmt.Println("there is cooldown ", i, hero.HeroName)
			}
		}
	}
}

func TestCompatibility(general []GeneralGameState, vision []VisionEnemeyTeam) {
	if len(general) != len(vision) {
		fmt.Printf("Ошибка: Массивы разной длины! General: %d, Vision: %d\n", len(general), len(vision))
	}

	minLen := len(general)
	if len(vision) < minLen {
		minLen = len(vision)
	}

	for i := 0; i < minLen; i++ {
		if general[i].GameTime != vision[i].Time {
			fmt.Printf("Рассинхрон на индексе %d: GeneralTime=%d, VisionTime=%d\n",
				i, general[i].GameTime, vision[i].Time)
		}

		if i > 0 {
			expectedTime := general[i-1].GameTime + 1
			if general[i].GameTime != expectedTime {
				fmt.Printf("Дырка в General на индексе %d: ожидалось %d, получено %d\n",
					i, expectedTime, general[i].GameTime)
			}

			if vision[i].Time != vision[i-1].Time+1 {
				fmt.Printf("Дырка в Vision на индексе %d: ожидалось %d, получено %d\n",
					i, vision[i-1].Time+1, vision[i].Time)
			}
		}
	}

	fmt.Println("Проверка завершена.")
}
