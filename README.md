# Order data quality automation

Audit a CSV export before importing orders. The command reports each invalid record and its failed rules as JSON. An optional SQLite file keeps a history of row counts across runs.

## Run the demo

Use Python 3.12. From the repository root, create a virtual environment with `python -m venv .venv`. Activate it (`.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux), then run:

```sh
python -m pip install -r requirements.txt
python -m pytest -q
```

```sh
python audit.py examples/orders.csv --db history.db
```

The example has four orders. Record 3 repeats an ID and has a negative amount. Record 4 has an unsupported currency. Both appear in the report. Query the stored summaries with `SELECT filename, row_count, invalid_rows FROM audits ORDER BY id;`.

## File and exit conventions

Provide a UTF-8 CSV with unique column headers including `order_id`, `amount`, and `currency`. Extra named columns are accepted. IDs must be nonempty and unique after trimming. Amounts must be finite and nonnegative. Accepted currencies are INR, USD and EUR. Record numbers count data records from one, excluding the header.

Exit code 0 means validation passed, 1 means the report contains invalid records, and 2 means the input, schema or storage operation failed. Each completed invocation with `--db` appends one summary, including runs with validation findings. The process keeps distinct IDs and issue details in memory.
