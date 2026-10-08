# PixRecon frozen prompt

This is the complete prompt source used by the audited seven-model grid. The same rule text is used for every case; only the orders and statement inputs change.

## Complete rules and answer schema

```text
You are reconciling a Brazilian merchant's Pix bank statement against its order list.

Rules:
1. Each statement line has an e2e_id. If the same e2e_id appears more than once, it is the same transfer exported twice: count it once.
2. Link a payment to an order by txid when present; otherwise by an order id written in the description. Never link by amount or payer name alone.
3. Amounts may be written as "R$ 1.234,56", "1.234,56" or "1234.56". A refund line has a negative amount and a refers_to field with the e2e_id of the payment it returns.
4. Times may be in UTC ("Z") or in -03:00. Compare instants, not clock text.
5. Status of each order, using the amount received in distinct transfers:
   - "unpaid": no linked payment.
   - "paid": exactly the order amount received, at or before expires_at.
   - "late_paid": exactly the order amount received, after expires_at.
   - "underpaid": less than the order amount received.
   - "overpaid": more than the order amount received (for example, two different transfers).
   - "refunded": the linked payment was fully returned by a refund line.
6. "payments" lists every distinct e2e_id linked to the order, including refund lines, sorted.
7. "orphans" lists distinct e2e_ids of payment lines that cannot be linked to any order, sorted.
8. Refunds: an order is refunded only when the refunds linked to it add up to exactly the total of its linked payments. A partial refund does not change the status; the refund line is still listed in "payments".
9. If more than one status could apply, use the first that applies in this order: unpaid, refunded, underpaid, overpaid, late_paid, paid. A payment exactly at expires_at is on time.
10. Every order from the order list must appear once in "orders"; do not add other ids.
11. Status uses the gross amount received in payment lines; a partial refund is not subtracted. created_at is not used by any rule.
12. When several transfers are linked to one order, compare the time of the latest one with expires_at.
13. "orphans" contains payment lines only: a refund line is never an orphan, even if its refers_to points to an orphan payment or to nothing.

Answer with exactly one JSON object and nothing else (no text before or after; one Markdown json code block around it is accepted). Exact schema, no other keys:
{"orders": {"<order_id>": {"status": "...", "payments": ["..."]}}, "orphans": ["..."]}
```

## Exact input construction

Read orders_json and statement_json from the same case in cases/CASES.json. Parse both JSON strings, then build the input exactly as below. RULES is the full text above, without adding or removing any rule.

```python
import json

def build_prompt(orders_json: str, statement_json: str) -> str:
    orders = json.loads(orders_json)
    statement = json.loads(statement_json)
    return (
        RULES
        + "\n\nOrders:\n" + json.dumps(orders, ensure_ascii=False, indent=1)
        + "\n\nStatement:\n" + json.dumps(statement, ensure_ascii=False, indent=1)
    )
```

The preserved implementation is prompt/prompt.py. The document records the frozen source; it does not claim a new Kaggle generation, model run or publication.

Source SHA256 (prompt.py): 6ebe0f794a9601bf1ae18c531b4712eb8a8e3b4cfff385ca0c9730302d694fc3
