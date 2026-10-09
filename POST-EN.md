---
title: "7 LLMs reconciled 73 Pix statements: 99.6% correct order links, zero invented orders observed, and the hard part was the clock"
published: false
tags: kagglechallenge, devchallenge, ai, machinelearning
cover_image: https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/ofqv53mfne9ft71f9hhu.png
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23).*

## What I Benchmarked

Pix reconciliation raises an everyday question: which orders match the transfers that actually arrived? Customers pay with Pix, Brazil's instant payment system, and at the end of the day two lists have to agree: the orders and the bank statement. They never agree cleanly. The bank exports the same transfer twice, a customer pays twice, pays a cent short, pays after the order expired, gets a refund, or sends money with no order reference at all. Somebody sits with both lists and sorts it out by hand. This benchmark tests whether a language model can perform that matching under explicit rules.

**PixRecon** is the test. Each case hands the model a list of orders (id, amount, created and expiry instants) and a bank statement (transfers with end-to-end id, amount, time, payer, an optional txid and a free-text description). The model must answer, as one JSON object, a status for every order (`paid`, `unpaid`, `underpaid`, `overpaid`, `late_paid`, `refunded`), the list of transfers linked to it, and the orphan transfers that match no order. Thirteen short rules live in the prompt: count a repeated end-to-end id once, link by txid or by an order id in the description and never by amount alone, compare instants across time zones, use the gross amount received, and follow a fixed precedence when more than one status could apply.

Why this task: it is boring, common and unforgiving. A wrong `paid` ships goods that were never paid for; a missed duplicate refunds money twice. It mixes several things models are said to be bad at: exact arithmetic on money written in two formats ("R$ 1.234,56" and "1234.56"), time zones, de-duplication, and a strict output schema that a downstream system will parse without mercy.

**The cases.** 73 in total, all fictional. Sixty are synthetic, generated from fixed seeds in three tiers: easy (5 orders, no injected exceptions), medium (10 orders, 25% chance of an exception per order) and hard (16 orders, 45%). The injected exceptions are tagged, so I can score by exception type: export duplicates, double payments, underpayments, late payments, refunds, orphans, missing txid, UTC timestamps and Brazilian number formatting. Thirteen gold cases are written by hand, each aimed at one rule: a payment exactly at the deadline, one second late, one second early, the same instant written in UTC and in -03:00, clock text that looks late but is not, a partial payment that is also late, cents in Brazilian format, a refund next to an export duplicate, a partial refund, a double payment with one leg refunded, a txid that contradicts the description, orphans, and a link that exists only in the description.

**The grade.** Deterministic, no LLM judge. For each expected order, 0.5 for the exact status and 0.5 for the exact list of linked transfers; 1 point for an exactly right orphan list. Every invented order adds 1 to the denominator. The answer must be a single JSON object, optionally inside one Markdown code fence; prose around it, two documents, duplicate keys or a broken schema score 0 for the case. A case is "perfect" only when the schema is valid and every point is earned. Failures (empty output, provider error, truncation) stay in the table as 0: the denominator is always 73.

**Keeping the run honest.** Every request is written to a hash-chained ledger before it is sent, with the SHA-256 of the prompt, the case and the expected answer, and the provider receipt (generation id, tokens, cost) is appended after. A completed answer is never re-asked to improve a score. Nine transport-level 429s were retried; two provider errors returned inside an HTTP 200 were graded as failures and not retried. The grid records US$ 9.17 in known receipt costs. The API usage reading exceeded those receipts by US$ 0.0024675825; that difference and the failed-attempt reservations remain unresolved, rather than being counted as zero.

## Models Tested

The new Kaggle run completed on **8 October 2026 (America/Asuncion)**. Task Page: https://www.kaggle.com/benchmarks/tasks/rafaorlando3/pixrecon-pix-reconciliation/1. Verified model: `google/gemini-3.7-flash` (Gemini 3.7 Flash). Verified result: mean **1.0000**, reported 95% confidence half-width **0.0000**, 73/73 valid schemas, 73/73 perfect cases and 0 failed cases.

Kaggle selected its default model. All 73 recorded requests completed without a retry. The provider receipts report US$ 1.13706675 of usage-equivalent cost; this run used the Kaggle Model Proxy free quota, which displayed US$ 1.14 of daily usage after completion. This is not a paid invoice. A zero-width reported interval here reflects identical scores on this finite set, not certainty about unseen statements.

The seven-model grid below is a separate frozen evaluation called directly through OpenRouter, using the repository cases, prompt and grader. Temperature and reasoning settings stayed at each provider's defaults; `max_tokens` was 8,192 for everyone. That cap turned out to matter, as you will see.

The seven, cheapest first, with the OpenRouter ids used:

| Model | Why it is here |
|---|---|
| openai/gpt-oss-120b | open weights, cheap, strong on structured tasks |
| qwen/qwen3-235b-a22b-2507 | open weights, instruct, no reasoning |
| google/gemma-4-31b-it | open weights, small enough to self-host |
| deepseek/deepseek-r1-0528 | open weights, reasoning model |
| anthropic/claude-sonnet-5 | frontier, mid price |
| openai/gpt-5.5 | frontier, mid price |
| google/gemini-3.1-pro-preview | frontier, most expensive of the set |

Same prompt, same 73 cases, same grader: 511 logical pairs and 520 direct transport attempts, including nine transport-level 429 retries. Completed answers were not re-asked to improve scores. Gemma ran on DeepInfra, GPT-OSS on CoreWeave and then BaseTen after a run of capacity 429s; the per-provider subsets are in the audit files but are not paired comparisons, so I do not read anything into them.

## Findings

### The money-matching part is solved. The rules are not.

Across the 3,565 order answers that parsed, the list of linked transfers was exactly right 99.6% of the time (3,551). Linking by end-to-end id, txid or description, de-duplicating the export, ignoring amount-only coincidences: every model does this well, including the cheap ones. None of the 436 parseable answers invented an order that did not exist. Orphan lists were wrong in 7 of 436 parsed answers, five of them Qwen on hard cases.

The status label is where the points go. Pooled status accuracy was 93.1%, and 180 of the 246 status errors are the same confusion: `paid` answered as `late_paid` (92) or `late_paid` answered as `paid` (88). The model found the right transfer and then misjudged whether it arrived before the order expired. The next confusion, `underpaid` answered as `overpaid` (30), is a sign error on the difference between amount due and amount received, and 20 of the 30 are Qwen.

| Expected status | Orders (x models) | Status right | Linked transfers right |
|---|---:|---:|---:|
| paid | 1,152 | 91.4% | 99.9% |
| unpaid | 473 | 100.0% | 100.0% |
| underpaid | 613 | 94.6% | 100.0% |
| overpaid | 321 | 92.2% | 96.6% |
| late_paid | 785 | 88.7% | 99.9% |
| refunded | 221 | 100.0% | 99.5% |

`unpaid` and `refunded` were never missed by any model. `late_paid` is the weakest label: one late payment in nine was reported as on time.

### Overall table

| Model | Mean score | Perfect cases | Schema-valid | Empty / provider error | Cost, 73 cases | US$ per perfect case |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.5 | 0.999 | 72/73 | 73/73 | 0 / 0 | US$ 2.42 | 0.034 |
| gpt-oss-120b | 0.979 | 64/73 | 72/73 | 0 / 0 | US$ 0.09 | 0.001 |
| claude-sonnet-5 | 0.973 | 71/73 | 71/73 | 0 / 0 | US$ 1.47 | 0.021 |
| gemma-4-31b-it | 0.957 | 33/73 | 73/73 | 0 / 0 | US$ 0.03 | 0.001 |
| qwen3-235b-a22b-2507 | 0.876 | 15/73 | 73/73 | 0 / 0 | US$ 0.02 | 0.001 |
| gemini-3.1-pro-preview | 0.780 | 56/73 | 57/73 | 2 / 2 | US$ 4.14 | 0.074 |
| deepseek-r1-0528 | 0.233 | 17/73 | 17/73 | 56 / 0 | US$ 1.00 | 0.059 |

![Mean score by tier, 7 models x 73 cases](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/3nznqc0ed0upevmvjy4r.png)

| Model | easy (20) | medium (20) | hard (20) | gold (13) |
|---|---:|---:|---:|---:|
| gpt-5.5 | 1.000 | 0.998 | 1.000 | 1.000 |
| gpt-oss-120b | 1.000 | 0.980 | 0.946 | 1.000 |
| claude-sonnet-5 | 1.000 | 1.000 | 0.950 | 0.923 |
| gemma-4-31b-it | 0.975 | 0.936 | 0.957 | 0.962 |
| qwen3-235b-a22b-2507 | 0.871 | 0.891 | 0.837 | 0.923 |
| gemini-3.1-pro-preview | 0.950 | 0.995 | 0.250 | 1.000 |
| deepseek-r1-0528 | 0.150 | 0.050 | 0.000 | 1.000 |

### Two models lost to the clock, two lost to their own thinking budget

**The clock.** The gold cases that separate models are not the deadline edges. A payment exactly at the cutoff, one second late and one second early were solved by all seven. What broke Qwen and Gemma was the same instant written twice: `13:00:00Z` for a deadline written as `10:00:00-03:00` in `g04-utc-equal-instant`. Both models called that payment late. They also failed `g05-utc-clock-text-trap`, where `10:30:00Z` is before the `10:00:00-03:00` deadline despite the clock text looking later. That single mistake, repeated across the synthetic cases that carry UTC timestamps, is most of Gemma's 42 `paid → late_paid` errors and a good part of Qwen's 124 confusions between the two labels. Gemma otherwise answered every one of its 73 cases with valid JSON and linked the right transfers in 99.8% of its order answers, which makes the failure easy to fix with a tool call and hard to fix with a prompt.

**The thinking budget.** DeepSeek R1 returned an empty answer in 56 of 73 cases. It did not get the cases wrong: it spent the entire 8,192-token budget reasoning (median 7,937 reasoning tokens, 237 seconds per case) and never wrote the JSON. In the 17 cases where it did answer, 13 of them gold, it was perfect, with 100% status accuracy. Gemini 3.1 Pro preview failed in a quieter way: on the hard tier it reasoned for a median of 7,853 tokens and then ran out of room in the middle of the JSON in 14 of 20 cases (`finish_reason: length`), which the grader reads as an invalid document. Its score on hard cases is 0.25; on everything else it is 0.95 or better, with 100% status accuracy when the answer parsed.

The cap was the same for every model; provider defaults and reasoning settings were not normalized, so these results describe this specific setup. But the lesson is not "raise the cap". A reconciliation job needs a guaranteed budget for the answer that the thinking cannot eat. The models that solved this task did it in 446 (GPT-5.5) to 957 (Sonnet 5) reasoning tokens and 7 to 13 seconds per case. Twenty times more thinking did not buy a better status label.

### Format discipline is a separate skill

Claude Sonnet 5 had 100% status accuracy on every answer that parsed and 71 perfect cases. Its two zeros were not reconciliation errors. In `hard-011` it opened with a sentence of prose ("Looking at the data, I need to deduplicate…") before the JSON. In `g10-double-pay-one-refunded` it wrote a correct JSON block, then added "Wait, correcting…" and a second block. Two documents, score 0, by the rule stated in the prompt. GPT-OSS-120b lost one hard case to a duplicate key: the same order id written twice in the object. These are the right calls for a benchmark whose output feeds another program; they are also the easiest points to recover with a strict decoder or a retry on parse failure.

### Price did not buy accuracy

![Cost per case vs score](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/ofqv53mfne9ft71f9hhu.png)

GPT-5.5 was the best model in the grid: 72 of 73 perfect, and the one miss was a single linked-transfer list on an overpaid order. GPT-OSS-120b, an open-weights model, finished within 0.02 of it for US$ 0.09, 27 times cheaper. The most expensive run, Gemini 3.1 Pro preview at US$ 4.14, finished sixth, because of the truncation above. DeepSeek R1 cost eleven times more than GPT-OSS to answer 17 cases. Under these frozen rules, GPT-5.5 had the highest score and GPT-OSS-120b offered a cheaper pre-check; operational use would still send exceptions such as `late_paid` and `overpaid` to a person.

### What the results show

Arithmetic in Brazilian format and partial-refund logic might look like the hard parts. In this grid they were not: `g07-brl-cents` and `g08-refund-with-export-duplicate` were 7 of 7, and `g09-partial-refund` was 6 of 7. The wall was time-zone arithmetic that a calendar library gets right in one line, and output budgets. Output hygiene was also strong: 511 evaluated pairs, 436 parseable answers, zero invented orders among those answers, and only two models produced any malformed JSON at all once truncation is set aside.

### Limits

PixRecon measures how well a model follows these closed rules on these cases. It is not an accounting or compliance certification; the statement format is invented, not a real bank export; and 73 cases is a small set, so a single gold case moves a model's mean by 0.014. Reasoning settings were provider defaults, not normalized, so the DeepSeek and Gemini results describe those defaults under an 8,192-token cap, not the models' ceiling. The per-provider subsets for GPT-OSS are not paired and are reported only for transparency.

### What I would measure next

Give every model a tool for instant comparison and see whether the `paid`/`late_paid` confusion disappears for Qwen and Gemma. Separate the reasoning budget from the output budget for DeepSeek and Gemini and rerun the hard tier. Add gold cases written by people who reconcile statements for a living, partial refunds spread across several transfers, and a statement with 200 lines to see where the linking accuracy starts to fall.

## My Benchmark

Benchmark on Kaggle: https://www.kaggle.com/benchmarks/tasks/rafaorlando3/pixrecon-pix-reconciliation/1

Kaggle Task Page: https://www.kaggle.com/benchmarks/tasks/rafaorlando3/pixrecon-pix-reconciliation/1

Notebook (its runtime and publication state are separate from the frozen direct-grid artifacts): https://www.kaggle.com/code/rafaorlando3/pixrecon-pix-statement-reconciliation-benchmark

Code (frozen cases, exact prompt, grader, selected receipts and analysis): https://github.com/rafaorlando3/pixrecon-benchmark

This article was created with AI assistance.