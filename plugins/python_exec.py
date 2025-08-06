import io
import contextlib
import threading

from runtime.constants import TIMEOUT, STATUS_Q


def _exec(code: str, g: dict | None = None) -> tuple[bool, str]:
    """Execute Python code with an optional shared globals dict."""
    ns = g if g is not None else {}
    ns["status_q"] = STATUS_Q
    buf = io.StringIO()

    def target() -> None:
        with contextlib.redirect_stdout(buf):
            exec(code, ns)

    t = threading.Thread(target=target)
    t.start()
    t.join(TIMEOUT)
    if t.is_alive():
        return False, "⏱️ Timeout"
    return True, buf.getvalue()


def register(reg):
    reg.register("python", _exec)

