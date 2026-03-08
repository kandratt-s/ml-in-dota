package utils

import (
	"fmt"
	"strings"
)

func BeautifulPrintVision(snapshot VisionEnemeyTeam) {
	fmt.Printf("\n=== TIME: %d сек | День: %v ===\n", snapshot.Time, snapshot.Time%600 < 300)
	fmt.Printf("%-20s | %-7s | %-6s | %-12s | %-12s | %-10s\n",
		"Герой", "Видим?", "Тень?", "Ближ.Союз", "Ближ.Враг", "До Тавера")
	fmt.Println(strings.Repeat("-", 85))

	for _, u := range snapshot.Unit {
		visibleStr := "НЕТ"
		if u.IsVisible {
			visibleStr = "ДА"
		}
		shadowStr := "НЕТ"
		if u.IsLastKnown {
			shadowStr = "ДА"
		}

		fmt.Printf("%-20s | %-7s | %-6s | %-12.1f | %-12.1f | %-10.1f\n",
			u.Name,
			visibleStr,
			shadowStr,
			u.NearestAllyDistance,
			u.NearestEnemyDistance,
			u.NearestAllyTowerDistance,
		)
	}
}
