"""Échéance ORP reportée au jour ouvrable (MODIFICATIONS du 9 novembre, §11 ; prompt complet §4)."""

from datetime import date

from jobbot.core.holidays import canton_of_postcode, easter, holidays, working_day
from jobbot.core.orp import due_date


def test_easter() -> None:
    assert [easter(y) for y in (2021, 2024, 2026, 2027)] == [
        date(2021, 4, 4),
        date(2024, 3, 31),
        date(2026, 4, 5),
        date(2027, 3, 28),
    ]


def test_a_5th_on_a_weekday_stays() -> None:
    # Le 5 novembre 2026 est un jeudi.
    assert due_date("2026-10") == date(2026, 11, 5)


def test_a_5th_on_a_saturday_moves_to_monday() -> None:
    # Le 5 décembre 2026 est un samedi.
    assert due_date("2026-11") == date(2026, 12, 7)


def test_a_5th_on_a_sunday_moves_to_monday() -> None:
    # Le 5 avril 2026 est le dimanche de Pâques, et le lundi 6 est férié : mardi 7.
    assert due_date("2026-03") == date(2026, 4, 7)
    # Le 5 octobre 2025 est un dimanche ordinaire.
    assert due_date("2025-09") == date(2025, 10, 6)


def test_a_5th_that_is_a_holiday_in_vaud() -> None:
    # Lundi de Pâques le 5 avril 2021 : férié partout sauf en Valais.
    assert due_date("2021-03", canton="VD") == date(2021, 4, 6)
    assert due_date("2021-03", canton="VS") == date(2021, 4, 5)


def test_a_5th_that_is_a_holiday_in_another_canton_only() -> None:
    # Jeûne genevois le jeudi 5 septembre 2024 : reporté à Genève, pas dans le canton de Vaud.
    assert due_date("2024-08", canton="GE") == date(2024, 9, 6)
    assert due_date("2024-08", canton="VD") == date(2024, 9, 5)


def test_holidays_of_vaud_and_a_catholic_canton() -> None:
    vaud = holidays(2026, "VD")
    assert date(2026, 1, 2) in vaud
    assert date(2026, 9, 21) in vaud  # lundi du Jeûne fédéral
    assert date(2026, 12, 26) not in vaud
    assert date(2026, 12, 8) in holidays(2026, "LU")
    # Un vendredi 4 décembre 2026 non férié, puis lundi 7 ; à Lucerne, mardi 8 est férié.
    assert working_day(date(2026, 12, 8), "LU") == date(2026, 12, 9)


def test_canton_of_postcode() -> None:
    assert canton_of_postcode("1020") == "VD"
    assert canton_of_postcode("1204") == "GE"
    assert canton_of_postcode("1950") == "VS"
    assert canton_of_postcode("1700") == "FR"
    assert canton_of_postcode("2000") == "NE"
    assert canton_of_postcode("3011") == "BE"
    assert canton_of_postcode("6900") == "TI"
    assert canton_of_postcode("8001") == "ZH"
    assert canton_of_postcode("abc") is None
    assert canton_of_postcode(None) is None
