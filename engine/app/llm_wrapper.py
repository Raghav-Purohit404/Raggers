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


def _is_ollama_available() -> bool:
    """
    Lightweight check to avoid blocking calls during EXE startup.
    """
    try:
        import socket
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
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

        if not _is_ollama_available():
            raise RuntimeError(
                "Ollama server is not running on port 11434. "
                "Please start Ollama before querying."
            )

        # 🔒 SINGLE, SAFE INITIALIZATION
        _llm_instance = ChatOllama(
            model="phi3:3.8b",
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
