# config_manager.py
import os
import json
from pathlib import Path
import shutil

APP_NAME = "PhiRAG"
DEFAULT_TREE = ["runtime_data", "faiss_index", "metadata", "logs", "watchdog"]

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
    def backend_ingestion_path(self) -> Path:
        return Path(self.data.get("backend_ingestion_path") or self.data.get("watchdog_path", "")).resolve()

    @property
    def faiss_path(self) -> Path:
        return Path(self.data.get("faiss_path", "")).resolve()

    @property
    def metadata_path(self) -> Path:
        return Path(self.data.get("metadata_path", "")).resolve()

    @property
    def faiss_backend_path(self) -> Path:
        return Path(self.data.get("faiss_backend_path") or self.data.get("faiss_path", "")).resolve()

    @property
    def runtime_data_path(self) -> Path:
        return Path(self.data.get("runtime_data_path") or self.data.get("root", "")).resolve()

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
        for k in ("root","watchdog_path","backend_ingestion_path","faiss_path","faiss_backend_path","metadata_path","logs_path","runtime_data_path"):
            if k in data and data[k]:
                data[k] = str(Path(data[k]).resolve())
        if "runtime_data_path" not in data and data.get("root"):
            data["runtime_data_path"] = str((Path(data["root"]) / "runtime_data").resolve())
        if "faiss_backend_path" not in data and data.get("faiss_path"):
            data["faiss_backend_path"] = data["faiss_path"]
        if "backend_ingestion_path" not in data and data.get("watchdog_path"):
            data["backend_ingestion_path"] = data["watchdog_path"]
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
        "backend_ingestion_path": created["watchdog"],
        "faiss_path": created["faiss_index"],
        "faiss_backend_path": created["faiss_index"],
        "runtime_data_path": created["runtime_data"],
        "metadata_path": created["metadata"],
        "logs_path": created["logs"]
    }
