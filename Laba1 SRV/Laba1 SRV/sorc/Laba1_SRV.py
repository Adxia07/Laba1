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
# Функции
def slack(task: Task) -> float:
    return task.D - task.C

def is_feasible(task: Task) -> bool:
    return slack(task) >= 0

def deadline_type(task: Task) -> str:
    if task.D == task.T:
        return "неявный"
    if task.D < task.T:
        return "ограниченный"
    else:
        return "произвольный"

def classify_system(tasks: list[Task]) -> str:
    return "жёсткого реального времени" if any(t.hardness == "жёсткое" for t in tasks) else "мягкого реального времени"

def critical_task(tasks: list[Task]) -> Task | None:
    hard = [t for t in tasks if t.hardness == "жёсткое"]
    return min(hard, key=slack) if hard else None

def required_reaction_time(tasks: list[Task]) -> float:
    hard = [t for t in tasks if t.hardness == "жёсткое"]
    return min(t.D for t in (hard or tasks))

def utilization(tasks: list[Task]) -> float:
    return sum(t.C / t.T for t in tasks)

def classify_architecture(n_cpu: int, has_network: bool) -> str:
    if has_network:
        return "распределённая"
    return "многопроцессорная" if n_cpu > 1 else "однопроцессорная"
# Ввод данных
def _make_task(row: dict) -> Task:
    hardness = str(row["hardness"]).strip().lower()
    if hardness not in ("жёсткое", "твёрдое", "мягкое"):
        raise ValueError(f"Неизвестный класс жёсткости: {row['hardness']!r}")
    task = Task(str(row["name"]).strip(), hardness, float(row["C"]), float(row["D"]), float(row["T"]))
    if task.C <= 0 or task.D <= 0 or task.T <= 0:
        raise ValueError(f"C, D, T должны быть > 0: {task.name}")
    return task

def load_json(path: Path) -> tuple[list[Task], int, bool]:
    data = json.loads(path.read_text(encoding="utf-8"))
    system = data["system"]
    tasks = [_make_task(r) for r in data["tasks"]]
    return tasks, int(system["cpus"]), bool(system["network"])
# Вывод данных
def _fmt(x: float) -> str:
    return f"{x:g}"

def print_table(tasks: list[Task]) -> None:
    headers = ["Задача", "Класс", "C", "D", "T", "L", "Выполнимо", "Тип дедлайна"]
    rows = [[t.name, t.hardness, _fmt(t.C), _fmt(t.D), _fmt(t.T), _fmt(slack(t)), "да" if is_feasible(t) else "нет", deadline_type(t)] for t in tasks]
    widths = [max(len(r[i]) for r in [headers] + rows) for i in range(len(headers))]
    line = "-+-".join("-" * w for w in widths)
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print(line)
    for r in rows:
        print(" | ".join(c.ljust(w) for c, w in zip(r, widths)))

def print_conclusion(tasks: list[Task], n_cpu: int, has_network: bool) -> None:
    crit = critical_task(tasks)
    u = utilization(tasks)
    all_ok = all(is_feasible(t) for t in tasks)
    print("\nВЫВОД")
    print(f"Класс системы: {classify_system(tasks)}")
    print(f"Архитектура: {classify_architecture(n_cpu, has_network)}")
    if crit:
        print(f"Критическая задача: «{crit.name}» (L = {_fmt(slack(crit))} мс)")
    else:
        print("Критическая задача: нет (жёстких задач в системе нет)")
    print(f"Требуемое время реакции R_треб = {_fmt(required_reaction_time(tasks))} мс")
    terms = " + ".join(f"{t.C / t.T:.2f}" for t in tasks)
    print(f"Коэффициент загрузки U = {terms} = {u:.2f} "
          f"({'≤' if u <= U_LIMIT else '>'} {U_LIMIT:g})")
    print("Дедлайны всех задач выполнимы (L ≥ 0)." if all_ok else "Есть задачи с невыполнимым дедлайном (L < 0): " + ", ".join(t.name for t in tasks if not is_feasible(t)))
    print("Необходимое условие U ≤ 1 " + ("выполнено." if u <= U_LIMIT else "НЕ выполнено."))

def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Классификация СРВ и расчёт времени реакции")
    p.add_argument("file", type=Path, help="JSON файл варианта")
    args = p.parse_args(argv)
    
    if args.file.suffix.lower() != ".json":
        p.error("Поддерживаются только файлы с расширением .json")
        
    tasks, n_cpu, has_net = load_json(args.file)
    if not tasks:
        p.error("в файле нет задач")
        
    print_table(tasks)
    print_conclusion(tasks, n_cpu, has_net)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())