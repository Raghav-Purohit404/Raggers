import subprocess
import sys
import json
from pathlib import Path

from runtime_paths import ENGINE_DIR, ROOT_DIR, bundled_python, ensure_runtime_environment, IS_FROZEN

ensure_runtime_environment()
ENGINE_PATH = ENGINE_DIR / "engine_main.py"


def python_runtime() -> str:
    if IS_FROZEN:
        return str(bundled_python())
    return sys.executable


def run_engine_query(query: str) -> dict:
    """
    Runs the engine as a subprocess and returns parsed JSON.
    """
    cmd = [
        python_runtime(),
        str(ENGINE_PATH),
        "--query",
        query
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR)
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
