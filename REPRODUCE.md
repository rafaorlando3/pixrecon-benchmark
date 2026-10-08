# Offline grading and analysis

The cases, prompt source, grader, CSV and selected response bytes are frozen. No generator or model runner is included. `PROMPT.md` documents the exact inputs. This publication does not run any code.

The single-answer example is in `README.md`. For the existing analysis source, the first argument must contain `GRID-511.csv`, `CASES.json` and an `OUT/` directory. It imports the grader and uses matplotlib/numpy to produce tables and figures. Prepare that layout explicitly when reproducing offline; no API key or model call is needed:

```bash
input_dir=$(mktemp -d)
output_dir=$(mktemp -d)
mkdir "$input_dir/OUT"
cp cases/CASES.json "$input_dir/CASES.json"
cp runs/openrouter-grid-2026-10-07/GRID-511.csv "$input_dir/GRID-511.csv"
cp runs/openrouter-grid-2026-10-07/raw/*.json "$input_dir/OUT/"
PYTHONPATH="$PWD/grader" python3 analysis/k3b_grid_analysis.py "$input_dir" "$output_dir"
```

The private source audit reports an exact offline regrade; see its public summary. Preserve failures and all 73 logical cases per model. Do not infer a new model run or additional verification from the existence of this recipe.
