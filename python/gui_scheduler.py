import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
from collections import defaultdict

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFTS = ["morning", "afternoon", "evening"]

MAX_DAYS_PER_WEEK = 5
MIN_EMP_PER_SHIFT = 2
MAX_EMP_PER_SHIFT = 3  # "full" threshold used for conflict resolution


def can_work(employee, day, assigned_by_day, days_worked):
    return (day not in assigned_by_day[employee]) and (days_worked[employee] < MAX_DAYS_PER_WEEK)


def try_assign(employee, day_index, desired_shift, schedule, assigned_by_day, days_worked):
    """
    Conflict resolution rules:
      1) Try desired shift same day (if not full)
      2) Else try other shifts same day
      3) Else try desired shift next day
      4) Else try other shifts next day
    """
    def attempt(d_idx, shift):
        day = DAYS[d_idx]
        if not can_work(employee, day, assigned_by_day, days_worked):
            return False
        if len(schedule[day][shift]) >= MAX_EMP_PER_SHIFT:
            return False
        schedule[day][shift].append(employee)
        assigned_by_day[employee].add(day)
        days_worked[employee] += 1
        return True

    # 1) same day desired
    if attempt(day_index, desired_shift):
        return True

    # 2) same day other shifts
    for sh in SHIFTS:
        if sh != desired_shift and attempt(day_index, sh):
            return True

    # 3-4) next day (if exists)
    if day_index + 1 < len(DAYS):
        next_idx = day_index + 1
        if attempt(next_idx, desired_shift):
            return True
        for sh in SHIFTS:
            if sh != desired_shift and attempt(next_idx, sh):
                return True

    return False


def fill_minimums(schedule, employees, assigned_by_day, days_worked, rng):
    """
    Ensure MIN_EMP_PER_SHIFT employees per shift per day.
    Randomly assign employees who:
      - aren't working that day already
      - haven't hit MAX_DAYS_PER_WEEK
    """
    for day in DAYS:
        for shift in SHIFTS:
            while len(schedule[day][shift]) < MIN_EMP_PER_SHIFT:
                candidates = [e for e in employees if can_work(e, day, assigned_by_day, days_worked)]
                if not candidates:
                    return  # can't fill further
                pick = rng.choice(candidates)
                schedule[day][shift].append(pick)
                assigned_by_day[pick].add(day)
                days_worked[pick] += 1


def schedule_to_text(schedule, employees, days_worked):
    lines = []
    lines.append("================ FINAL WEEK SCHEDULE ================\n")
    for day in DAYS:
        lines.append(f"{day}:")
        for shift in SHIFTS:
            ppl = schedule[day][shift]
            lines.append(f"  - {shift.title():9}: {', '.join(ppl) if ppl else '(none)'}")
        lines.append("")
    lines.append("Weekly days worked:")
    for e in employees:
        lines.append(f"  {e}: {days_worked[e]} day(s)")
    return "\n".join(lines)


class SchedulerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Employee Schedule Manager (Python GUI + Bonuses)")

        self.employees = []
        self.pref_vars = {}  # pref_vars[emp][day] = (p1var,p2var,p3var)

        outer = ttk.Frame(root, padding=10)
        outer.pack(fill="both", expand=True)

        # Top input area
        top = ttk.Frame(outer)
        top.pack(fill="x")

        ttk.Label(top, text="Employee names (one per line):").grid(row=0, column=0, sticky="w")
        self.names_text = tk.Text(top, width=40, height=6)
        self.names_text.grid(row=1, column=0, sticky="we", pady=5)

        right = ttk.Frame(top)
        right.grid(row=1, column=1, sticky="n", padx=12)

        ttk.Label(right, text="Optional random seed:").pack(anchor="w")
        self.seed_entry = ttk.Entry(right, width=14)
        self.seed_entry.pack(anchor="w", pady=(2, 8))

        ttk.Button(right, text="Load Employees", command=self.load_employees).pack(anchor="w")
        ttk.Button(right, text="Generate Schedule", command=self.generate).pack(anchor="w", pady=(8, 0))
        ttk.Button(right, text="Save Output to .txt", command=self.save_output).pack(anchor="w", pady=(8, 0))

        top.columnconfigure(0, weight=1)

        # Preferences table container
        self.prefs_frame = ttk.Frame(outer)
        self.prefs_frame.pack(fill="both", expand=True, pady=(10, 0))

        # Output
        ttk.Label(outer, text="Output (use this for screenshot):").pack(anchor="w", pady=(10, 0))
        self.output = tk.Text(outer, width=100, height=18)
        self.output.pack(fill="both", expand=True, pady=5)

        self.output.insert("end", "1) Enter employee names\n2) Click Load Employees\n3) Set ranked preferences (1st/2nd/3rd)\n4) Click Generate Schedule\n")

    def load_employees(self):
        raw = self.names_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showerror("Input Error", "Please enter at least one employee name.")
            return

        names = [n.strip() for n in raw.splitlines() if n.strip()]
        # remove duplicates while preserving order
        seen = set()
        uniq = []
        for n in names:
            if n not in seen:
                uniq.append(n)
                seen.add(n)

        self.employees = uniq
        self.pref_vars.clear()

        # rebuild preference grid
        for w in self.prefs_frame.winfo_children():
            w.destroy()

        ttk.Label(
            self.prefs_frame,
            text="Ranked Shift Preferences (Bonus): choose 1st / 2nd / 3rd for each day (no duplicates per day)."
        ).grid(row=0, column=0, columnspan=30, sticky="w", pady=(0, 8))

        # header row
        ttk.Label(self.prefs_frame, text="Employee").grid(row=1, column=0, sticky="w")
        col = 1
        for day in DAYS:
            ttk.Label(self.prefs_frame, text=day).grid(row=1, column=col, columnspan=3, padx=8)
            ttk.Label(self.prefs_frame, text="1st").grid(row=2, column=col)
            ttk.Label(self.prefs_frame, text="2nd").grid(row=2, column=col + 1)
            ttk.Label(self.prefs_frame, text="3rd").grid(row=2, column=col + 2)
            col += 3

        # employee rows
        for r, emp in enumerate(self.employees, start=3):
            ttk.Label(self.prefs_frame, text=emp).grid(row=r, column=0, sticky="w")
            self.pref_vars[emp] = {}
            col = 1
            for day in DAYS:
                p1 = tk.StringVar(value="morning")
                p2 = tk.StringVar(value="afternoon")
                p3 = tk.StringVar(value="evening")

                ttk.Combobox(self.prefs_frame, textvariable=p1, values=SHIFTS, width=10, state="readonly").grid(row=r, column=col, padx=2)
                ttk.Combobox(self.prefs_frame, textvariable=p2, values=SHIFTS, width=10, state="readonly").grid(row=r, column=col + 1, padx=2)
                ttk.Combobox(self.prefs_frame, textvariable=p3, values=SHIFTS, width=10, state="readonly").grid(row=r, column=col + 2, padx=2)

                self.pref_vars[emp][day] = (p1, p2, p3)
                col += 3

        self.output.delete("1.0", "end")
        self.output.insert("end", "Employees loaded. Now set ranked preferences and click Generate Schedule.\n")

    def validate_preferences(self):
        for emp in self.employees:
            for day in DAYS:
                p1, p2, p3 = self.pref_vars[emp][day]
                ranked = [p1.get(), p2.get(), p3.get()]
                if len(set(ranked)) != 3:
                    return False, f"{emp} has duplicate preferences on {day}. Each rank must be unique."
        return True, ""

    def generate(self):
        if not self.employees:
            messagebox.showerror("Error", "Load employees first.")
            return

        ok, msg = self.validate_preferences()
        if not ok:
            messagebox.showerror("Preference Error", msg)
            return

        seed_txt = self.seed_entry.get().strip()
        rng = random.Random(int(seed_txt)) if seed_txt else random.Random()

        # Build preferences: preferences[emp][day] = [first, second, third]
        preferences = {e: {} for e in self.employees}
        for e in self.employees:
            for day in DAYS:
                p1, p2, p3 = self.pref_vars[e][day]
                preferences[e][day] = [p1.get(), p2.get(), p3.get()]

        schedule = {day: {shift: [] for shift in SHIFTS} for day in DAYS}
        assigned_by_day = defaultdict(set)
        days_worked = defaultdict(int)

        # Phase 1: assign based on ranked preferences + conflict handling
        for day_index, day in enumerate(DAYS):
            day_order = self.employees[:]
            rng.shuffle(day_order)

            for emp in day_order:
                if days_worked[emp] >= MAX_DAYS_PER_WEEK:
                    continue
                ranked = preferences[emp][day]
                for pref_shift in ranked:
                    if try_assign(emp, day_index, pref_shift, schedule, assigned_by_day, days_worked):
                        break

        # Phase 2: fill minimum staffing
        fill_minimums(schedule, self.employees, assigned_by_day, days_worked, rng)

        out_text = schedule_to_text(schedule, self.employees, days_worked)
        self.output.delete("1.0", "end")
        self.output.insert("end", out_text)

    def save_output(self):
        text = self.output.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Nothing to Save", "Generate a schedule first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            title="Save Schedule Output"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        messagebox.showinfo("Saved", f"Saved output to:\n{path}")


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    SchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
