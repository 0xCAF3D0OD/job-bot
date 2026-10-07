"""Saisie Job-Room : adresse découpée et champs dans l'ordre du formulaire (capture 2026-10-07)."""

from datetime import date

import pytest

from jobbot.core.orp import ApplicationData, split_address, to_row


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Chemin Malombré 10\n1206 Genève", ("Chemin Malombré", "10", "", "1206 Genève")),
        (
            "Avenue Alexandre-Vinet 30, 1004 Lausanne",
            ("Avenue Alexandre-Vinet", "30", "", "1004 Lausanne"),
        ),
        (
            "Rue du Marché 4b, Case postale 123, CH-1211 Genève 3",
            ("Rue du Marché", "4b", "123", "1211 Genève 3"),
        ),
        ("12, rue de Lausanne\n1201 Genève", ("rue de Lausanne", "12", "", "1201 Genève")),
        ("Bahnhofstrasse 1-3, 8001 Zürich", ("Bahnhofstrasse", "1-3", "", "8001 Zürich")),
        ("Lausanne", ("Lausanne", "", "", "")),
        ("", ("", "", "", "")),
    ],
)
def test_split_address(text: str, expected: tuple[str, str, str, str]) -> None:
    found = split_address(text)
    assert (found.street, found.number, found.po_box, found.postcode_city) == expected


def test_job_room_fields_follow_the_form() -> None:
    app = ApplicationData(
        id=1,
        sent_at=date(2026, 10, 2),
        company="Acme SA",
        company_address="Avenue de l'Exemple 5, 1003 Lausanne",
        contact_name="Camille Exemple",
        contact_phone="021 000 00 00",
        job_title="Ingénieur DevOps",
        rate_text="temps partiel (80 %)",
        method="electronique",
        assigned_by_orp=False,
        status="entretien",
        status_reason=None,
        interview_at=None,
        application_url="https://emploi.exemple.ch/1",
        contact_email="rh@exemple.ch",
    )
    fields = to_row(app).job_room
    assert [f.label for f in fields] == [
        "Date",
        "Mode",
        "Entreprise",
        "Rue",
        "N°",
        "Numéro de case postale",
        "Pays",
        "NPA / Lieu",
        "Personne contactée",
        "Courriel",
        "Numéro de téléphone",
        "Désignation du poste",
        "Lien vers le formulaire en ligne",
        "Assignée",
        "Taux",
        "Résultat",
    ]
    values = {f.label: f.value for f in fields}
    assert values["Date"] == "02.10.2026" and values["Mode"] == "Par voie électronique"
    assert (values["Rue"], values["N°"], values["NPA / Lieu"]) == (
        "Avenue de l'Exemple",
        "5",
        "1003 Lausanne",
    )
    assert values["Courriel"] == "rh@exemple.ch" and values["Assignée"] == "Non"
    assert values["Taux"] == "A temps partiel"
    assert values["Résultat"] == "Entretien d'embauche + En suspens"
    assert {f.label for f in fields if f.choice} == {"Mode", "Pays", "Assignée", "Taux", "Résultat"}
