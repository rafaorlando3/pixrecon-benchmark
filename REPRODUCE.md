# Offline grading and analysis

The cases, prompt source, grader, CSV and selected response bytes are frozen. `PROMPT.md` documents the exact inputs for offline grading. The Kaggle notebook described below includes model calls and is separate from this offline recipe. Publishing its source does not execute it.

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

## Kaggle execution source

`kaggle/pixrecon-kaggle-task.ipynb` preserves the exact source submitted to Kaggle BuildTask version 1 (job `356568120`), with complete file SHA-256 `b11620a60fdb19d8623a8e0fb587e4a66ddceef9672369a626cf64f744efb760`. It asserts Kaggle Benchmarks SDK `0.6.1` and embeds the frozen cases, prompt and grader.

Its final cells call `pixrecon.run(kbench.llm, cases)`. Kaggle BuildTask performs server-side execution with Kaggle's default model selection. Running this notebook invokes models; it is not required to reproduce the archived OpenRouter answers or grade them offline. The effective BuildTask model and result remain unconfirmed in this source archive, which has no execution outputs. The historical Kaggle records and the frozen seven-model grid remain separate.

The submitted source disables the SDK client's built-in retries and sets each nested evaluation to one attempt. It permits one final retry only for recognized transport failures; authentication, rate-limit/quota and unknown errors are not retried by that branch. This documents the source's behavior, without claiming a successful completion or starting another run.
