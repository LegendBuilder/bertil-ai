import os
import sys


def _ensure_repo_root_on_path() -> None:
    """Prepend repo root to sys.path so `import services.*` works in tests.
    This avoids needing editable installs during CI/local runs.
    """
    current_dir = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


_ensure_repo_root_on_path()
