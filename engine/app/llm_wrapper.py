# llm_wrapper.py
import os
import sys
import threading
from typing import Optional

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# ─────────────────────────────────────────────────────────────
# GLOBAL SINGLETON LOCK (CRITICAL FOR EXE SAFETY)
# ─────────────────────────────────────────────────────────────
_llm_instance = None
_llm_lock = threading.Lock()


def _is_ollama_available(host: str = "127.0.0.1", port: int = 11434) -> bool:
    """
    Lightweight check to avoid blocking calls during EXE startup.
    """
    try:
        import socket
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False


def get_llm() -> ChatOllama:
    """
    Lazily initialize ChatOllama exactly ONCE.
    Prevents:
    - recursive spawning
    - repeated model loads
    - EXE hang / RAM explosion
    """
    global _llm_instance

    if _llm_instance is not None:
        return _llm_instance

    with _llm_lock:
        if _llm_instance is not None:
            return _llm_instance

        # Load user configuration dynamically if available
        cfg = None
        try:
            from GUI.config_manager import AppConfig
            cfg = AppConfig.load()
        except Exception:
            pass

        model_name = "phi3:3.8b"
        base_url = "http://127.0.0.1:11434"
        if cfg:
            if cfg.ollama_model:
                model_name = cfg.ollama_model
            if cfg.ollama_url:
                base_url = cfg.ollama_url

        # Parse host and port for availability check
        host, port = "127.0.0.1", 11434
        if base_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                host = parsed.hostname or "127.0.0.1"
                port = parsed.port or 11434
            except Exception:
                pass

        if not _is_ollama_available(host, port):
            raise RuntimeError(
                f"Ollama server is not running at {host}:{port}. "
                "Please start Ollama before querying."
            )

        # 🔒 SINGLE, SAFE INITIALIZATION
        _llm_instance = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.7,
            timeout=120
        )

        return _llm_instance


def get_llm_response(prompt: str, word_limit: Optional[int] = None) -> str:
    """
    Generate a response from Phi-3 via Ollama with strong word-count guidance.
    EXE-safe, rerun-safe, singleton-safe.
    """
    try:
        llm = get_llm()

        if word_limit:
            system_instruction = (
                f"You are a helpful assistant. "
                f"Answer in approximately {word_limit} words. "
                f"Stay close to the requested length. "
                f"Be clear, structured, and complete."
            )
        else:
            system_instruction = (
                "You are a helpful assistant. "
                "Answer clearly and concisely."
            )

        response = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=prompt)
        ])

        return response.content

    except Exception as e:
        return f"⚠️ Error generating response: {e}"
