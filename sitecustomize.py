"""Bootstrap runtime hooks for Liya.
Preserves the existing Greenleaf runtime hook and explicitly loads the marketing lesson extension.
"""
from sitecustomize_legacy import *  # noqa: F401,F403

try:
    import usercustomize  # noqa: F401
    import marketing_lesson5_mentor_fix  # noqa: F401
    print("GREENLEAF marketing extension explicitly loaded", flush=True)
except Exception as exc:
    print(f"GREENLEAF marketing extension failed: {type(exc).__name__}: {exc}", flush=True)
