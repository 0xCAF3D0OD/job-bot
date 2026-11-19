"""« Tes droits » (§72r, §72t, §72v) : règles de docs/droits, ta situation dans le compte, chiffres
jamais devinés.
"""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from jobbot import accounts
from jobbot.auth import passwords
from jobbot.db.models import User
from jobbot.droits import regles
from jobbot.droits import service as droits
from jobbot.droits.service import Situation
from jobbot.runtime import Runtime

from .conftest import admin_engine

RULES = regles.load()


def _figs(**fields: object) -> droits.Figures:
    return droits.figures(RULES, Situation(**fields))  # type: ignore[arg-type]


def test_the_rules_file_is_complete_and_sourced() -> None:
    """Chaque rubrique, chaque ligne affichée et chaque paramètre a sa source et sa date (§72r point
    6).
    """
    for key in regles.TOPICS:
        section = RULES.section(key)
        assert section.get("Vérifié") == "2026-11-19"
        assert section.get("Phrase source")
        lines = RULES.lines(key)
        assert len(lines) in (3, 4)
        assert all(line.title and line.detail and line.source for line in lines)
    for row in RULES.section("paramètres").tables[0]:
        assert row["Source"] and date.fromisoformat(row["Vérifié"])
    for row in RULES.section("assistant").tables[0]:
        assert row["Source"]


@pytest.mark.parametrize(
    ("age", "children", "months", "expected"),
    [
        ("moins_25", False, "12_17", 200),
        ("moins_25", False, "22_24", 200),
        ("moins_25", True, "12_17", 260),
        ("moins_25", True, "18_21", 400),
        ("25_54", None, "12_17", 260),
        ("25_54", False, "18_21", 400),
        ("25_54", True, "22_24", 400),
        ("55_plus", None, "18_21", 400),
        ("55_plus", False, "22_24", 520),
    ],
)
def test_the_number_of_allowances(
    age: str, children: bool | None, months: str, expected: int
) -> None:
    """Art. 27 al. 2 et 5bis LACI : 200, 260, 400 ou 520 au plus."""
    assert _figs(age=age, enfants=children, mois=months).total == expected


def test_under_25_needs_to_know_about_children() -> None:
    assert _figs(age="moins_25", mois="18_21").total is None


@pytest.mark.parametrize(
    ("children", "gain", "expected"),
    [
        (True, None, 80),
        (True, 9000, 80),
        (False, 3797, 80),
        (False, 3798, 70),
        (False, None, None),
        (None, 3000, None),
    ],
)
def test_the_rate(children: bool | None, gain: int | None, expected: int | None) -> None:
    """80 % avec des enfants, ou un gain assuré jusqu'à 3 797 francs (140 francs par jour), sinon 70
    %.
    """
    assert _figs(enfants=children, gain=gain).taux == expected


def test_remaining_days_and_end_of_the_frame() -> None:
    figs = _figs(
        age="25_54", mois="18_21", enfants=False, touchees=88, inscription=date(2026, 4, 1)
    )
    assert (figs.total, figs.restants) == (400, 312)
    assert figs.fin == date(2028, 3, 31)
    # Sans les indemnités touchées : le total est connu, pas ce qui reste.
    assert _figs(age="25_54", mois="18_21").restants is None
    assert _figs(inscription=date(2024, 2, 29)).fin == date(2026, 2, 27)


def test_holidays() -> None:
    """5 jours par tranche de 60 ; disponibles = acquis moins pris ; sinon les acquis seuls."""
    assert (_figs(touchees=125).vacances_acquis, _figs(touchees=125).vacances_disponibles) == (
        10,
        None,
    )
    assert _figs(touchees=125, vacances_prises=5).vacances_disponibles == 5
    assert _figs(touchees=59).vacances_acquis == 0
    assert _figs().vacances_acquis is None


def test_nothing_known_nothing_shown() -> None:
    figs = _figs()
    assert (figs.total, figs.restants, figs.taux, figs.fin) == (None, None, None, None)
    assert not figs.avs and _figs(age="55_plus").avs


def test_the_assistant_never_sees_the_figures() -> None:
    """L'Assistant écrit {{clé}} ; le chiffre est mis à l'affichage, même coupé en deux."""
    filled = droits.values(_figs(age="25_54", mois="18_21", touchees=88, vacances_prises=0))
    assert filled["jours_restants"] == "312 jours" and filled["vacances"] == "5 jours disponibles"
    assert filled["taux"] == droits.MISSING
    filler = droits.Filler(filled)
    out = (
        filler.feed("Il te reste {")
        + filler.feed("{ jours_")
        + filler.feed("restants}} et {{inconnu}}.")
    )
    assert out + filler.flush() == "Il te reste 312 jours et ."


async def test_your_situation_round_trip(client: AsyncClient, runtime: Runtime) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM settings WHERE key = 'droits_situation'"))
    try:
        page = (await client.get("/api/droits")).json()
        assert page["figures"]["restants"] is None and page["situation_complete"] is False
        assert [topic["key"] for topic in page["topics"]] == list(regles.TOPICS)
        assert page["texts"]["Fin"] == "Fin estimée"
        saved = await client.put(
            "/api/droits/situation",
            json={
                "inscription": "2026-04-01",
                "mois": "18_21",
                "age": "25_54",
                "enfants": False,
                "gain": 6200,
                "touchees": 88,
            },
        )
        assert saved.status_code == 200 and saved.json()["vacances_prises"] is None
        figures = (await client.get("/api/droits")).json()["figures"]
        assert figures | {"avs": False} == {
            "total": 400,
            "restants": 312,
            "taux": 70,
            "fin": "2028-03-31",
            "vacances_acquis": 5,
            "vacances_disponibles": None,
            "avs": False,
        }
        assert (await client.put("/api/droits/situation", json={"age": "60"})).status_code == 422
        assert (await client.put("/api/droits/situation", json={"gain": -1})).status_code == 422
        # Tout vidé : rien n'est gardé.
        await client.put("/api/droits/situation", json={})
        async with admin_engine().begin() as conn:
            left = await conn.scalar(
                text("SELECT count(*) FROM settings WHERE key = 'droits_situation'")
            )
        assert left == 0
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM settings WHERE key = 'droits_situation'"))


async def test_your_situation_stays_in_your_account(runtime: Runtime) -> None:
    """Un autre compte ne voit pas ta situation (C-1, C-4)."""
    owner = accounts.current()
    async with runtime.sessionmaker.begin() as session:
        await droits.save(session, Situation(age="25_54", gain=5000))
        other = User(username="droits-autre", password_hash=passwords.hash_password("x" * 12))
        session.add(other)
        await session.flush()
        other_id = other.id
    accounts.set_current(other_id)
    try:
        async with runtime.sessionmaker() as session:
            assert await droits.load(session) == Situation()
    finally:
        accounts.set_current(owner)
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": other_id})
            await conn.execute(text("DELETE FROM settings WHERE key = 'droits_situation'"))
