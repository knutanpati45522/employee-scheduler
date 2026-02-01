package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"
)

var DAYS = []string{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
var SHIFTS = []string{"morning", "afternoon", "evening"}

const MAX_DAYS_PER_WEEK = 5
const MIN_EMP_PER_SHIFT = 2
const MAX_EMP_PER_SHIFT = 3 // defines "full"

// ---------- helpers ----------

func normalize(tok string) string {
	t := strings.ToLower(strings.TrimSpace(tok))
	switch t {
	case "m":
		return "morning"
	case "a":
		return "afternoon"
	case "e":
		return "evening"
	default:
		return t
	}
}

func parseRanked(line string) []string {
	line = strings.ReplaceAll(line, ",", " ")
	parts := strings.Fields(line)

	ranked := []string{}
	seen := map[string]bool{}

	for _, p := range parts {
		sh := normalize(p)
		if (sh == "morning" || sh == "afternoon" || sh == "evening") && !seen[sh] {
			ranked = append(ranked, sh)
			seen[sh] = true
		}
	}
	for _, sh := range SHIFTS {
		if !seen[sh] {
			ranked = append(ranked, sh)
		}
	}
	if len(ranked) > 3 {
		return ranked[:3]
	}
	return ranked
}

func canWork(emp, day string, assignedByDay map[string]map[string]bool, daysWorked map[string]int) bool {
	if daysWorked[emp] >= MAX_DAYS_PER_WEEK {
		return false
	}
	if assignedByDay[emp] == nil {
		return true
	}
	return !assignedByDay[emp][day]
}

func attemptAssign(emp, day, shift string,
	schedule map[string]map[string][]string,
	assignedByDay map[string]map[string]bool,
	daysWorked map[string]int) bool {

	if !canWork(emp, day, assignedByDay, daysWorked) {
		return false
	}
	if len(schedule[day][shift]) >= MAX_EMP_PER_SHIFT {
		return false
	}
	schedule[day][shift] = append(schedule[day][shift], emp)

	if assignedByDay[emp] == nil {
		assignedByDay[emp] = map[string]bool{}
	}
	assignedByDay[emp][day] = true
	daysWorked[emp]++
	return true
}

func tryAssign(emp string, dayIndex int, desiredShift string,
	schedule map[string]map[string][]string,
	assignedByDay map[string]map[string]bool,
	daysWorked map[string]int) bool {

	day := DAYS[dayIndex]

	// 1) desired same day
	if attemptAssign(emp, day, desiredShift, schedule, assignedByDay, daysWorked) {
		return true
	}
	// 2) other shifts same day
	for _, sh := range SHIFTS {
		if sh != desiredShift {
			if attemptAssign(emp, day, sh, schedule, assignedByDay, daysWorked) {
				return true
			}
		}
	}

	// 3-4) next day
	if dayIndex+1 < len(DAYS) {
		nextDay := DAYS[dayIndex+1]
		if attemptAssign(emp, nextDay, desiredShift, schedule, assignedByDay, daysWorked) {
			return true
		}
		for _, sh := range SHIFTS {
			if sh != desiredShift {
				if attemptAssign(emp, nextDay, sh, schedule, assignedByDay, daysWorked) {
					return true
				}
			}
		}
	}

	return false
}

func fillMinimums(schedule map[string]map[string][]string, employees []string,
	assignedByDay map[string]map[string]bool, daysWorked map[string]int, rng *rand.Rand) {

	for _, day := range DAYS {
		for _, shift := range SHIFTS {
			for len(schedule[day][shift]) < MIN_EMP_PER_SHIFT {
				candidates := []string{}
				for _, e := range employees {
					if canWork(e, day, assignedByDay, daysWorked) {
						candidates = append(candidates, e)
					}
				}
				if len(candidates) == 0 {
					return
				}
				pick := candidates[rng.Intn(len(candidates))]
				_ = attemptAssign(pick, day, shift, schedule, assignedByDay, daysWorked)
			}
		}
	}
}

func printSchedule(schedule map[string]map[string][]string, employees []string, daysWorked map[string]int) {
	fmt.Println("\n================ FINAL WEEK SCHEDULE ================\n")
	for _, day := range DAYS {
		fmt.Printf("%s:\n", day)
		for _, shift := range SHIFTS {
			people := schedule[day][shift]
			if len(people) == 0 {
				fmt.Printf("  - %-9s: (none)\n", strings.Title(shift))
			} else {
				fmt.Printf("  - %-9s: %s\n", strings.Title(shift), strings.Join(people, ", "))
			}
		}
		fmt.Println()
	}

	fmt.Println("Weekly days worked:")
	for _, e := range employees {
		fmt.Printf("  %s: %d day(s)\n", e, daysWorked[e])
	}
}

// ---------- main ----------

func main() {
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Employee Scheduler (Go CLI + Preference Bonus)")

	fmt.Print("Optional random seed (press Enter to skip): ")
	seedLine, _ := reader.ReadString('\n')
	seedLine = strings.TrimSpace(seedLine)

	var rng *rand.Rand
	if seedLine != "" {
		seedInt, err := strconv.ParseInt(seedLine, 10, 64)
		if err != nil {
			fmt.Println("Invalid seed. Using current time.")
			rng = rand.New(rand.NewSource(time.Now().UnixNano()))
		} else {
			rng = rand.New(rand.NewSource(seedInt))
		}
	} else {
		rng = rand.New(rand.NewSource(time.Now().UnixNano()))
	}

	fmt.Print("Number of employees: ")
	nLine, _ := reader.ReadString('\n')
	nLine = strings.TrimSpace(nLine)
	n, err := strconv.Atoi(nLine)
	if err != nil || n <= 0 {
		fmt.Println("Invalid number of employees.")
		return
	}

	employees := make([]string, 0, n)
	for i := 0; i < n; i++ {
		fmt.Printf("Employee #%d name: ", i+1)
		name, _ := reader.ReadString('\n')
		name = strings.TrimSpace(name)
		if name == "" {
			i--
			fmt.Println("Name cannot be empty. Try again.")
			continue
		}
		employees = append(employees, name)
	}

	// preferences[emp][day] = ranked shifts
	preferences := map[string]map[string][]string{}
	fmt.Println("\nEnter ranked preferences each day (example: 'm e a' or 'morning, evening, afternoon')\n")

	for _, e := range employees {
		fmt.Printf("--- %s ---\n", e)
		preferences[e] = map[string][]string{}
		for _, day := range DAYS {
			fmt.Printf("%s: ", day)
			line, _ := reader.ReadString('\n')
			line = strings.TrimSpace(line)
			preferences[e][day] = parseRanked(line)
		}
		fmt.Println()
	}

	// schedule[day][shift] = []employees
	schedule := map[string]map[string][]string{}
	for _, day := range DAYS {
		schedule[day] = map[string][]string{}
		for _, shift := range SHIFTS {
			schedule[day][shift] = []string{}
		}
	}

	assignedByDay := map[string]map[string]bool{}
	daysWorked := map[string]int{}

	// Phase 1: preference-based assignment + conflict resolution
	for dayIndex, day := range DAYS {
		dayOrder := make([]string, len(employees))
		copy(dayOrder, employees)
		rng.Shuffle(len(dayOrder), func(i, j int) { dayOrder[i], dayOrder[j] = dayOrder[j], dayOrder[i] })

		for _, emp := range dayOrder {
			if daysWorked[emp] >= MAX_DAYS_PER_WEEK {
				continue
			}
			ranked := preferences[emp][day]
			for _, prefShift := range ranked {
				if tryAssign(emp, dayIndex, prefShift, schedule, assignedByDay, daysWorked) {
					break
				}
			}
		}
	}

	// Phase 2: fill minimum staffing per shift/day
	fillMinimums(schedule, employees, assignedByDay, daysWorked, rng)

	printSchedule(schedule, employees, daysWorked)
}
