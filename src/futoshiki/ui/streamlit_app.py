"""Local Streamlit UI for the Futoshiki project."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from futoshiki.benchmark import BENCHMARK_SPECS, benchmark_inputs, create_solver, summarize_benchmark
from futoshiki.formatter import format_instance
from futoshiki.logic.backward_chaining import BackwardChainer, extract_constant_answers
from futoshiki.logic.cnf import encode_instance_to_cnf
from futoshiki.logic.predicates import atom
from futoshiki.logic.terms import var
from futoshiki.models import PuzzleInstance, SolverResult
from futoshiki.parser import PuzzleFormatError, parse_text
from futoshiki.propagation import clone_domains, initialize_domains, propagate
from futoshiki.solvers.logic_backward_solver import build_snapshot_program
from futoshiki.validator import validate_instance

st.set_page_config(page_title="Futoshiki Logic", page_icon="[]", layout="wide")


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
        .board { display: grid; gap: 0.35rem; justify-content: start; margin-top: 0.75rem; }
        .cell {
            width: 58px; height: 58px; display: flex; align-items: center; justify-content: center;
            border-radius: 12px; font-size: 1.55rem; font-weight: 700; border: 1px solid #334155;
            background: #0f172a; color: #e2e8f0;
        }
        .cell.given { background: #1e293b; color: #f8fafc; }
        .cell.inferred { background: #0b3b2e; }
        .cell.branch { background: #3b280b; }
        .cell.conflict { background: #4c1d1d; }
        .sign {
            width: 26px; height: 58px; display: flex; align-items: center; justify-content: center;
            font-size: 1.35rem; color: #a5b4fc; font-weight: 700;
        }
        .vsign {
            width: 58px; height: 24px; display: flex; align-items: center; justify-content: center;
            font-size: 1.15rem; color: #93c5fd; font-weight: 700;
        }
        .dot { width: 26px; height: 24px; }
        .panel-note {
            padding: 0.9rem 1rem; border-radius: 12px; background: rgba(15,23,42,0.72); border: 1px solid #334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _default_input_path() -> Path | None:
    candidates = sorted(Path.cwd().glob("inputs/input-*.txt"))
    return candidates[0] if candidates else None


def _load_default_text() -> str:
    path = _default_input_path()
    if path:
        return path.read_text(encoding="utf-8")
    return "\n".join(
        [
            "4",
            "0, 0, 0, 0",
            "0, 0, 0, 0",
            "0, 0, 0, 0",
            "0, 0, 0, 0",
            "0, 0, 0",
            "0, 0, 0",
            "0, 0, 0",
            "0, 0, 0",
            "0, 0, 0, 0",
            "0, 0, 0, 0",
            "0, 0, 0, 0",
        ]
    )


def _render_board(instance: PuzzleInstance, result: SolverResult | None = None) -> None:
    use_result_grid = (
        result is not None
        and result.grid is not None
        and len(result.grid) == instance.size
        and all(len(row) == instance.size for row in result.grid)
    )
    grid = result.grid if use_result_grid else instance.grid
    origins = result.assignment_origins if result else {}
    html = [f'<div class="board" style="grid-template-columns: repeat({instance.size * 2 - 1}, auto);">']
    for r in range(instance.size):
        for c in range(instance.size):
            cell = (r, c)
            value = grid[r][c]
            css = "cell"
            if instance.grid[r][c] != 0:
                css += " given"
            elif origins.get(cell) == "branch":
                css += " branch"
            elif value != 0:
                css += " inferred"
            html.append(f'<div class="{css}">{value if value != 0 else ""}</div>')
            if c < instance.size - 1:
                symbol = {0: "", 1: "&lt;", -1: "&gt;"}[instance.horizontal_constraints[r][c]]
                html.append(f'<div class="sign">{symbol}</div>')
        if r < instance.size - 1:
            for c in range(instance.size):
                symbol = {0: "", 1: "v", -1: "^"}[instance.vertical_constraints[r][c]]
                html.append(f'<div class="vsign">{symbol}</div>')
                if c < instance.size - 1:
                    html.append('<div class="dot"></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _solver_help(name: str) -> str:
    texts = {
        "backtracking": "MRV + degree heuristic with forward checking and AC-3. This is the main reference solver.",
        "astar": "A* over propagated domains. `g(s)` counts branching decisions, `h(s)` is an admissible lower bound from unresolved components.",
        "bruteforce": "Naive left-to-right, top-to-bottom enumeration. Included as a slow baseline.",
        "logic-fc": "Ground Horn KB with agenda-based forward chaining. Falls back to search only if pure inference stops early.",
        "logic-bc": "SLD-style backward chaining queries `Val(i,j,?)` and `Possible(i,j,?)`, then falls back to search if needed.",
    }
    return texts[name]


def _parse_current_text(text: str) -> PuzzleInstance:
    return parse_text(text, name="editor")


def _text_key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _result_key(result: SolverResult | None) -> str:
    if result is None:
        return "none"
    if result.grid is not None:
        return str(tuple(tuple(row) for row in result.grid))
    if result.domains is not None:
        return str(tuple((cell, tuple(sorted(values))) for cell, values in sorted(result.domains.items())))
    return result.message


def _program_stats(instance: PuzzleInstance) -> dict[str, int]:
    n = instance.size
    givens = sum(1 for row in instance.grid for value in row if value != 0)
    nonzero_h = sum(1 for row in instance.horizontal_constraints for value in row if value != 0)
    nonzero_v = sum(1 for row in instance.vertical_constraints for value in row if value != 0)
    facts = (n**3) + givens + nonzero_h + nonzero_v + (n * (n - 1) // 2)

    value_rules = (n**3) * (n + 3)
    row_rules = n**4
    col_rules = n**4
    inequality_rules = 4 * (n**2) * ((n**2) - 1)
    contradiction_rules = (2 * (n**4)) + (2 * (n**3)) - (2 * (n**2))

    return {
        "facts": facts,
        "rules": value_rules + row_rules + col_rules + inequality_rules + contradiction_rules,
    }


def _build_backward_query_program(
    instance: PuzzleInstance,
    result: SolverResult | None,
):
    domains = None
    if result is not None and result.domains is not None:
        if all(cell in result.domains for cell in ((r, c) for r in range(instance.size) for c in range(instance.size))):
            domains = clone_domains(result.domains)
    if domains is None:
        propagated = propagate(
            instance,
            initialize_domains(instance),
            use_forward_checking=False,
            use_ac3=True,
            trace_enabled=False,
        )
        domains = propagated.domains
    program = build_snapshot_program(instance, domains)
    return program, domains, sum(len(values) for values in domains.values())


def _trace_text(result: SolverResult | None, limit: int = 250) -> str:
    if result is None:
        return ""
    lines = [f"[{event.category}] {event.message}" for event in result.trace[:limit]]
    if len(result.trace) > limit:
        lines.append(f"... showing first {limit} / {len(result.trace)} events")
    return "\n".join(lines)


def main() -> None:
    _inject_css()
    st.title("Futoshiki Logic Project")
    st.caption("CLI-grade solvers, logic engines, CNF statistics, and a local Streamlit interface.")

    if "editor_text" not in st.session_state:
        st.session_state.editor_text = _load_default_text()
    if "last_editor_text" not in st.session_state:
        st.session_state.last_editor_text = st.session_state.editor_text
    if "result" not in st.session_state:
        st.session_state.result = None
    if "solve_cache" not in st.session_state:
        st.session_state.solve_cache = {}
    if "run_all_cache" not in st.session_state:
        st.session_state.run_all_cache = {}
    if "query_cache" not in st.session_state:
        st.session_state.query_cache = {}
    if "query_message" not in st.session_state:
        st.session_state.query_message = ""
    if "benchmark_rows" not in st.session_state:
        st.session_state.benchmark_rows = None
    if "benchmark_summary" not in st.session_state:
        st.session_state.benchmark_summary = ""
    if "cnf_stats_cache" not in st.session_state:
        st.session_state.cnf_stats_cache = {}

    left, right = st.columns([1.2, 1.8], gap="large")

    with left:
        st.subheader("Input")
        input_files = sorted(Path.cwd().glob("inputs/input-*.txt"))
        options = ["Editor only"] + [path.name for path in input_files]
        selected = st.selectbox("Choose bundled input", options)
        if selected != "Editor only":
            st.session_state.editor_text = Path("inputs") / selected
            st.session_state.editor_text = Path(st.session_state.editor_text).read_text(encoding="utf-8")
        uploaded = st.file_uploader("Upload a puzzle file", type=["txt"])
        if uploaded is not None:
            st.session_state.editor_text = uploaded.getvalue().decode("utf-8")
        st.session_state.editor_text = st.text_area(
            "Puzzle editor",
            value=st.session_state.editor_text,
            height=360,
        )
        if st.session_state.editor_text != st.session_state.last_editor_text:
            st.session_state.result = None
            st.session_state.query_message = ""
            st.session_state.last_editor_text = st.session_state.editor_text

        solver_name = st.selectbox(
            "Solver",
            ["backtracking", "astar", "bruteforce", "logic-fc", "logic-bc"],
            index=0,
        )
        heuristic = st.selectbox("A* heuristic", ["main", "h0", "hweak"], index=0)
        st.markdown(f'<div class="panel-note">{_solver_help(solver_name)}</div>', unsafe_allow_html=True)

        run_col, all_col, validate_col, reset_col = st.columns(4)
        run_clicked = run_col.button("Run", width="stretch")
        run_all_clicked = all_col.button("Run All", width="stretch")
        validate_clicked = validate_col.button("Validate", width="stretch")
        reset_clicked = reset_col.button("Reset", width="stretch")

        if reset_clicked:
            st.session_state.editor_text = _load_default_text()
            st.session_state.result = None
            st.rerun()

    try:
        instance = _parse_current_text(st.session_state.editor_text)
        puzzle_key = _text_key(st.session_state.editor_text)
        is_valid_instance, instance_errors = validate_instance(instance)
        current_result = st.session_state.result
        if (
            current_result is not None
            and current_result.grid is not None
            and (
                len(current_result.grid) != instance.size
                or any(len(row) != instance.size for row in current_result.grid)
            )
        ):
            st.session_state.result = None
    except PuzzleFormatError as exc:
        instance = None
        puzzle_key = ""
        is_valid_instance = False
        instance_errors = [str(exc)]

    with right:
        solve_tab, logs_tab, benchmark_tab, theory_tab = st.tabs(["Board", "Logs", "Benchmark", "Theory"])

        with solve_tab:
            if instance is None:
                st.error("\n".join(instance_errors))
            else:
                if validate_clicked:
                    if is_valid_instance:
                        st.success("Input format and local constraints are valid.")
                    else:
                        st.error("\n".join(instance_errors))

                if run_clicked and is_valid_instance:
                    solver_key = "astar-main" if solver_name == "astar" and heuristic == "main" else solver_name
                    if solver_name == "astar" and heuristic != "main":
                        solver_key = f"astar-{heuristic}"
                    cache_key = f"{puzzle_key}|{solver_key}"
                    cached_result = st.session_state.solve_cache.get(cache_key)
                    if cached_result is None:
                        with st.spinner(f"Running {solver_key}..."):
                            solver = create_solver(solver_key)
                            if solver_name == "astar":
                                solver = create_solver(f"astar-{heuristic}" if heuristic != "main" else "astar-main")
                            cached_result = solver.solve(instance)
                            st.session_state.solve_cache[cache_key] = cached_result
                    st.session_state.result = cached_result
                if run_all_clicked and is_valid_instance:
                    all_results = st.session_state.run_all_cache.get(puzzle_key)
                    if all_results is None:
                        with st.spinner("Running all solvers for the current puzzle..."):
                            all_results = []
                            for spec in BENCHMARK_SPECS:
                                solver = create_solver(spec.name)
                                result = solver.solve(instance)
                                all_results.append(
                                    {
                                        "solver": spec.name,
                                        "solved": result.solved,
                                        "runtime_ms": round(result.stats.runtime_ms, 3),
                                        "nodes": result.stats.nodes_expanded,
                                        "rule_firings": result.stats.rule_firings,
                                    }
                                )
                            st.session_state.run_all_cache[puzzle_key] = all_results
                    st.dataframe(all_results, width="stretch")
                _render_board(instance, st.session_state.result)
                result = st.session_state.result
                if result is not None:
                    stats = result.stats
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Runtime (ms)", f"{stats.runtime_ms:.3f}")
                    c2.metric("Nodes", stats.nodes_expanded)
                    c3.metric("Propagations", stats.propagations)
                    c4.metric("Rule firings", stats.rule_firings)
                    c5.metric("Contradictions", stats.contradictions)
                    c6, c7, c8 = st.columns(3)
                    c6.metric("Depth", stats.depth)
                    c7.metric("Peak frontier", max(stats.peak_frontier, stats.peak_open_set))
                    c8.metric("Peak domain sum", stats.peak_domain_size_sum)
                    if result.grid is not None:
                        output_text = format_instance(instance, grid=result.grid)
                        st.download_button(
                            "Export Output",
                            output_text,
                            file_name="output.txt",
                            mime="text/plain",
                            width="stretch",
                        )

                st.subheader("Logic Query")
                query_cols = st.columns(3)
                query_r = query_cols[0].number_input("Row", min_value=1, max_value=instance.size, value=1)
                query_c = query_cols[1].number_input("Col", min_value=1, max_value=instance.size, value=1)
                run_query = query_cols[2].button("Ask Val(i,j,?)", width="stretch")
                if run_query:
                    query_key = f"{puzzle_key}|{_result_key(st.session_state.result)}|{int(query_r)}|{int(query_c)}"
                    message = st.session_state.query_cache.get(query_key)
                    if message is None:
                        with st.spinner("Running backward chaining query..."):
                            program, _, domain_sum = _build_backward_query_program(
                                instance,
                                st.session_state.result,
                            )
                            engine = BackwardChainer(program, max_depth=64)
                            qv = var("V")
                            answer = engine.ask(atom("Val", int(query_r), int(query_c), qv))
                            values = [constant.value for constant in extract_constant_answers(answer, qv)]
                            if values:
                                message = (
                                    f"Backward chaining proves Val({int(query_r)},{int(query_c)},?) = {values} "
                                    f"(goals resolved: {answer.goals_resolved})."
                                )
                            else:
                                possible = engine.ask(atom("Possible", int(query_r), int(query_c), qv))
                                possible_values = [constant.value for constant in extract_constant_answers(possible, qv)]
                                if possible_values:
                                    message = (
                                        f"Backward chaining cannot prove a unique value yet. "
                                        f"Current possible values: {possible_values} "
                                        f"(goal count: {possible.goals_resolved}, domain sum: {domain_sum})."
                                    )
                                else:
                                    message = (
                                        "Backward chaining found no provable `Val` or `Possible` facts for this cell "
                                        "from the current snapshot KB."
                                    )
                            st.session_state.query_cache[query_key] = message
                    st.session_state.query_message = message
                if st.session_state.query_message:
                    if "found no provable" in st.session_state.query_message:
                        st.warning(st.session_state.query_message)
                    else:
                        st.info(st.session_state.query_message)

                st.subheader("CNF Stats")
                cnf_stats = st.session_state.cnf_stats_cache.get(puzzle_key)
                if cnf_stats is None:
                    cnf = encode_instance_to_cnf(instance)
                    program_stats = _program_stats(instance)
                    cnf_stats = {
                        "variables": cnf.num_variables,
                        "clauses": cnf.num_clauses,
                        "facts": program_stats["facts"],
                        "rules": program_stats["rules"],
                    }
                    st.session_state.cnf_stats_cache[puzzle_key] = cnf_stats
                st.json(cnf_stats)

        with logs_tab:
            result = st.session_state.result
            if result is None:
                st.info("Run a solver to see trace logs.")
            else:
                st.write(result.message or "No message.")
                st.code(_trace_text(result), language="text")

        with benchmark_tab:
            if st.button("Benchmark bundled inputs", width="stretch"):
                csv_path = Path("reports/benchmark_results.csv")
                with st.spinner("Benchmarking bundled inputs..."):
                    rows = benchmark_inputs("inputs", csv_path)
                    st.session_state.benchmark_rows = rows
                    st.session_state.benchmark_summary = summarize_benchmark(rows)
                st.success(f"Wrote {csv_path}")
            if st.session_state.benchmark_rows is not None:
                st.dataframe(st.session_state.benchmark_rows, width="stretch")
                st.markdown(st.session_state.benchmark_summary)

        with theory_tab:
            st.markdown(
                """
                ### FOL Vocabulary
                `Val(i,j,v)`, `Given(i,j,v)`, `LessH(i,j)`, `GreaterH(i,j)`, `LessV(i,j)`, `GreaterV(i,j)`, `Less(v1,v2)`.

                ### Input Format
                The editor and bundled files follow the assignment format: first `N`, then `N` CSV grid rows, `N` CSV horizontal rows, and `N-1` CSV vertical rows.

                ### Forward Chaining
                The ground Horn program propagates `Val`, `NotVal`, `Possible`, and `Assigned` facts with a real agenda-based engine. Search fallback is explicitly separated in the hybrid solver.

                ### Backward Chaining
                Queries are resolved by depth-first SLD resolution over the same Horn KB. The UI query panel asks `Val(i,j,?)` directly.

                ### A* Heuristic
                The main heuristic counts disconnected ambiguous constraint components after propagation. Each non-trivial component needs at least one new branching decision, so the heuristic is an admissible lower bound.
                """
            )


if __name__ == "__main__":
    main()
