from pathlib import Path

import main as project_main


def test_root_main_solves_with_positional_arguments(tmp_path: Path) -> None:
    output_path = tmp_path / "output-01.txt"
    code = project_main.main(["inputs/input-01.txt", str(output_path), "backtracking"])
    assert code == 0
    assert output_path.exists()
