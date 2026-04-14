"""Benchmark chart generation for the project report."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def generate_benchmark_figures(csv_path: str | Path, output_dir: str | Path) -> list[str]:
    data = pd.read_csv(csv_path)
    figures_dir = Path(output_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    solver_order = [
        "bruteforce",
        "backtracking",
        "astar-h0",
        "astar-main",
        "logic-forward",
        "logic-backward",
    ]
    data["solver"] = pd.Categorical(data["solver"], categories=solver_order, ordered=True)
    data = data.sort_values(["solver", "input"])

    created: list[str] = []

    def save_current(name: str) -> None:
        path = figures_dir / name
        plt.tight_layout()
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        created.append(path.name)

    runtime_avg = data.groupby("solver", observed=True)["runtime_ms"].mean().reindex(solver_order).dropna()
    plt.figure(figsize=(8, 4.5))
    runtime_avg.plot(kind="bar", color="#1f77b4")
    plt.ylabel("Average runtime (ms)")
    plt.xlabel("Solver")
    plt.title("Average Runtime by Solver")
    plt.xticks(rotation=25, ha="right")
    save_current("runtime_avg_by_solver.png")

    runtime_pivot = data.pivot(index="input", columns="solver", values="runtime_ms").reindex(columns=solver_order)
    plt.figure(figsize=(10, 5.2))
    for solver in solver_order:
        if solver in runtime_pivot:
            plt.plot(runtime_pivot.index, runtime_pivot[solver], marker="o", label=solver)
    plt.ylabel("Runtime (ms)")
    plt.xlabel("Input")
    plt.title("Runtime by Input")
    plt.xticks(rotation=45, ha="right")
    plt.legend(ncol=2)
    save_current("runtime_by_input.png")

    nodes_avg = data.groupby("solver", observed=True)["nodes_expanded"].mean().reindex(solver_order).dropna()
    plt.figure(figsize=(8, 4.5))
    nodes_avg.plot(kind="bar", color="#2ca02c")
    plt.ylabel("Average nodes expanded")
    plt.xlabel("Solver")
    plt.title("Average Nodes Expanded by Solver")
    plt.xticks(rotation=25, ha="right")
    save_current("nodes_by_solver.png")

    inference_avg = data.groupby("solver", observed=True)["rule_firings"].mean().reindex(solver_order).dropna()
    plt.figure(figsize=(8, 4.5))
    inference_avg.plot(kind="bar", color="#d62728")
    plt.ylabel("Average inference count")
    plt.xlabel("Solver")
    plt.title("Average Rule Firings / Goals Resolved")
    plt.xticks(rotation=25, ha="right")
    save_current("inference_by_solver.png")

    astar = data[data["solver"].isin(["astar-h0", "astar-main"])].pivot(
        index="input",
        columns="solver",
        values="runtime_ms",
    )
    plt.figure(figsize=(9.5, 4.8))
    x = range(len(astar.index))
    width = 0.38
    plt.bar([value - width / 2 for value in x], astar["astar-h0"], width=width, label="astar-h0", color="#9467bd")
    plt.bar([value + width / 2 for value in x], astar["astar-main"], width=width, label="astar-main", color="#8c564b")
    plt.ylabel("Runtime (ms)")
    plt.xlabel("Input")
    plt.title("A* Heuristic Runtime Comparison")
    plt.xticks(list(x), astar.index, rotation=45, ha="right")
    plt.legend()
    save_current("astar_h0_vs_main_runtime.png")

    scale = data[["input", "size"]].drop_duplicates().sort_values("input")
    plt.figure(figsize=(9.5, 4.5))
    plt.bar(scale["input"], scale["size"] ** 2, color="#ff7f0e")
    plt.ylabel("Number of cells (N^2)")
    plt.xlabel("Input")
    plt.title("Puzzle Scale by Input")
    plt.xticks(rotation=45, ha="right")
    save_current("puzzle_scale_by_input.png")

    memory_proxy = (
        data.assign(
            memory_proxy=data[["peak_frontier", "peak_open_set", "peak_domain_size_sum"]].max(axis=1)
        )
        .groupby("solver", observed=True)["memory_proxy"]
        .mean()
        .reindex(solver_order)
        .dropna()
    )
    plt.figure(figsize=(8, 4.5))
    memory_proxy.plot(kind="bar", color="#17becf")
    plt.ylabel("Average proxy value")
    plt.xlabel("Solver")
    plt.title("Average Memory Proxy by Solver")
    plt.xticks(rotation=25, ha="right")
    save_current("memory_proxy_by_solver.png")

    return created
