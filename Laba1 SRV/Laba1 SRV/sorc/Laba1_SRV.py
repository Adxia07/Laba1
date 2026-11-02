from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

U_LIMIT = 1.0

@dataclass(frozen=True)
class Task:
    name: str
    hardness: str
    C: float
    D: float
    T: float

def slack(task: Task) -> float:
    return task.D - task.C

def is_feasible(task: Task) -> bool:
    return slack(task) >= 0

def deadline_type(task: Task) -> str:
    if task.D == task.T:
        return "не€вный"
    if task.D < task.T:
        return "ограниченный"
    else:
        return "произвольный"

def classify_system(tasks: list[Task]) -> str:
    return "жЄсткого реального времени" if any(t.hardness == "жЄсткое" for t in tasks) else "м€гкого реального времени"

def critical_task(tasks: list[Task]) -> Task | None:
    hard = [t for t in tasks if t.hardness == "жЄсткое"]
    return min(hard, key=slack) if hard else None

def required_reaction_time(tasks: list[Task]) -> float:
    hard = [t for t in tasks if t.hardness == "жЄсткое"]
    return min(t.D for t in (hard or tasks))

def utilization(tasks: list[Task]) -> float:
    return sum(t.C / t.T for t in tasks)

def classify_architecture(n_cpu: int, has_network: bool) -> str:
    if has_network:
        return "распределЄнна€"
    return "многопроцессорна€" if n_cpu > 1 else "однопроцессорна€"

def _make_task(row: dict) -> Task:
    hardness = str(row["hardness"]).strip().lower()
    if hardness not in ("жЄсткое", "твЄрдое", "м€гкое"):
        raise ValueError(f"Ќеизвестный класс жЄсткости: {row['hardness']!r}")
    task = Task(str(row["name"]).strip(), hardness, float(row["C"]), float(row["D"]), float(row["T"]))
    if task.C <= 0 or task.D <= 0 or task.T <= 0:
        raise ValueError(f"C, D, T должны быть > 0: {task.name}")
    return task

def load_json(path: Path) -> tuple[list[Task], int, bool]:
    data = json.loads(path.read_text(encoding="utf-8"))
    system = data["system"]
    tasks = [_make_task(r) for r in data["tasks"]]
    return tasks, int(system["cpus"]), bool(system["network"])