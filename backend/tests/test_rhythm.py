"""Le bon rythme (docs/86) : l'objectif réparti par semaine, la dose du jour, le message des
offres une fois par jour, et le téléphone silencieux les jours sans recherche."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from jobbot.db.models import Application, Evaluation, Notification, Offer, OfferStatus, Setting
from jobbot.notify import service as notify
from jobbot.notify.service import Message
from jobbot.rhythm import service as rhythm
from jobbot.runtime import Runtime
from jobbot.settings import Settings

from .conftest import admin_engine, make_settings

ZURICH = ZoneInfo("Europe/Zurich")
WEEKDAYS = rhythm.Rhythm((0, 1, 2, 3, 4))
KEYS = (
    "'orp_monthly_target', 'rhythm_days', 'offers_notify_mode', 'offers_notify_hour', "
    "'offers_digest_day', 'notify_score_threshold', 'rhythm_pause_from', 'rhythm_pause_until', "
    "'rhythm_signal_week'"
)


@pytest.fixture
async def rt(runtime: Runtime) -> AsyncIterator[Runtime]:
    async def reset() -> None:
        async with admin_engine().begin() as conn:
            await conn.execute(text("TRUNCATE applications, offers, notifications CASCADE"))
            await conn.execute(text(f"DELETE FROM settings WHERE key IN ({KEYS})"))

    await reset()
    r = Runtime.create(make_settings(ntfy_topic="sujet", public_url="http://jobbot.local"))
    yield r
    await r.dispose()
    await reset()


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[Message]:
    messages: list[Message] = []

    async def fake_send(_settings: Settings, message: Message) -> None:
        messages.append(message)

    monkeypatch.setattr(notify, "send", fake_send)
    return messages


def test_the_month_spread_over_the_weeks() -> None:
    # Octobre 2026 : 22 jours de semaine ; le 1er est un jeudi.
    assert rhythm.week_target(10, 0, date(2026, 10, 1), WEEKDAYS) == 1  # jeudi et vendredi
    # Une candidature la première semaine : les 9 qui restent, sur 20 jours, 5 cette semaine.
    assert rhythm.week_target(10, 1, date(2026, 10, 7), WEEKDAYS) == 3
    # En retard la dernière semaine : tout ce qui reste, sans plus.
    assert rhythm.week_target(10, 4, date(2026, 10, 28), WEEKDAYS) == 6
    assert rhythm.week_target(10, 12, date(2026, 10, 14), WEEKDAYS) == 0  # objectif atteint
    # Trois jours de recherche : 13 jours en octobre, 3 cette semaine.
    assert rhythm.week_target(10, 0, date(2026, 10, 5), rhythm.Rhythm((0, 2, 4))) == 3
    # Un week-end, sans jour de recherche cette semaine-là.
    assert rhythm.week_target(10, 0, date(2026, 11, 1), WEEKDAYS) == 0


async def _application(rt: Runtime, sent_at: date) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(
            Application(
                sent_at=sent_at,
                method="electronique",
                company="Acme SA",
                job_title="DevOps",
                orp_month=f"{sent_at:%Y-%m}",
            )
        )


async def _offer(rt: Runtime, n: int, score: int, scored_at: datetime) -> None:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"r{n}",
            title=f"Offre {n}",
            company=f"Entreprise {n} SA",
            first_seen_at=scored_at,
            last_seen_at=scored_at,
            status=OfferStatus.TO_REVIEW,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                filter_reasons=[],
                criteria_hash="x",
                score=score,
                scored_at=scored_at,
            )
        )


async def test_the_week_on_today(client: AsyncClient, rt: Runtime) -> None:
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="orp_monthly_target", value=10))
    for day in (date(2026, 10, 6), date(2026, 10, 19), date(2026, 10, 20)):
        await _application(rt, day)
    async with rt.sessionmaker() as session:
        week = await rhythm.week(session, date(2026, 10, 20))
    # 1 avant la semaine : 9 à faire sur 10 jours, 5 cette semaine ; 2 déjà faites.
    assert (week.target, week.count, week.research_today) == (5, 2, True)
    assert [(d.day.day, d.research, d.sent) for d in week.days][:3] == [
        (19, True, 1),
        (20, True, 1),
        (21, True, 0),
    ]
    assert not week.days[5].research and not week.days[6].research
    today = (await client.get("/api/today")).json()
    assert today["rhythm"]["count"] >= 0 and len(today["rhythm"]["days"]) == 7
    assert today["rhythm"]["research_today"] is True


async def test_offers_once_a_day_from_the_chosen_hour(rt: Runtime, sent: list[Message]) -> None:
    tuesday = datetime(2026, 10, 20, 8, 0, tzinfo=ZURICH)
    await _offer(rt, 1, 82, tuesday - timedelta(hours=1))
    # Avant 9 h : rien ; les bonnes notes attendent, elles ne sont pas marquées.
    assert (await notify.notify_new_scores(rt, tuesday)).offers == 0
    assert (await notify.notify_new_scores(rt, tuesday.replace(hour=9, minute=10))).offers == 1
    await _offer(rt, 2, 75, tuesday.replace(hour=11))
    # Déjà un message aujourd'hui : la suivante attend demain.
    assert (await notify.notify_new_scores(rt, tuesday.replace(hour=15))).offers == 0
    # Samedi, jour sans recherche : rien non plus.
    saturday = datetime(2026, 10, 24, 10, 0, tzinfo=ZURICH)
    assert (await notify.notify_new_scores(rt, saturday)).offers == 0
    monday = datetime(2026, 10, 26, 9, 30, tzinfo=ZURICH)
    assert (await notify.notify_new_scores(rt, monday)).offers == 1
    assert [m.title.split(" (")[0] for m in sent] == [
        "1 nouvelle offre pour toi",
        "1 nouvelle offre pour toi",
    ]
    # « Dès qu'elles arrivent » : comme avant, à chaque passage.
    async with rt.sessionmaker.begin() as session:
        session.add(Setting(key="offers_notify_mode", value="instant"))
    await _offer(rt, 3, 90, monday)
    assert (await notify.notify_new_scores(rt, monday.replace(hour=7))).offers == 1


async def test_a_day_without_search_keeps_the_phone_quiet(
    rt: Runtime, sent: list[Message], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rhythm, "now", lambda: datetime(2026, 10, 24, 10, 0, tzinfo=ZURICH))
    message = Message(title="Relancer ?", message="Acme SA")
    await notify.deliver(rt, message, kind="follow_up", link="/candidatures/suivi")
    # Un rappel daté passe quand même.
    await notify.deliver(rt, message, kind="orp_due", link="/candidatures/suivi")
    assert len(sent) == 1
    async with rt.sessionmaker() as session:
        kinds = sorted(n.kind for n in await session.scalars(select(Notification)))
    assert kinds == ["follow_up", "orp_due"]  # la cloche garde tout


async def test_the_rhythm_settings(client: AsyncClient, rt: Runtime) -> None:
    current = (await client.get("/api/settings")).json()
    assert current["rhythm_days"] == [0, 1, 2, 3, 4]
    assert (current["offers_notify_mode"], current["offers_notify_hour"]) == ("daily", 9)
    changed = {**current, "rhythm_days": [4, 0, 2, 2], "offers_notify_hour": 8}
    saved = (await client.put("/api/settings", json=changed)).json()
    assert saved["rhythm_days"] == [0, 2, 4] and saved["offers_notify_hour"] == 8
    wrongs: list[dict[str, object]] = [
        {"rhythm_days": []},
        {"rhythm_days": [7]},
        {"offers_notify_hour": 23},
    ]
    for wrong in wrongs:
        assert (await client.put("/api/settings", json={**current, **wrong})).status_code == 422


def test_a_pause_lowers_the_pace_without_debt() -> None:
    # Deux semaines de pause sur 22 jours de recherche : 12 jours ouverts, l'objectif du mois
    # passe à 6 pour le rythme (10 x 12 / 22, arrondi au-dessus), et rien n'est à rattraper.
    paused = rhythm.Rhythm(
        (0, 1, 2, 3, 4), pause_from=date(2026, 10, 5), pause_until=date(2026, 10, 18)
    )
    assert not paused.research(date(2026, 10, 12)) and paused.research(date(2026, 10, 19))
    assert rhythm.week_target(10, 1, date(2026, 10, 7), paused) == 0
    assert rhythm.week_target(10, 1, date(2026, 10, 19), paused) == 3  # 5 sur 10 jours
    assert rhythm.week_target(10, 1, date(2026, 10, 19), WEEKDAYS) == 5  # sans pause : 9


async def _settings(rt: Runtime, **values: object) -> None:
    async with rt.sessionmaker.begin() as session:
        for key, value in values.items():
            session.add(Setting(key=key, value=value))


async def test_the_weeks_of_the_month_and_the_pause(client: AsyncClient, rt: Runtime) -> None:
    await _settings(
        rt,
        orp_monthly_target=10,
        rhythm_pause_from="2026-10-12",
        rhythm_pause_until="2026-10-18",
    )
    for day in (date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 6)):
        await _application(rt, day)
    async with rt.sessionmaker() as session:
        weeks = await rhythm.month_weeks(session, "2026-10", date(2026, 10, 20))
        assert not await rhythm.is_research_day(session, date(2026, 10, 14))
    assert [(w.start.day, w.end.day, w.state) for w in weeks] == [
        (1, 4, "done"),
        (5, 11, "missed"),
        (12, 18, "pause"),
        (19, 25, "current"),
        (26, 31, "upcoming"),
    ]
    assert weeks[0].count == 2 and weeks[1].count == 1
    page = (await client.get("/api/rhythm/semaines", params={"month": "2026-10"})).json()
    assert [w["state"] for w in page["weeks"]][:3] == ["done", "missed", "pause"]
    assert (await client.get("/api/rhythm/semaines", params={"month": "oct"})).status_code == 422


async def test_the_pause_in_the_settings(client: AsyncClient, rt: Runtime) -> None:
    current = (await client.get("/api/settings")).json()
    assert current["rhythm_pause_from"] is None
    pause = {**current, "rhythm_pause_from": "2026-10-26", "rhythm_pause_until": "2026-11-01"}
    saved = (await client.put("/api/settings", json=pause)).json()
    assert saved["rhythm_pause_until"] == "2026-11-01"
    async with rt.sessionmaker() as session:
        loaded = await rhythm.load(session)
    assert loaded.paused(date(2026, 10, 28)) and not loaded.paused(date(2026, 11, 2))
    for wrong in (
        {"rhythm_pause_from": "2026-10-26", "rhythm_pause_until": None},
        {"rhythm_pause_from": "2026-11-02", "rhythm_pause_until": "2026-10-26"},
    ):
        assert (await client.put("/api/settings", json={**current, **wrong})).status_code == 422
    ended = (await client.put("/api/settings", json=current)).json()
    assert ended["rhythm_pause_from"] is None


async def _scored_application(rt: Runtime, n: int, sent_at: date, score: int) -> None:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"s{n}",
            title=f"Poste {n}",
            company="Acme SA",
            first_seen_at=datetime(2026, 10, 1, tzinfo=UTC),
            last_seen_at=datetime(2026, 10, 1, tzinfo=UTC),
            status=OfferStatus.APPLIED,
        )
        session.add(offer)
        await session.flush()
        session.add(
            Evaluation(
                offer_id=offer.id,
                filter_passed=True,
                filter_reasons=[],
                criteria_hash="x",
                score=score,
                scored_at=datetime(2026, 10, 1, tzinfo=UTC),
            )
        )
        session.add(
            Application(
                offer_id=offer.id,
                sent_at=sent_at,
                method="electronique",
                company="Acme SA",
                job_title=f"Poste {n}",
                orp_month=f"{sent_at:%Y-%m}",
            )
        )


async def test_the_end_of_week_signal(rt: Runtime, sent: list[Message]) -> None:
    from jobbot.notify.rhythm import notify_week

    await _settings(rt, orp_monthly_target=10)
    friday, thursday = date(2026, 10, 23), date(2026, 10, 22)
    async with rt.sessionmaker() as session:
        assert await rhythm.signal(session, thursday) is None  # pas le dernier jour
        late = await rhythm.signal(session, friday)
    # Rien cette semaine : 5 attendues (10 sur 10 jours restants, 5 cette semaine).
    assert late is not None and late.kind == "late"
    assert (late.title, late.message) == ("0 sur 5 cette semaine", "Lundi, reprends à ton rythme.")
    for n in range(5):
        await _scored_application(rt, n, date(2026, 10, 19 + n % 5), 80)
    assert await notify_week(rt, friday) == 1
    assert await notify_week(rt, friday) == 0  # une fois par semaine
    assert sent[-1].title == "Semaine faite : 5 candidatures"
    assert sent[-1].message == "Octobre : 5 / 10. Le reste du temps est à toi."
    # Beaucoup plus, dont des offres peu notées : « trop ».
    for n in range(5, 9):
        await _scored_application(rt, n, date(2026, 10, 22), 35)
    async with rt.sessionmaker() as session:
        too_much = await rhythm.signal(session, friday)
    assert too_much is not None and too_much.kind == "too_much"
    assert too_much.title == "9 candidatures cette semaine, dont 4 peu notées"
