"""Le dépôt est public : aucune donnée personnelle ne doit y être suivie."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_data_dir_is_not_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "data/", ".env"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert tracked == []


def test_gitignore_covers_personal_data() -> None:
    lines = (REPO_ROOT / ".gitignore").read_text().splitlines()
    assert "data/" in lines
    assert ".env" in lines
