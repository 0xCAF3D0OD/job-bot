"""Sans le rôle de l'application, la séparation des comptes serait contournée : une base qui a
les règles de séparation refuse la connexion ; une base pas encore migrée reste joignable
(docs/69 §1)."""

from typing import Any

import pytest

from jobbot.db.base import _on_connect


class FakeConnection:
    def __init__(self, role: bool, policies: bool) -> None:
        self.answers = {"pg_roles": role, "pg_policies": policies}
        self.executed: list[str] = []
        self.last = False

    def cursor(self) -> "FakeConnection":
        return self

    def execute(self, sql: str, _params: Any = None) -> None:
        self.executed.append(sql)
        self.last = next((v for k, v in self.answers.items() if k in sql), False)

    def fetchone(self) -> tuple[int] | None:
        return (1,) if self.last else None

    def close(self) -> None:
        pass

    def commit(self) -> None:
        pass


def test_role_used_when_present() -> None:
    connection = FakeConnection(role=True, policies=True)
    _on_connect(connection, None)
    assert any(sql.startswith("set role") for sql in connection.executed)


def test_missing_role_refused_once_accounts_exist() -> None:
    with pytest.raises(RuntimeError, match="séparation des comptes"):
        _on_connect(FakeConnection(role=False, policies=True), None)


def test_unmigrated_database_still_reachable() -> None:
    _on_connect(FakeConnection(role=False, policies=False), None)


class DirectConnection(FakeConnection):
    """Connecté directement avec un rôle restreint (docs/78 §3.1)."""

    def __init__(self, user: str) -> None:
        super().__init__(role=True, policies=True)
        self.user = user

    def fetchone(self) -> tuple[Any] | None:
        if self.executed[-1] == "select current_user":
            return (self.user,)
        return super().fetchone()


def test_direct_login_needs_nothing() -> None:
    connection = DirectConnection("jobbot_app")
    _on_connect(connection, None)
    assert connection.executed == ["select current_user"]


def test_worker_takes_its_own_role() -> None:
    connection = DirectConnection("dkey")
    _on_connect(connection, None, access="worker")
    assert "set role jobbot_worker" in connection.executed


def test_owner_commands_stay_unrestricted() -> None:
    connection = FakeConnection(role=True, policies=True)
    _on_connect(connection, None, access="admin")
    assert connection.executed == []
