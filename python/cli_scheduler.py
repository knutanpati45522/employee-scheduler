import random
from collections import defaultdict

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFTS = ["morning", "afternoon", "evening"]

MAX_DAYS_PER_WEEK = 5
MIN_EMP_PER_SHIFT = 2
MAX_EMP_PER_SHIFT = 3


def normalize(tok: str) -> str:
    t = tok.strip().lower()
    return {"m": "morning", "a": "afternoon", "e": "evening"}.get(t, t)


def parse_ranked(line: str):
    line = line.replace(",", " ")
    parts = [normalize(x) for x in line.split()]
    ranked = []
    for p in parts:
        if p in SHIFTS and p not in ranked:
            ranked.append(p)
    for sh in SHIFTS:
        if sh not in ranked:
            ranked.append(sh)
    return ranked[:3]


def can_work(emp, day, assigned_by_day, days_worked):
    return (day not in assigned_by_day[emp]) and (days_worked[emp] < MAX_DAYS_PER_WEEK)


def try_assign(emp, day_index, desired_shift, schedule, assigned_by_day, days_worked):
    def attempt(d_idx, shift):
        day = DAYS[d_idx]
        if not can_work(emp, day, assigned_by_day, days_worked):
            return False
        if len(schedule[day][shift]) >= MAX_EMP_PER_SHIFT:
            return False
        schedule[day][shift].append(emp)
        assigned_by_day[emp].add(day)
        days_worked[emp] += 1
        return True

    if attempt(day_index, desired_shift):
        return True
    for sh in SHIFTS:
        if sh != desired_shift and attempt(day_index, sh):
            return True

    if day_index + 1 < len(DAYS):
        next_idx = day_index + 1
        if attempt(next_idx, desired_shift):
            return True
        for sh in SHIFTS:
            if sh != desired_shift and attempt(next_idx, sh):
                return True
    return False


def fill_minimums(schedule, employees, assigned_by_day, days_worked, rng):
    for day in DAYS:
        for shift in SHIFTS:
            while len(schedule[day][shift]) < MIN_EMP_PER_SHIFT:
                candidates = [e for e in employees if can_work(e, day, assigned_by_day, days_worked)]
                if not candidates:
                    return
                pick = rng.choice(candidates)
                schedule[day][shift].append(pick)
                assigned_by_day[pick].add(day)
                days_worked[pick] += 1


def print_schedule(schedule, employees, days_worked):
    print("\n================ FINAL WEEK SCHEDULE ================\n")
    for day in DAYS:
        print(f"{day}:")
        for shift in SHIFTS:
            ppl = schedule[day][shift]
            print(f"  - {shift.title():9}: {', '.join(ppl) if ppl else '(none)'}")
        print()
    print("Weekly days worked:")
    for e in employees:
        print(f"  {e}: {days_worked[e]} day(s)")


def main():
    print("Employee Scheduler (Python CLI)")
    seed_in = input("Optional random seed (Enter to skip): ").strip()
    rng = random.Random(int(seed_in)) if seed_in else random.Random()

    n = int(input("Number of employees: ").strip())
    employees = []
    for i in range(n):
        employees.append(input(f"Employee #{i+1} name: ").strip())

    preferences = {e: {} for e in employees}
    print("\nEnter ranked preferences per day (example: 'm e a' or 'morning, evening, afternoon')\n")
    for e in employees:
        print(f"--- {e} ---")
        for day in DAYS:
            preferences[e][day] = parse_ranked(input(f"{day}: ").strip())
        print()

    schedule = {day: {shift: [] for shift in SHIFTS} for day in DAYS}
    assigned_by_day = defaultdict(set)
    days_worked = defaultdict(int)

    for day_index, day in enumerate(DAYS):
        day_order = employees[:]
        rng.shuffle(day_order)
        for e in day_order:
            if days_worked[e] >= MAX_DAYS_PER_WEEK:
                continue
            for pref_shift in preferences[e][day]:
                if try_assign(e, day_index, pref_shift, schedule, assigned_by_day, days_worked):
                    break

    fill_minimums(schedule, employees, assigned_by_day, days_worked, rng)
    print_schedule(schedule, employees, days_worked)


if __name__ == "__main__":
    main()
