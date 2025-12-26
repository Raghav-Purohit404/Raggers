# Logger module
import csv
from datetime import datetime
import os

LOG_FILE = "query_logs.csv"

def log_query(query, response):
    os.makedirs("logs", exist_ok=True)
    filepath = os.path.join("logs", LOG_FILE)

    # Create file with header if it doesn't exist
    if not os.path.isfile(filepath):
        with open(filepath, mode="w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Query", "Response"])

    # Append the log
    with open(filepath, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), query, response])
