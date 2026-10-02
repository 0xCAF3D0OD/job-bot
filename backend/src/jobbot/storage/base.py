"""Stockage des fichiers (CV, certificats, exports ORP).

L'application n'écrit des fichiers que par cette interface. Le disque local est le seul
backend en 0.1 ; un backend S3 pourra s'ajouter sans toucher au reste du code.
"""

from typing import Protocol

from jobbot.settings import Settings, StorageBackend


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...


def create_storage(settings: Settings) -> Storage:
    from jobbot.storage.local import LocalStorage

    match settings.storage_backend:
        case StorageBackend.LOCAL:
            return LocalStorage(settings.storage_path)
