"""Command line interface for solving, verifying, and benchmarking."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .benchmark import benchmark_inputs, create_solver, summarize_benchmark
from .formatter import format_instance
from .parser import parse_file, parse_output
from .reporting import generate_benchmark_figures
from .solvers.verify_sat import verify_solution_with_cnf
from .utils import default_output_path, write_text
from .validator import validate_solution


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m futoshiki.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve = subparsers.add_parser("solve", help="Solve one Futoshiki puzzle.")
    solve.add_argument("--input", required=True, help="Path to input puzzle.")
    solve.add_argument(
        "--solver",
        required=True,
        choices=["bruteforce", "backtracking", "astar", "logic-fc", "logic-bc", "logic-forward", "logic-backward"],
    )
    solve.add_argument("--heuristic", default="main", choices=["main", "h0", "hweak"])
    solve.add_argument("--output", help="Optional output path.")

    bench = subparsers.add_parser("benchmark", help="Benchmark all solvers on a folder of inputs.")
    bench.add_argument("--inputs", required=True, help="Folder containing input-XX.txt files.")
    bench.add_argument("--out", required=True, help="CSV output path.")

    verify = subparsers.add_parser("verify", help="Verify a produced output file.")
    verify.add_argument("--input", required=True, help="Original input file.")
    verify.add_argument("--output", required=True, help="Solved output file.")
    return parser


def _solver_name(cli_name: str, heuristic: str) -> str:
    if cli_name == "astar":
        return "astar-main" if heuristic == "main" else f"astar-{heuristic}"
    if cli_name == "logic-fc":
        return "logic-forward"
    if cli_name == "logic-bc":
        return "logic-backward"
    return cli_name


def solve_command(args: argparse.Namespace) -> int:
    instance = parse_file(args.input)
    solver_name = _solver_name(args.solver, args.heuristic)
    solver = create_solver(solver_name)
    result = solver.solve(instance)
    if not result.solved or result.grid is None:
        print(f"[FAIL] {solver_name}: {result.message}")
        return 1
    output_text = format_instance(instance, grid=result.grid)
    output_path = Path(args.output) if args.output else default_output_path(args.input, "outputs")
    write_text(output_path, output_text)
    print(
        f"[OK] {solver_name} solved {Path(args.input).name} in "
        f"{result.stats.runtime_ms:.3f} ms -> {output_path}"
    )
    return 0


def ensure_output_exists(input_path: str, output_path: str) -> bool:
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


def benchmark_command(args: argparse.Namespace) -> int:
    rows = benchmark_inputs(args.inputs, args.out)
    summary = summarize_benchmark(rows)
    summary_path = Path(args.out).with_name("benchmark_summary.md")
    figures_dir = Path(args.out).with_name("figures")
    write_text(summary_path, summary)
    created_figures = generate_benchmark_figures(args.out, figures_dir)
    print(f"[OK] Benchmarked {len(rows)} runs -> {args.out}")
    print(f"[OK] Summary -> {summary_path}")
    print(f"[OK] Figures -> {figures_dir} ({len(created_figures)} files)")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    instance = parse_file(args.input)
    if not ensure_output_exists(args.input, args.output):
        return 1
    parsed_output = parse_output(Path(args.output).read_text(encoding="utf-8"), instance.size)
    if parsed_output.horizontal_constraints != instance.horizontal_constraints:
        print("[FAIL] Output horizontal inequality signs do not match the input.")
        return 1
    if parsed_output.vertical_constraints != instance.vertical_constraints:
        print("[FAIL] Output vertical inequality signs do not match the input.")
        return 1
    solved_grid = parsed_output.grid
    valid, errors = validate_solution(instance, solved_grid)
    verification = verify_solution_with_cnf(instance, solved_grid)
    if not valid or not verification.valid_cnf:
        print("[FAIL] Output is invalid.")
        for line in errors or verification.details:
            print(f" - {line}")
        return 1
    print(
        f"[OK] Output valid. CNF variables={verification.cnf_stats['variables']} "
        f"clauses={verification.cnf_stats['clauses']}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "solve":
        return solve_command(args)
    if args.command == "benchmark":
        return benchmark_command(args)
    if args.command == "verify":
        return verify_command(args)
    parser.error(f"Unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
