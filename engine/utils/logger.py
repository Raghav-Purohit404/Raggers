# Logger module
import csv
from datetime import datetime
from runtime_paths import QUERY_LOG


def log_query(query, response):
    QUERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    filepath = QUERY_LOG

    # Create file with header if it doesn't exist
    if not filepath.is_file():
        with filepath.open(mode="w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Query", "Response"])

    # Append the log
    with filepath.open(mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), query, response])
