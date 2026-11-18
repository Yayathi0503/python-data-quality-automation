import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from audit import audit

ROOT = Path(__file__).parent


def test_cli_findings_and_append_history(tmp_path):
    command = [sys.executable, str(ROOT / "audit.py"), str(ROOT / "examples/orders.csv"),
               "--db", str(tmp_path / "history.db")]
    for _ in range(2):
        run = subprocess.run(command, capture_output=True, text=True)
        assert run.returncode == 1
        report = json.loads(run.stdout)
        assert report["rows"] == 4 and report["invalid_rows"] == 2
        assert report["issues"][0] == {"record": 3, "rules": ["duplicate_id", "invalid_amount"]}
    with sqlite3.connect(tmp_path / "history.db") as db:
        assert db.execute("SELECT row_count, invalid_rows FROM audits").fetchall() == [(4, 2)] * 2


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "abc", "-0.01"])
def test_invalid_amount(tmp_path, amount):
    path = tmp_path / "orders.csv"
    path.write_text(f"order_id,amount,currency\na,{amount},USD\n")
    assert audit(path)["issues"][0]["rules"] == ["invalid_amount"]


def test_valid_rows_and_utf8_bom(tmp_path):
    path = tmp_path / "orders.csv"
    path.write_text("order_id,amount,currency\nA,0.00,INR\n", encoding="utf-8-sig")
    assert audit(path) == {"rows": 1, "invalid_rows": 0, "issues": []}


def test_invalid_schema(tmp_path):
    path = tmp_path / "orders.csv"
    path.write_text("order_id,amount,amount\n")
    with pytest.raises(ValueError, match="headers"):
        audit(path)
