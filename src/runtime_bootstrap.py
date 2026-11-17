"""Import-time fixes for local Windows dev (onnx DLL, Chroma default embed)."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType


def _onnxruntime_import_ok() -> bool:
    try:
        importlib.import_module("onnxruntime")
        return True
    except Exception:
        return False


def _install_onnxruntime_stub() -> None:
    """Let Chroma import without a working onnxruntime native DLL (offline RAG uses own vectors)."""
    stub = ModuleType("onnxruntime")

    class _InferenceSession:  # noqa: D106 - stub
        def __init__(self, *args, **kwargs):
            pass

        def run(self, *args, **kwargs):
            raise RuntimeError("onnxruntime stub: install VC++ redist or fix onnxruntime")

    stub.InferenceSession = _InferenceSession
    stub.get_device = lambda: "CPU"
    sys.modules["onnxruntime"] = stub


def prepare_runtime() -> None:
    if not _onnxruntime_import_ok():
        _install_onnxruntime_stub()