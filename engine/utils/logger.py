# Logger module
import csv
from datetime import datetime
from pathlib import Path
from runtime_paths import QUERY_LOG


def get_query_log_path() -> Path:
    try:
        from GUI.config_manager import AppConfig
        cfg = AppConfig.load()
        if cfg and cfg.logs_path:
            return Path(cfg.logs_path) / "query_logs.csv"
    except Exception:
        pass
    return QUERY_LOG


def log_query(query, response):
    filepath = get_query_log_path()
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create file with header if it doesn't exist
    if not filepath.is_file() or filepath.stat().st_size == 0:
        with filepath.open(mode="w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Query", "Response", "Feedback"])

    # Append the log
    with filepath.open(mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), query, response, ""])
