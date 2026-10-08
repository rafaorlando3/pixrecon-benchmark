#!/usr/bin/env python3
"""K3b: analysis of the PixRecon 7-model grid (GRID-511.csv + OUT/*.json + CASES.json).
Regrades every answer with the v4 grader to get per-order detail (status confusion, payments, orphans).
Usage: python3 -I k3b_grid_analysis.py ZIPDIR OUTDIR
"""
import csv, json, os, sys, hashlib, collections
import grader_v4 as G

zipdir, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
rows = list(csv.DictReader(open(os.path.join(zipdir, 'GRID-511.csv'))))
cases = {c['case_id']: c for c in json.load(open(os.path.join(zipdir, 'CASES.json')))}
NAMES = {'I1': 'gpt-oss-120b', 'I2': 'qwen3-235b-a22b-2507', 'I3': 'gemma-4-31b-it', 'I4': 'deepseek-r1-0528',
         'I5': 'claude-sonnet-5', 'I6': 'gpt-5.5', 'I7': 'gemini-3.1-pro-preview'}
ORDER = ['I6', 'I1', 'I5', 'I3', 'I2', 'I7', 'I4']  # by mean score desc (computed below, fixed for tables)

# map answer sha -> OUT file content
outmap = {}
for fn in os.listdir(os.path.join(zipdir, 'OUT')):
    p = os.path.join(zipdir, 'OUT', fn)
    try:
        j = json.load(open(p))
    except Exception:
        continue
    ch = (j.get('choices') or [{}])[0]
    msg = ch.get('message') or {}
    content = msg.get('content')
    if content is None:
        content = ''
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
    outmap.setdefault(sha, []).append((fn, content, ch.get('finish_reason'), ch.get('error')))

matched = 0
details = []  # per row regrade
for r in rows:
    sha = r['answer_sha256']
    content = None
    if sha in outmap:
        content = outmap[sha][0][1]; matched += 1
    g = G.grade(content if content is not None else '', cases[r['case_id']]['expected_json'])
    # consistency check with the published score
    pub = float(r['score'])
    if abs(pub - g['score']) > 1e-9:
        print('MISMATCH', r['attempt_id'], pub, g['score'], g['errors'][:3])
    r['_g'] = g
    details.append(r)
print('matched answers', matched, 'of', len(rows))

# ---------- tables ----------
def pct(x): return f"{100*x:.1f}%"
T = []
T.append('## Table 1. Overall (73 cases per model; failures count as 0)\n')
T.append('| Model | Mean score | Perfect cases | Schema-valid | Empty / provider error | Cost (US$) | US$ per case | US$ per perfect case |')
T.append('|---|---:|---:|---:|---:|---:|---:|---:|')
stats = {}
for lab in ORDER:
    rs = [r for r in rows if r['label'] == lab]
    n = len(rs); mean = sum(float(r['score']) for r in rs)/n
    perfect = sum(r['perfect'] == 'True' for r in rs)
    valid = sum(r['schema_valid'] == 'True' for r in rs)
    empty = sum(r['empty_output'] == 'True' for r in rs); perr = sum(r['provider_error'] == 'True' for r in rs)
    cost = sum(float(r['cost_USD']) for r in rs)
    stats[lab] = dict(n=n, mean=mean, perfect=perfect, valid=valid, empty=empty, perr=perr, cost=cost)
    T.append(f"| {NAMES[lab]} | {mean:.3f} | {perfect}/73 | {valid}/73 | {empty} / {perr} | {cost:.2f} | {cost/n:.4f} | {(cost/perfect if perfect else float('nan')):.3f} |")

T.append('\n## Table 2. Mean score by tier\n')
tiers = ['easy', 'medium', 'hard', 'gold']
T.append('| Model | ' + ' | '.join(f'{t} (n={sum(1 for r in rows if r["label"]=="I1" and r["tier"]==t)})' for t in tiers) + ' |')
T.append('|---|' + '---:|'*len(tiers))
tier_stats = {}
for lab in ORDER:
    vals = []
    for t in tiers:
        rs = [float(r['score']) for r in rows if r['label'] == lab and r['tier'] == t]
        m = sum(rs)/len(rs); tier_stats[(lab, t)] = m; vals.append(f'{m:.3f}')
    T.append(f'| {NAMES[lab]} | ' + ' | '.join(vals) + ' |')

# per expected-status accuracy (status and payments), only rows with parsed answers
T.append('\n## Table 3. Status accuracy by expected status (all 7 models pooled, parsed answers only)\n')
STAT = G.STATUSES
acc = collections.defaultdict(lambda: [0, 0, 0])  # expected -> [n, status_ok, payments_ok]
acc_m = collections.defaultdict(lambda: [0, 0, 0])  # (label, expected)
conf = collections.defaultdict(int)  # (expected, got)
conf_m = collections.defaultdict(int)
for r in details:
    g = r['_g']
    if not g['parsed']:
        continue
    for oid, d in g['detail'].items():
        e = d['expected']; got = d['got'] if d['got'] in STAT else ('missing' if d['got'] is None else 'invalid')
        acc[e][0] += 1; acc[e][1] += d['status_ok']; acc[e][2] += d['payments_ok']
        k = (r['label'], e); acc_m[k][0] += 1; acc_m[k][1] += d['status_ok']; acc_m[k][2] += d['payments_ok']
        conf[(e, got)] += 1; conf_m[(r['label'], e, got)] += 1
T.append('| Expected status | Orders (x models) | Status right | Linked transfers right |')
T.append('|---|---:|---:|---:|')
for s in STAT:
    n, so, po = acc[s]
    if n: T.append(f'| {s} | {n} | {pct(so/n)} | {pct(po/n)} |')

T.append('\n## Table 4. Confusion: expected status -> answered status (pooled, parsed answers; counts)\n')
gots = list(STAT) + ['missing', 'invalid']
T.append('| expected \\ got | ' + ' | '.join(gots) + ' |')
T.append('|---|' + '---:|'*len(gots))
for e in STAT:
    T.append(f'| **{e}** | ' + ' | '.join(str(conf.get((e, g_), 0)) for g_ in gots) + ' |')

T.append('\n## Table 5. Status accuracy per model and expected status (parsed answers)\n')
T.append('| Model | ' + ' | '.join(STAT) + ' |')
T.append('|---|' + '---:|'*len(STAT))
for lab in ORDER:
    vals = []
    for s in STAT:
        n, so, po = acc_m[(lab, s)]
        vals.append(pct(so/n) if n else '-')
    T.append(f'| {NAMES[lab]} | ' + ' | '.join(vals) + ' |')

# gold cases
T.append('\n## Table 6. Gold cases: which models got each one perfect\n')
T.append('| Gold case | Perfect (of 7) | Models that failed | Typical failure |')
T.append('|---|---:|---|---|')
gold_ids = [c for c in cases if c.startswith('g')]
gold_fail_count = {}
for cid in sorted(gold_ids):
    rs = [r for r in details if r['case_id'] == cid]
    ok = [r for r in rs if r['perfect'] == 'True']
    bad = [r for r in rs if r['perfect'] != 'True']
    reasons = []
    for r in bad:
        g = r['_g']
        if not g['parsed']:
            reasons.append('no JSON' if r['empty_output'] == 'True' or r['provider_error'] == 'True' else 'invalid JSON')
        elif not g['schema_valid']:
            reasons.append('schema')
        else:
            wrong = [f"{oid}:{d['expected']}->{d['got']}" for oid, d in g['detail'].items() if not d['status_ok']]
            pay = [oid for oid, d in g['detail'].items() if not d['payments_ok']]
            rr = []
            if wrong: rr.append('status ' + ';'.join(wrong))
            if pay: rr.append('payments ' + ','.join(pay))
            if not g['orphans_ok']: rr.append('orphans')
            if g['extra_orders']: rr.append('invented ' + ','.join(g['extra_orders']))
            reasons.append(' / '.join(rr) or 'other')
    gold_fail_count[cid] = len(bad)
    T.append(f"| {cid} | {len(ok)}/7 | {', '.join(NAMES[r['label']] for r in bad) or '-'} | {'; '.join(sorted(set(reasons)))[:160] or '-'} |")

# invented orders, orphans, missing
T.append('\n## Table 7. Hygiene: invented orders, wrong orphan list, missing orders, invalid JSON (per model, 73 cases)\n')
T.append('| Model | Cases with invented orders | Cases with wrong orphan list (parsed) | Cases with missing orders | Invalid JSON / schema | Empty or error |')
T.append('|---|---:|---:|---:|---:|---:|')
hyg = {}
for lab in ORDER:
    rs = [r for r in details if r['label'] == lab]
    inv = sum(1 for r in rs if r['_g']['extra_orders'])
    orph = sum(1 for r in rs if r['_g']['parsed'] and not r['_g']['orphans_ok'])
    miss = sum(1 for r in rs if r['_g']['missing_orders'])
    invalid = sum(1 for r in rs if r['_g']['parsed'] and not r['_g']['schema_valid']) + sum(1 for r in rs if not r['_g']['parsed'] and r['empty_output'] != 'True' and r['provider_error'] != 'True')
    empty = sum(1 for r in rs if r['empty_output'] == 'True' or r['provider_error'] == 'True')
    hyg[lab] = (inv, orph, miss, invalid, empty)
    T.append(f'| {NAMES[lab]} | {inv} | {orph} | {miss} | {invalid} | {empty} |')

# tokens / latency
T.append('\n## Table 8. Reasoning tokens and latency (median per case)\n')
import statistics
T.append('| Model | Median reasoning tokens | Median completion tokens | Median seconds per case | Cases hitting max_tokens (finish=length) |')
T.append('|---|---:|---:|---:|---:|')
for lab in ORDER:
    rs = [r for r in rows if r['label'] == lab]
    rt = statistics.median(int(r['reasoning_tokens'] or 0) for r in rs)
    ct = statistics.median(int(r['completion_tokens'] or 0) for r in rs)
    du = statistics.median(float(r['duration_seconds'] or 0) for r in rs)
    ln = sum(1 for r in rs if r['finish_reason'] == 'length')
    T.append(f'| {NAMES[lab]} | {rt:.0f} | {ct:.0f} | {du:.1f} | {ln} |')

# by exception tag (pooled and per model), synthetic cases carry comma-separated tags
T.append('\n## Table 9. Mean score by injected exception tag (synthetic cases; a case can carry several tags)\n')
tagstats = collections.defaultdict(list); tag_m = collections.defaultdict(list)
for r in rows:
    tags = [t for t in (r['exceptions'] or '').split(',') if t]
    for t in tags:
        tagstats[t].append(float(r['score'])); tag_m[(r['label'], t)].append(float(r['score']))
tags_sorted = sorted(tagstats, key=lambda t: sum(tagstats[t])/len(tagstats[t]))
T.append('| Tag | Cases x models | Mean score (pooled) | ' + ' | '.join(NAMES[l] for l in ORDER) + ' |')
T.append('|---|---:|---:|' + '---:|'*len(ORDER))
for t in tags_sorted:
    v = tagstats[t]
    T.append(f'| {t} | {len(v)} | {sum(v)/len(v):.3f} | ' + ' | '.join(f"{(sum(tag_m[(l,t)])/len(tag_m[(l,t)])):.2f}" if tag_m[(l,t)] else '-' for l in ORDER) + ' |')

open(os.path.join(outdir, 'tables.md'), 'w').write('\n'.join(T) + '\n')
json.dump({'stats': stats, 'tier': {f'{k[0]}/{k[1]}': v for k, v in tier_stats.items()}, 'conf': {f'{k[0]}->{k[1]}': v for k, v in conf.items()},
           'gold_fail': gold_fail_count, 'hyg': hyg, 'acc': {k: v for k, v in acc.items()},
           'acc_m': {f'{k[0]}/{k[1]}': v for k, v in acc_m.items()}}, open(os.path.join(outdir, 'numbers.json'), 'w'), indent=1)

# ---------- figures ----------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
colors = {'I6': '#1f5fbf', 'I1': '#2a9d8f', 'I5': '#e76f51', 'I3': '#8ab17d', 'I2': '#f4a261', 'I7': '#9b5de5', 'I4': '#6c757d'}
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
x = np.arange(len(tiers)); w = 0.11
for i, lab in enumerate(ORDER):
    vals = [tier_stats[(lab, t)] for t in tiers]
    ax.bar(x + (i - 3) * w, vals, w, label=NAMES[lab], color=colors[lab])
ax.set_xticks(x); ax.set_xticklabels(['easy (20)', 'medium (20)', 'hard (20)', 'gold (13)'])
ax.set_ylim(0, 1.05); ax.set_ylabel('mean score (failures = 0)')
ax.set_title('PixRecon: mean score by tier, 7 models x 73 cases')
ax.legend(ncol=4, fontsize=8, frameon=False, loc='lower left')
ax.grid(axis='y', alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(outdir, 'fig1_score_by_tier.png')); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
for lab in ORDER:
    s = stats[lab]; cpc = s['cost'] / s['n']
    ax.scatter(cpc, s['mean'], s=140, color=colors[lab], edgecolor='black', linewidth=0.5, zorder=3)
    dx = 1.08
    ax.annotate(f"{NAMES[lab]}\n{s['perfect']}/73 perfect", (cpc * dx, s['mean']), fontsize=8, va='center')
ax.set_xscale('log'); ax.set_xlabel('US$ per case (OpenRouter receipts, log scale)'); ax.set_ylabel('mean score (failures = 0)')
ax.set_ylim(0, 1.08); ax.set_xlim(1e-4, 0.3)
ax.set_title('Price does not buy accuracy: cost per case vs score')
ax.grid(alpha=0.3, which='both')
fig.tight_layout(); fig.savefig(os.path.join(outdir, 'fig2_cost_vs_score.png')); plt.close(fig)
print('done')
