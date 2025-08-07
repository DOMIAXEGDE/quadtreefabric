# src/quadtreefabric/plugins/java_exec.py

from __future__ import annotations
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Tuple, Dict, Optional

from ..runtime.constants import TIMEOUT

def _find(progs: Iterable[str]) -> Optional[str]:
    """Finds the first available program in a list of executables."""
    for p in progs:
        exe = shutil.which(p)
        if exe:
            return exe
    return None

def _find_main_class(code: str) -> Optional[str]:
    """
    Finds the main class name in a Java source string.
    Looks for a public class with a main method.
    """
    # Regex to find a public class with a main method
    pattern = re.compile(
        r"public\s+class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{"
        r"(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*?"
        r"public\s+static\s+void\s+main\s*\(\s*String\s*\[\s*\]\s*\w+\s*\)"
    )
    match = pattern.search(code)
    if match:
        return match.group(1)

    # Fallback: find the first public class
    fallback_match = re.search(r"public\s+class\s+([a-zA-Z_][a-zA-Z0-9_]*)", code)
    if fallback_match:
        return fallback_match.group(1)

    return None

def _exec(code: str, globals: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Compiles and runs Java code.

    This function first checks for the presence of the Java compiler (javac)
    and the Java runtime (java). It then saves the provided code to a temporary
    .java file, compiles it, and if successful, executes the main class.

    Args:
        code: The Java source code to execute.
        globals: A dictionary for session state (not used for Java).

    Returns:
        A tuple containing a boolean indicating success and a string with
        the output or error message.
    """
    javac = _find(["javac"])
    if not javac:
        return False, "Could not find 'javac'. Please ensure the JDK is installed and in your PATH."

    java = _find(["java"])
    if not java:
        return False, "Could not find 'java'. Please ensure the JRE is installed and in your PATH."

    main_class = _find_main_class(code)
    if not main_class:
        return False, "Could not find a public main class. e.g., 'public class MyClass { public static void main(String[] args) { ... } }'"

    with tempfile.TemporaryDirectory(prefix="java_exec_") as td:
        td_path = Path(td)
        src_file = td_path / f"{main_class}.java"
        src_file.write_text(code, encoding="utf-8")

        # --- Compilation Step ---
        compile_cmd = [javac, str(src_file)]
        try:
            comp_proc = subprocess.run(
                compile_cmd,
                text=True,
                capture_output=True,
                timeout=TIMEOUT,
                cwd=td_path
            )
        except subprocess.TimeoutExpired:
            return False, f"⏱️ Java compilation exceeded {TIMEOUT}s"

        if comp_proc.returncode != 0:
            return False, f"Compilation Error:\n{comp_proc.stdout}{comp_proc.stderr}"

        # --- Execution Step ---
        run_cmd = [java, main_class]
        try:
            run_proc = subprocess.run(
                run_cmd,
                text=True,
                capture_output=True,
                timeout=TIMEOUT,
                cwd=td_path
            )
        except subprocess.TimeoutExpired:
            return False, f"⏱️ Java execution exceeded {TIMEOUT}s"

        ok = run_proc.returncode == 0
        output = run_proc.stdout if ok else f"Runtime Error:\n{run_proc.stdout}{run_proc.stderr}"
        return ok, output

def register(reg):
    """
    Registers the 'java' executor with the application's registry.
    This function is called by the plugin system on startup.
    """
    reg.register("java", _exec)
