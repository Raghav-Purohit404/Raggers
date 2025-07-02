import csv
from datetime import datetime
import os

LOG_FILE = "query_logs.csv"

def log_query(query, response):
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    filepath = os.path.join(logs_dir, LOG_FILE)

    if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
        with open(filepath, mode="w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Query", "Response", "Feedback"])

    with open(filepath, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), query, response, ""])
