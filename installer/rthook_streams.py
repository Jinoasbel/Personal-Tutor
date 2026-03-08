"""
rthook_streams.py — PyInstaller runtime hook.
Runs before ANY frozen module is imported.
"""
import sys
import multiprocessing

# ── Fix 1: freeze_support — prevents multiple windows on Windows ──────────────
# Without this PyInstaller re-runs main() for every subprocess/thread spawn,
# opening duplicate windows and crashing workers.
multiprocessing.freeze_support()

# ── Fix 2: null streams — prevents loguru/kokoro NoneType crash ───────────────
# console=False sets sys.stdout/stderr to None. loguru does logger.add(sys.stderr)
# at import time and crashes if it's None.
class _NullWriter:
    def write(self, *a, **kw): pass
    def flush(self, *a, **kw): pass
    def isatty(self): return False

if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()
