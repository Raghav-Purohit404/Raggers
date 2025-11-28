# config_manager.py
import os
import json
from pathlib import Path
import shutil

APP_NAME = "PhiRAG"
DEFAULT_TREE = ["faiss_index", "metadata", "logs", "watchdog"]

def appdata_config_path():
    appdata = os.getenv("APPDATA") or str(Path.home() / ".config")
    cfg_dir = Path(appdata) / APP_NAME
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"

def default_subfolders():
    return DEFAULT_TREE

class AppConfig:
    def __init__(self, data: dict):
        self.data = data

    @property
    def root(self) -> Path:
        val = self.data.get("root", "")
        return Path(val).resolve() if val else None

    @property
    def watchdog_path(self) -> Path:
        return Path(self.data.get("watchdog_path", "")).resolve()

    @property
    def faiss_path(self) -> Path:
        return Path(self.data.get("faiss_path", "")).resolve()

    @property
    def metadata_path(self) -> Path:
        return Path(self.data.get("metadata_path", "")).resolve()

    @property
    def logs_path(self) -> Path:
        return Path(self.data.get("logs_path", "")).resolve()

    @property
    def ollama_model(self) -> str:
        return self.data.get("ollama_model", "")

    @property
    def ollama_url(self) -> str:
        return self.data.get("ollama_url", "http://127.0.0.1:11434")

    def save(self) -> Path:
        p = appdata_config_path()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        return p

    @classmethod
    def load(cls):
        p = appdata_config_path()
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        # resolve stored paths to absolute form
        for k in ("root","watchdog_path","faiss_path","metadata_path","logs_path"):
            if k in data and data[k]:
                data[k] = str(Path(data[k]).resolve())
        return AppConfig(data)

def ensure_tree(root: Path):
    """Create canonical folder tree under chosen root and return dict of paths."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    created = {}
    for sub in default_subfolders():
        p = (root / sub).resolve()
        p.mkdir(parents=True, exist_ok=True)
        created[sub] = str(p)
    return {
        "root": str(root),
        "watchdog_path": created["watchdog"],
        "faiss_path": created["faiss_index"],
        "metadata_path": created["metadata"],
        "logs_path": created["logs"]
    }
