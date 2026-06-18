import os
import sys
import tempfile
from pathlib import Path


APP_NAME = "Raggers"
IS_FROZEN = bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    if IS_FROZEN:
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_dir()
INTERNAL_DIR = APP_DIR / "_internal"


def resource_dir() -> Path:
    if IS_FROZEN and (INTERNAL_DIR / "engine").exists():
        return INTERNAL_DIR
    return APP_DIR


ROOT_DIR = APP_DIR
RESOURCE_DIR = resource_dir()
ENGINE_DIR = RESOURCE_DIR / "engine"
GUI_DIR = RESOURCE_DIR / "GUI"
DATA_DIR = RESOURCE_DIR / "data"


def is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def log_dir() -> Path:
    local_logs = APP_DIR / "logs"
    if is_writable_dir(local_logs):
        return local_logs

    candidates = []
    for env_name in ("LOCALAPPDATA", "APPDATA", "TEMP", "TMP"):
        env_value = os.getenv(env_name)
        if env_value:
            candidates.append(Path(env_value) / APP_NAME / "logs")
    candidates.append(Path(tempfile.gettempdir()) / APP_NAME / "logs")
    candidates.append(Path.home() / f".{APP_NAME.lower()}" / "logs")

    for candidate in candidates:
        if is_writable_dir(candidate):
            return candidate

    return local_logs


LOG_DIR = log_dir()

STREAMLIT_APP = ENGINE_DIR / "app" / "interface.py"
STARTUP_LOG = LOG_DIR / "startup.log"
ERROR_LOG = LOG_DIR / "error.log"
QUERY_LOG = LOG_DIR / "query_logs.csv"
FAISS_INDEX_DIR = DATA_DIR / "combined_faiss_index"
FAISS_BACKEND_DIR = DATA_DIR / "faiss_backend"
EMBEDDING_MODEL_DIR = DATA_DIR / "models" / "all-MiniLM-L6-v2"


def bundled_python() -> Path:
    return INTERNAL_DIR / "python.exe"


def ensure_runtime_environment() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if str(RESOURCE_DIR) not in sys.path:
        sys.path.insert(0, str(RESOURCE_DIR))

    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    os.environ.setdefault("RAGGERS_ROOT", str(ROOT_DIR))
    os.environ.setdefault("RAGGERS_RESOURCE_DIR", str(RESOURCE_DIR))
    os.environ.setdefault("RAGGERS_DATA_DIR", str(DATA_DIR))
    os.environ.setdefault("RAGGERS_LOG_DIR", str(LOG_DIR))
    os.environ.setdefault("RAGGERS_FAISS_INDEX", str(FAISS_INDEX_DIR))
    os.environ.setdefault("RAGGERS_FAISS_BACKEND", str(FAISS_BACKEND_DIR))
    os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")

    if EMBEDDING_MODEL_DIR.exists():
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(DATA_DIR / "models"))
        os.environ.setdefault("HF_HOME", str(DATA_DIR / "models"))
        os.environ.setdefault("TRANSFORMERS_CACHE", str(DATA_DIR / "models"))


def required_runtime_paths() -> list[Path]:
    required = [
        ENGINE_DIR,
        GUI_DIR,
        DATA_DIR,
        STREAMLIT_APP,
    ]
    if IS_FROZEN:
        required.append(INTERNAL_DIR)
    return required


def missing_runtime_paths() -> list[Path]:
    return [path for path in required_runtime_paths() if not path.exists()]


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        try:
            return str(path.relative_to(RESOURCE_DIR))
        except ValueError:
            return str(path)
