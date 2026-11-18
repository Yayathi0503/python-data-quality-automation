"""Audit an orders CSV and optionally append its summary to SQLite."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3


def audit(path):
    issues = []
    ids = set()
    rows = 0
    invalid_rows = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        required = {"order_id", "amount", "currency"}
        if not required.issubset(headers) or len(headers) != len(set(headers)):
            raise ValueError("Expected unique headers including order_id, amount, currency")
        for rows, row in enumerate(reader, 1):
            reasons = []
            if None in row or None in row.values():
                reasons.append("column_count")
            order_id = (row["order_id"] or "").strip()
            if not order_id:
                reasons.append("missing_id")
            elif order_id in ids:
                reasons.append("duplicate_id")
            ids.add(order_id)
            try:
                amount = Decimal(row["amount"] or "")
                if not amount.is_finite() or amount < 0:
                    reasons.append("invalid_amount")
            except InvalidOperation:
                reasons.append("invalid_amount")
            if (row["currency"] or "").strip() not in {"USD", "EUR", "INR"}:
                reasons.append("unsupported_currency")
            if reasons:
                invalid_rows += 1
                issues.append({"record": rows, "rules": reasons})
    return {"rows": rows, "invalid_rows": invalid_rows, "issues": issues}


def save_summary(path, source, report):
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            filename TEXT, row_count INTEGER, invalid_rows INTEGER)""")
        db.execute("INSERT INTO audits(filename, row_count, invalid_rows) VALUES (?, ?, ?)",
                   (source.name, report["rows"], report["invalid_rows"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.csv_file)
        if args.db:
            if args.db.resolve() == args.csv_file.resolve():
                raise ValueError("Choose a separate SQLite file")
            save_summary(args.db, args.csv_file, result)
    except (ValueError, OSError, csv.Error, sqlite3.Error) as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(result, indent=2))
    return int(result["invalid_rows"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
