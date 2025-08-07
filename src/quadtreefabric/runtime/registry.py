import importlib
import os
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Tuple, Optional

from .session import ExecutorSession

# --- Helper function to determine the correct base path ---
def get_base_path():
    """Get the base path for the application, whether running from source or bundled."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running as a normal script
        # Assumes this file is at src/quadtreefabric/runtime/registry.py
        return Path(__file__).parent.parent.parent.parent

# --- Original classes ---
ExecutorFn = Callable[[str, dict | None], Tuple[bool, str]]
_THROTTLE = 0.25  # seconds


class ExecutorRegistry:
    """Global store for language executors."""

    def __init__(self) -> None:
        self._exec: Dict[str, ExecutorFn] = {}
        self._sessions: Dict[str, ExecutorSession] = {}
        self._last_tick = 0.0
        self._discover()

    def register(self, lang: str, fn: ExecutorFn) -> None:
        self._exec[lang.lower()] = fn

    def unregister(self, lang: str) -> None:
        self._exec.pop(lang.lower(), None)

    def list_languages(self):
        return sorted(self._exec)

    def has(self, lang: str) -> bool:
        return lang.lower() in self._exec

    def get(self, lang: str) -> Optional[ExecutorFn]:
        return self._exec.get(lang.lower())

    def execute(self, code: str, lang: str) -> Tuple[bool, str]:
        fn = self.get(lang)
        if not fn:
            return False, f"No executor for {lang}. Install a plugin."
        sess = self._sessions.setdefault(lang, ExecutorSession(fn))
        return sess.exec(code)[:2]

    # ---------- REVISED DISCOVERY MECHANISM ----------
    def _discover(self) -> None:
        """
        Discover and load executors by directly scanning the plugins directory.
        This method is compatible with both normal execution and PyInstaller bundles.
        """
        base_path = get_base_path()
        # Path is now relative to the package root
        plugins_dir = base_path / "src" / "quadtreefabric" / "plugins"

        if not plugins_dir.is_dir():
            # Also check for plugins dir relative to this file for development
            local_plugins_dir = Path(__file__).parent.parent / "plugins"
            if local_plugins_dir.is_dir():
                plugins_dir = local_plugins_dir
            else:
                return

        for file in plugins_dir.glob("*.py"):
            if file.stem.startswith("__"):
                continue

            try:
                # Construct the full module path for importlib
                module_name = f"quadtreefabric.plugins.{file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, str(file))

                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)

                    if hasattr(mod, "register"):
                        mod.register(self)

            except Exception as e:
                print(f"[exec] Failed to load plugin {file.name}: {e}")

    def tick(self) -> None:
        now = time.perf_counter()
        if now - self._last_tick > _THROTTLE:
            self._discover()
            self._last_tick = now


REGISTRY = ExecutorRegistry()
