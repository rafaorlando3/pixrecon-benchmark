"""Deterministic grading. No LLM judge.

Version 4 (2026-10-01): every order in the answer, including invented ones, is validated structurally
before the content comparison (REVISAO-K2 of the Codex, 05h40). Order ids must be strings, also when
grade() receives a dict directly.

Version 3 (2026-10-01):
- The whole answer must be one JSON object. The only wrapper allowed is a single Markdown code fence
  around the entire answer (```json ... ``` or ``` ... ```). Text before/after, a top-level array,
  two documents, duplicate keys and NaN/Infinity are rejected.
- Schema is exact: top level {"orders", "orphans"}; each order {"status", "payments"}.
- Three numbers are reported, never merged silently:
    content_score  points earned on content, in [0, 1] (as in v2);
    schema_valid   True only if the answer follows the exact schema;
    score          the value the benchmark publishes = content_score if schema_valid else 0.0.
  perfect = schema_valid and content_score == 1 and no missing or extra order.
"""
from __future__ import annotations

import json
import re

STATUSES = ("paid", "unpaid", "underpaid", "overpaid", "late_paid", "refunded")
TOP_KEYS = {"orders", "orphans"}
ORDER_KEYS = {"status", "payments"}

_FENCE = re.compile(r"\A```(?:json|JSON)?[ \t]*\r?\n(.*)\r?\n```\Z", re.S)


class _DupKey(Exception):
    pass


def _no_dup_pairs(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise _DupKey(sorted({k for k in keys if keys.count(k) > 1}))
    return dict(pairs)


def _no_constants(name):
    raise ValueError("non_finite_constant:" + name)


def parse_answer(text_or_obj):
    """Returns (obj, errors). obj is the parsed JSON value of the WHOLE answer, or None."""
    if isinstance(text_or_obj, dict):
        return text_or_obj, []
    if hasattr(text_or_obj, "model_dump"):
        return text_or_obj.model_dump(), []
    text = "" if text_or_obj is None else str(text_or_obj)
    text = text.strip()
    if not text:
        return None, ["empty_answer"]
    m = _FENCE.match(text)
    if m:
        text = m.group(1).strip()
        if "```" in text:
            return None, ["more_than_one_fence"]
    try:
        obj = json.loads(text, object_pairs_hook=_no_dup_pairs, parse_constant=_no_constants)
    except _DupKey as e:
        return None, ["duplicate_json_keys:" + ",".join(map(str, e.args[0]))]
    except ValueError as e:  # JSONDecodeError is a ValueError: residual text, two documents, bad syntax
        msg = str(e)
        if msg.startswith("non_finite_constant:"):
            return None, [msg]
        if "Extra data" in msg:
            return None, ["text_after_json_or_two_documents"]
        return None, ["invalid_json_or_text_around_it"]
    except RecursionError:
        return None, ["invalid_json_too_deep"]
    return obj, []


def _id_list(v, where, errors):
    """A valid id list is a list of strings without repeats. Returns sorted list or None."""
    if not isinstance(v, list):
        errors.append(f"{where}:not_a_list")
        return None
    if not all(isinstance(x, str) for x in v):
        errors.append(f"{where}:non_string_id")
        return None
    if len(v) != len(set(v)):
        errors.append(f"{where}:repeated_id")
        return None
    return sorted(v)


def _check_order(oid, g, schema_errors):
    """Structural validation of ONE order value, expected or not. Returns (status, sorted payments or None)."""
    if not isinstance(g, dict):
        schema_errors.append(f"order {oid}:not_object")
        return None, None
    if not all(isinstance(k, str) for k in g.keys()):
        schema_errors.append(f"order {oid}:non_string_key")
    ks = set(map(str, g.keys()))
    if ks - ORDER_KEYS:
        schema_errors.append(f"order {oid}:extra_keys:" + ",".join(sorted(ks - ORDER_KEYS)))
    for k in sorted(ORDER_KEYS - ks):
        schema_errors.append(f"order {oid}:{k}_missing")
    status = g.get("status")
    if "status" in g and not (isinstance(status, str) and status in STATUSES):
        schema_errors.append(f"order {oid}:invalid_status")
    pays = _id_list(g["payments"], f"order {oid}.payments", schema_errors) if "payments" in g else None
    return status, pays


def grade(answer, expected_json: str) -> dict:
    """content_score: each expected order earns 0.5 for the exact status and 0.5 for the exact list of
    linked e2e_ids; orphans earn 1 if exactly right; each extra order adds 1 to the denominator.
    v4: EVERY order present in the answer (expected or invented) is validated structurally first;
    a malformed invented order makes schema_valid False (published 0). A well-formed invented order
    only costs content points. schema_errors make schema_valid False; content_errors only cost points."""
    exp = json.loads(expected_json)
    ans, parse_errors = parse_answer(answer)
    schema_errors = list(parse_errors)
    content_errors: list[str] = []
    detail = {}
    base = {"score": 0.0, "content_score": 0.0, "schema_valid": False, "parsed": False, "perfect": False,
            "orphans_ok": False, "extra_orders": [], "missing_orders": [],
            "schema_errors": schema_errors, "content_errors": content_errors, "errors": [], "detail": detail}
    if not isinstance(ans, dict):
        if ans is not None:
            schema_errors.append("top_level_not_object")
        base["errors"] = schema_errors + content_errors
        return base
    base["parsed"] = True
    if not all(isinstance(k, str) for k in ans.keys()):
        schema_errors.append("top_level:non_string_key")
    keys = set(map(str, ans.keys()))
    if keys - TOP_KEYS:
        schema_errors.append("extra_top_level_keys:" + ",".join(sorted(keys - TOP_KEYS)))
    got_orders = ans.get("orders")
    if not isinstance(got_orders, dict):
        schema_errors.append("orders:missing_or_not_object")
        got_orders = {}
    # 1) structure of every order in the answer, independent of the gold
    checked = {}
    for oid, g in got_orders.items():
        if not isinstance(oid, str):
            schema_errors.append(f"order {oid!r}:non_string_id")
        checked[str(oid)] = _check_order(str(oid), g, schema_errors)
    # 2) content against the gold, expected orders only
    points = 0.0
    missing = []
    for oid, e in exp["orders"].items():
        if oid not in checked:
            content_errors.append(f"order {oid}:missing")
            missing.append(oid)
            status, pays = None, None
        else:
            status, pays = checked[oid]
        st_ok = isinstance(status, str) and status == e["status"]
        pay_ok = pays is not None and pays == e["payments"]
        points += 0.5 * st_ok + 0.5 * pay_ok
        detail[oid] = {"expected": e["status"], "got": status if isinstance(status, (str, type(None))) else repr(status),
                       "status_ok": st_ok, "payments_ok": pay_ok}
    extra = sorted(k for k in checked if k not in exp["orders"])
    if extra:
        content_errors.append("extra_orders:" + ",".join(extra))
    if "orphans" not in ans:
        schema_errors.append("orphans:missing")
        orph = None
    else:
        orph = _id_list(ans["orphans"], "orphans", schema_errors)
    orph_ok = orph is not None and orph == exp["orphans"]
    points += 1.0 * orph_ok
    n = len(exp["orders"]) + 1 + len(extra)
    content = points / n
    valid = not schema_errors
    base.update(content_score=content, schema_valid=valid, score=content if valid else 0.0,
                orphans_ok=orph_ok, extra_orders=extra, missing_orders=missing,
                perfect=(valid and content == 1.0 and not content_errors),
                errors=schema_errors + content_errors)
    return base
