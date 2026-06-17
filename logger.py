import csv
from datetime import datetime
import os
from runtime_paths import QUERY_LOG


def log_query(query, response):
    QUERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    filepath = QUERY_LOG

    if not filepath.is_file() or filepath.stat().st_size == 0:
        with filepath.open(mode="w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Query", "Response", "Feedback"])

    with filepath.open(mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), query, response, ""])
