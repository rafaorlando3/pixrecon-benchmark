## Table 1. Overall (73 cases per model; failures count as 0)

| Model | Mean score | Perfect cases | Schema-valid | Empty / provider error | Cost (US$) | US$ per case | US$ per perfect case |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.5 | 0.999 | 72/73 | 73/73 | 0 / 0 | 2.42 | 0.0331 | 0.034 |
| gpt-oss-120b | 0.979 | 64/73 | 72/73 | 0 / 0 | 0.09 | 0.0012 | 0.001 |
| claude-sonnet-5 | 0.973 | 71/73 | 71/73 | 0 / 0 | 1.47 | 0.0202 | 0.021 |
| gemma-4-31b-it | 0.957 | 33/73 | 73/73 | 0 / 0 | 0.03 | 0.0004 | 0.001 |
| qwen3-235b-a22b-2507 | 0.876 | 15/73 | 73/73 | 0 / 0 | 0.02 | 0.0002 | 0.001 |
| gemini-3.1-pro-preview | 0.780 | 56/73 | 57/73 | 2 / 2 | 4.14 | 0.0567 | 0.074 |
| deepseek-r1-0528 | 0.233 | 17/73 | 17/73 | 56 / 0 | 1.00 | 0.0137 | 0.059 |

## Table 2. Mean score by tier

| Model | easy (n=20) | medium (n=20) | hard (n=20) | gold (n=13) |
|---|---:|---:|---:|---:|
| gpt-5.5 | 1.000 | 0.998 | 1.000 | 1.000 |
| gpt-oss-120b | 1.000 | 0.980 | 0.946 | 1.000 |
| claude-sonnet-5 | 1.000 | 1.000 | 0.950 | 0.923 |
| gemma-4-31b-it | 0.975 | 0.936 | 0.957 | 0.962 |
| qwen3-235b-a22b-2507 | 0.871 | 0.891 | 0.837 | 0.923 |
| gemini-3.1-pro-preview | 0.950 | 0.995 | 0.250 | 1.000 |
| deepseek-r1-0528 | 0.150 | 0.050 | 0.000 | 1.000 |

## Table 3. Status accuracy by expected status (all 7 models pooled, parsed answers only)

| Expected status | Orders (x models) | Status right | Linked transfers right |
|---|---:|---:|---:|
| paid | 1152 | 91.4% | 99.9% |
| unpaid | 473 | 100.0% | 100.0% |
| underpaid | 613 | 94.6% | 100.0% |
| overpaid | 321 | 92.2% | 96.6% |
| late_paid | 785 | 88.7% | 99.9% |
| refunded | 221 | 100.0% | 99.5% |

## Table 4. Confusion: expected status -> answered status (pooled, parsed answers; counts)

| expected \ got | paid | unpaid | underpaid | overpaid | late_paid | refunded | missing | invalid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **paid** | 1053 | 0 | 7 | 0 | 92 | 0 | 0 | 0 |
| **unpaid** | 0 | 473 | 0 | 0 | 0 | 0 | 0 | 0 |
| **underpaid** | 1 | 0 | 580 | 30 | 2 | 0 | 0 | 0 |
| **overpaid** | 16 | 0 | 1 | 296 | 6 | 1 | 1 | 0 |
| **late_paid** | 88 | 0 | 1 | 0 | 696 | 0 | 0 | 0 |
| **refunded** | 0 | 0 | 0 | 0 | 0 | 221 | 0 | 0 |

## Table 5. Status accuracy per model and expected status (parsed answers)

| Model | paid | unpaid | underpaid | overpaid | late_paid | refunded |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.5 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| gpt-oss-120b | 98.9% | 100.0% | 97.2% | 98.3% | 98.6% | 100.0% |
| claude-sonnet-5 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| gemma-4-31b-it | 78.2% | 100.0% | 91.8% | 95.0% | 93.2% | 100.0% |
| qwen3-235b-a22b-2507 | 71.5% | 100.0% | 80.9% | 65.0% | 47.6% | 100.0% |
| gemini-3.1-pro-preview | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| deepseek-r1-0528 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## Table 6. Gold cases: which models got each one perfect

| Gold case | Perfect (of 7) | Models that failed | Typical failure |
|---|---:|---|---|
| g01-exact-cutoff | 7/7 | - | - |
| g02-one-second-late | 7/7 | - | - |
| g03-one-second-early | 7/7 | - | - |
| g04-utc-equal-instant | 5/7 | qwen3-235b-a22b-2507, gemma-4-31b-it | status PED-1004:paid->late_paid |
| g05-utc-clock-text-trap | 5/7 | qwen3-235b-a22b-2507, gemma-4-31b-it | status PED-1005:paid->late_paid |
| g06-partial-and-late | 7/7 | - | - |
| g07-brl-cents | 7/7 | - | - |
| g08-refund-with-export-duplicate | 7/7 | - | - |
| g09-partial-refund | 6/7 | qwen3-235b-a22b-2507 | status PED-1009:paid->underpaid |
| g10-double-pay-one-refunded | 5/7 | qwen3-235b-a22b-2507, claude-sonnet-5 | invalid JSON; status PED-1010:overpaid->refunded |
| g11-txid-beats-description | 7/7 | - | - |
| g12-orphans | 7/7 | - | - |
| g13-description-link | 7/7 | - | - |

## Table 7. Hygiene: parsed-answer checks and output failures (73 evaluated cases per model)

| Model | Cases with invented orders (parsed) | Cases with wrong orphan list (parsed) | Cases with missing orders (parsed) | Invalid JSON / schema | Empty or error |
|---|---:|---:|---:|---:|---:|
| gpt-5.5 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss-120b | 0 | 1 | 1 | 1 | 0 |
| claude-sonnet-5 | 0 | 0 | 0 | 2 | 0 |
| gemma-4-31b-it | 0 | 0 | 0 | 0 | 0 |
| qwen3-235b-a22b-2507 | 0 | 5 | 0 | 0 | 0 |
| gemini-3.1-pro-preview | 0 | 1 | 0 | 14 | 2 |
| deepseek-r1-0528 | 0 | 0 | 0 | 0 | 56 |

Invented-order, orphan-list and missing-order checks apply to the 436 parseable answers across the 511 evaluated pairs. Zero invented orders were observed in those 436 answers; this does not establish that property for unparseable, empty or provider-error outputs. The 73-case evaluation denominator and the frozen counts above are unchanged.

## Table 8. Reasoning tokens and latency (median per case)

| Model | Median reasoning tokens | Median completion tokens | Median seconds per case | Cases hitting max_tokens (finish=length) |
|---|---:|---:|---:|---:|
| gpt-5.5 | 446 | 654 | 6.9 | 0 |
| gpt-oss-120b | 0 | 2386 | 19.5 | 0 |
| claude-sonnet-5 | 957 | 1299 | 12.6 | 0 |
| gemma-4-31b-it | 0 | 508 | 15.8 | 0 |
| qwen3-235b-a22b-2507 | 0 | 247 | 7.0 | 0 |
| gemini-3.1-pro-preview | 3854 | 4351 | 29.9 | 14 |
| deepseek-r1-0528 | 7937 | 8192 | 237.5 | 47 |

## Table 9. Mean score by injected exception tag (synthetic cases; a case can carry several tags)

| Tag | Cases x models | Mean score (pooled) | gpt-5.5 | gpt-oss-120b | claude-sonnet-5 | gemma-4-31b-it | qwen3-235b-a22b-2507 | gemini-3.1-pro-preview | deepseek-r1-0528 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| double_payment | 217 | 0.758 | 1.00 | 0.95 | 0.97 | 0.95 | 0.85 | 0.55 | 0.03 |
| refunded | 154 | 0.759 | 1.00 | 0.94 | 1.00 | 0.95 | 0.88 | 0.54 | 0.00 |
| no_txid | 266 | 0.764 | 1.00 | 0.96 | 0.97 | 0.95 | 0.87 | 0.60 | 0.00 |
| late_paid | 259 | 0.766 | 1.00 | 0.96 | 0.97 | 0.95 | 0.86 | 0.59 | 0.03 |
| underpaid | 245 | 0.767 | 1.00 | 0.96 | 0.97 | 0.95 | 0.86 | 0.60 | 0.03 |
| export_duplicate | 266 | 0.767 | 1.00 | 0.96 | 0.97 | 0.95 | 0.86 | 0.60 | 0.03 |
| brl_format | 280 | 0.771 | 1.00 | 0.96 | 0.97 | 0.95 | 0.86 | 0.62 | 0.03 |
| utc_timestamp | 280 | 0.771 | 1.00 | 0.96 | 0.97 | 0.95 | 0.86 | 0.62 | 0.03 |
| orphan | 168 | 0.793 | 1.00 | 0.98 | 1.00 | 0.95 | 0.88 | 0.70 | 0.04 |
| gold | 91 | 0.973 | 1.00 | 1.00 | 0.92 | 0.96 | 0.92 | 1.00 | 1.00 |
