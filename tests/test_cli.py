from pathlib import Path

from futoshiki.cli import main
from futoshiki.parser import parse_file


def test_cli_solve_and_verify(tmp_path: Path) -> None:
    output_path = tmp_path / "output-01.txt"
    solve_code = main(
        ["solve", "--input", "inputs/input-01.txt", "--solver", "backtracking", "--output", str(output_path)]
    )
    assert solve_code == 0
    verify_code = main(["verify", "--input", "inputs/input-01.txt", "--output", str(output_path)])
    assert verify_code == 0


def test_cli_verify_rejects_wrong_output_sign(tmp_path: Path) -> None:
    output_path = tmp_path / "bad-output.txt"
    text = Path("outputs/output-01.txt").read_text(encoding="utf-8")
    output_path.write_text(text.replace("<", ">", 1), encoding="utf-8")
    code = main(["verify", "--input", "inputs/input-01.txt", "--output", str(output_path)])
    assert code == 1


def test_cli_benchmark_creates_summary_and_figures(tmp_path: Path) -> None:
    csv_path = tmp_path / "benchmark_results.csv"
    code = main(["benchmark", "--inputs", "inputs", "--out", str(csv_path)])
    assert code == 0
    assert csv_path.exists()
    assert (tmp_path / "benchmark_summary.md").exists()
    figures = list((tmp_path / "figures").glob("*.png"))
    assert len(figures) >= 6
