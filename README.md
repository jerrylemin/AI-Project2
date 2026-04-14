# CSC14003 Project 2 - Futoshiki

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

Launch UI:

```bash
python main.py
```

Solve one input:

```bash
python main.py inputs/input-01.txt outputs/output-01.txt backtracking
python main.py inputs/input-01.txt outputs/output-01.txt astar main
python main.py inputs/input-01.txt outputs/output-01.txt logic-forward
python main.py inputs/input-01.txt outputs/output-01.txt logic-backward
```

Verify one output:

```bash
python main.py verify inputs/input-01.txt outputs/output-01.txt
```

Run benchmark and create charts:

```bash
python main.py benchmark inputs reports/benchmark_results.csv
```

## Main files

- `main.py`: root entry point for UI and command-line runs
- `src/futoshiki/`: source code
- `inputs/`, `outputs/`: bundled test cases
- `reports/project2_overleaf.txt`: final Overleaf source
