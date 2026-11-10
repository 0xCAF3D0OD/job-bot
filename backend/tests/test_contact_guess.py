from jobbot.letters.contact_guess import guess_contact


def test_cv_classique() -> None:
    text = (
        "Camille Exemple\nEmployée de commerce\nRue du Test 1\n1003 Lausanne\n"
        "079 123 45 67\ncamille@example.ch\n\nExpériences\nCoop, Lausanne"
    )
    found = guess_contact(text)
    assert found.name == "Camille Exemple"
    assert found.street == "Rue du Test 1"
    assert (found.postcode, found.city) == ("1003", "Lausanne")
    assert found.phone == "079 123 45 67"
    assert found.email == "camille@example.ch"


def test_tout_sur_une_ligne() -> None:
    found = guess_contact("Luca Rossi\nBahnhofstrasse 12, CH-8001 Zürich | +41 79 000 00 00")
    assert found.street == "Bahnhofstrasse 12"
    assert (found.postcode, found.city) == ("8001", "Zürich")
    assert found.phone == "+41 79 000 00 00"


def test_rien_a_proposer() -> None:
    found = guess_contact("CURRICULUM VITAE\nExpériences\n2019 à 2023 : vendeuse")
    assert found.name is None
    assert found.street is None and found.postcode is None and found.city is None


def test_l_adresse_d_un_employeur_plus_bas_n_est_pas_prise() -> None:
    lines = ["Camille Exemple", *["ligne"] * 20, "Rue de l'Employeur 9", "1200 Genève"]
    found = guess_contact("\n".join(lines))
    assert found.street is None and found.postcode is None
