Employee Schedule Manager (Python GUI + Go CLI) — With Bonus Points

This repo contains an employee scheduling application implemented in **two distinct languages**:
- **Python** (includes a **GUI** using Tkinter) ✅ GUI Bonus
- **Go** (CLI version) ✅ Second language contrast

It demonstrates control structures (conditionals, loops, branching), data structures, and scheduling logic.

---

Requirements Implemented

Core Rules
- Company operates **7 days/week**
- Shifts per day: **Morning / Afternoon / Evening**
- **No employee works more than one shift per day**
- **Max 5 days/week per employee**
- **At least 2 employees per shift per day**
  - If fewer than 2 are available, the program **randomly assigns** additional eligible employees (who have not worked 5 days and are not already assigned that day).

### Conflict Resolution
If an employee’s preferred shift is **full** for a day:
1. assign them to another available shift **same day**
2. otherwise assign them to the **next day** (same logic)

To define “full”, both implementations use:
- `MAX_EMP_PER_SHIFT = 3`

---

## Bonus Features

### ✅ GUI Implementation — Python
- File: `python/gui_scheduler.py`
- Tkinter GUI handles:
  - employee name input
  - ranked preferences input (1st/2nd/3rd for every day)
  - validation (no duplicate ranking per day)
  - output display in GUI (ready for screenshot submission)
  - optional save output to `.txt`

### ✅ Shift Preference Handling — Python + Go
Employees specify **ranked preferences**:
- 1st preference, 2nd preference, 3rd preference

Scheduling tries:
1) 1st choice  
2) if conflict/full → 2nd choice  
3) if conflict/full → 3rd choice  
4) if none work on that day → attempt next day (same preference order)  
Then minimum staffing is enforced.

---

## How to Run

## Python GUI
```bash
cd python
python gui_scheduler.py

cd python
python cli_scheduler.py

cd go
go run main.go
