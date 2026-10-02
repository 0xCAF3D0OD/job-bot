from pathlib import Path

import pytest

from jobbot.storage.local import LocalStorage


def test_put_get_delete(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    storage.put("documents/cv.pdf", b"%PDF")
    assert storage.exists("documents/cv.pdf")
    assert storage.get("documents/cv.pdf") == b"%PDF"
    storage.delete("documents/cv.pdf")
    assert not storage.exists("documents/cv.pdf")


@pytest.mark.parametrize("key", ["../evade.txt", "/etc/passwd", "a/../../b", ""])
def test_keys_cannot_escape_root(tmp_path: Path, key: str) -> None:
    with pytest.raises(ValueError):
        LocalStorage(tmp_path).put(key, b"x")
