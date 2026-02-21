"""
Unit test fixtures — load each service module exactly once to prevent
Prometheus duplicate-registration errors across test files.
"""

import importlib.util
import os
import sys


def _load_once(alias: str, svc_dir: str, filename: str):
    """Load a module from an explicit path, registering under `alias`.
    Skips exec if already loaded (prevents Prometheus double-registration)."""
    if alias in sys.modules:
        return sys.modules[alias]
    path = os.path.join(os.path.dirname(__file__), svc_dir, filename)
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# ── emotion-regulator ────────────────────────────────────────────────────────
_er_dir = "../../services/emotion-regulator"
er_metrics = _load_once("er_metrics", _er_dir, "metrics.py")
sys.modules["metrics"] = er_metrics  # satisfies `import metrics as m` in er/main.py
er_main = _load_once("er_main", _er_dir, "main.py")

# ── language-center ──────────────────────────────────────────────────────────
_lc_dir = "../../services/language-center"
lc_metrics = _load_once("lc_metrics", _lc_dir, "metrics.py")
sys.modules["metrics"] = lc_metrics  # lc/main.py also does `from metrics import ...`
lc_templates = _load_once("lc_templates", _lc_dir, "templates.py")
sys.modules["templates"] = lc_templates
lc_main = _load_once("lc_main", _lc_dir, "main.py")

# ── central-agent ────────────────────────────────────────────────────────────
_ca_dir = "../../services/central-agent"
ca_metrics = _load_once("ca_metrics", _ca_dir, "metrics.py")
sys.modules["metrics"] = ca_metrics
ca_main = _load_once("ca_main", _ca_dir, "main.py")

# ── memory-manager ───────────────────────────────────────────────────────────
_mm_dir = "../../services/memory-manager"
mm_metrics = _load_once("mm_metrics", _mm_dir, "metrics.py")
sys.modules["metrics"] = mm_metrics
mm_main = _load_once("mm_main", _mm_dir, "main.py")
