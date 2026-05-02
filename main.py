from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from futoshiki.benchmark import benchmark_inputs, create_solver, summarize_benchmark
from futoshiki.formatter import format_instance
from futoshiki.parser import parse_file, parse_output
from futoshiki.reporting import generate_benchmark_figures
from futoshiki.solvers.verify_sat import verify_solution_with_cnf
from futoshiki.utils import write_text
from futoshiki.validator import validate_solution


USAGE = """Usage:
  python main.py
  python main.py ui
  python main.py <input_path> <output_path> <solver> [heuristic]
  python main.py verify <input_path> <output_path>
  python main.py benchmark <inputs_dir> <out_csv>

Examples:
  python main.py
  python main.py inputs/input-01.txt outputs/output-01.txt backtracking
  python main.py inputs/input-01.txt outputs/output-01.txt astar main
  python main.py verify inputs/input-01.txt outputs/output-01.txt
  python main.py benchmark inputs reports/benchmark_results.csv
"""


def _launch_ui() -> int:
    app_path = PROJECT_ROOT / "src" / "futoshiki" / "ui" / "streamlit_app.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app_path)])


def _resolve_solver_name(name: str, heuristic: str) -> str:
    if name == "astar":
        return "astar-main" if heuristic == "main" else f"astar-{heuristic}"
    if name == "logic-fc":
        return "logic-forward"
    if name == "logic-bc":
        return "logic-backward"
    return name


def _solve(input_path: str, output_path: str, solver_name: str, heuristic: str = "main") -> int:
    instance = parse_file(input_path)
    solver = create_solver(_resolve_solver_name(solver_name, heuristic))
    result = solver.solve(instance)
    if not result.solved or result.grid is None:
        print(f"[FAIL] {solver_name}: {result.message}")
        return 1
    write_text(output_path, format_instance(instance, grid=result.grid))
    print(f"[OK] Solved {Path(input_path).name} -> {output_path}")
    return 0


def _ensure_output_exists(input_path: str, output_path: str) -> bool:
    target = Path(output_path)
    if target.exists():
        return True
    instance = parse_file(input_path)
    solver = create_solver("backtracking")
    result = solver.solve(instance)
    if not result.solved or result.grid is None:
        print(f"[FAIL] Could not auto-create missing output: {result.message}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    write_text(target, format_instance(instance, grid=result.grid))
    print(f"[INFO] Output file was missing; generated {target} with backtracking.")
    return True


def _verify(input_path: str, output_path: str) -> int:
    instance = parse_file(input_path)
    if not _ensure_output_exists(input_path, output_path):
        return 1
    parsed = parse_output(Path(output_path).read_text(encoding="utf-8"), instance.size)
    if parsed.horizontal_constraints != instance.horizontal_constraints:
        print("[FAIL] Output horizontal inequality signs do not match the input.")
        return 1
    if parsed.vertical_constraints != instance.vertical_constraints:
        print("[FAIL] Output vertical inequality signs do not match the input.")
        return 1
    valid, errors = validate_solution(instance, parsed.grid)
    verification = verify_solution_with_cnf(instance, parsed.grid)
    if not valid or not verification.valid_cnf:
        print("[FAIL] Output is invalid.")
        for line in errors or verification.details:
            print(f" - {line}")
        return 1
    print("[OK] Output is valid.")
    return 0


def _benchmark(inputs_dir: str, out_csv: str) -> int:
    rows = benchmark_inputs(inputs_dir, out_csv)
    summary_path = Path(out_csv).with_name("benchmark_summary.md")
    figures_dir = Path(out_csv).with_name("figures")
    write_text(summary_path, summarize_benchmark(rows))
    generate_benchmark_figures(out_csv, figures_dir)
    print(f"[OK] Benchmarked {len(rows)} runs -> {out_csv}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"ui", "app"}:
        return _launch_ui()
    if args[0] == "verify" and len(args) == 3:
        return _verify(args[1], args[2])
    if args[0] == "benchmark" and len(args) == 3:
        return _benchmark(args[1], args[2])
    if len(args) in {3, 4}:
        heuristic = args[3] if len(args) == 4 else "main"
        return _solve(args[0], args[1], args[2], heuristic)
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
