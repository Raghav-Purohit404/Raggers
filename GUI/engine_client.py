import subprocess
import sys
import json
from pathlib import Path


ENGINE_PATH = Path(__file__).resolve().parents[1] / "engine" / "engine_main.py"


def run_engine_query(query: str) -> dict:
    """
    Runs the engine as a subprocess and returns parsed JSON.
    """
    cmd = [
        sys.executable,
        str(ENGINE_PATH),
        "--query",
        query
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "error": "Engine process failed",
            "stderr": result.stderr
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON from engine",
            "raw_output": result.stdout
        }
