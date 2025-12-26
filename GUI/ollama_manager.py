# ollama_manager.py
import shutil
import subprocess
import webbrowser
from typing import List

OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/windows"
DEFAULT_MODEL = "phi3.8b"

def is_ollama_installed(cmd="ollama") -> bool:
    return shutil.which(cmd) is not None

def list_ollama_models(cmd="ollama") -> List[str]:
    if not is_ollama_installed(cmd):
        return []
    try:
        out = subprocess.check_output([cmd, "list"], stderr=subprocess.STDOUT, text=True, timeout=5)
        models = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            models.append(line.split()[0])
        return models
    except Exception:
        return []

def open_ollama_download_page():
    webbrowser.open(OLLAMA_DOWNLOAD_URL)

def try_pull_model(model_name: str, cmd="ollama") -> bool:
    """
    Optionally allow user to try `ollama pull <model>` if ollama is present.
    Returns True on success (exit code 0), False otherwise.
    """
    if not is_ollama_installed(cmd):
        return False
    try:
        subprocess.check_call([cmd, "pull", model_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        return True
    except Exception:
        return False
