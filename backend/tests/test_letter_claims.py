"""Une affirmation plus forte que sa source (demande de Kevin du 30.10.2026) : la phrase réelle qui
a échappé à la relecture, et trois exagérations types. Sans l'IA : à chaque CI."""

from jobbot.llm import claims
from jobbot.llm.scoring import ProfileChunkData

ALLO = ProfileChunkData(
    id=6,
    kind="projet",
    title="Allô Remplaçant",
    content="alloremplacant.ch, plateforme de remplacements",
)
SENTENCE = (
    "alloremplacant.ch is a platform I built end to end and which runs in production for "
    "compulsory schooling in the canton of Vaud"
)


def _letter(text: str, chunk_ids: list[int]) -> dict[str, object]:
    return {"subject": "Candidature", "paragraphs": [{"text": text, "chunk_ids": chunk_ids}]}


def test_the_exact_sentence_fails() -> None:
    """La phrase de la lettre de Kevin, avec un profil qui ne parle que d'une plateforme de
    remplacements : production, institution et « de bout en bout » ne sont pas dans la source."""
    flags = claims.check(_letter(SENTENCE + ".", [6]), [ALLO])
    assert len(flags) == 1
    reasons = flags[0].reasons
    assert "production" in reasons and "institution" in reasons and "seul" in reasons
    # La phrase est retirée ; la lettre garde ce qui reste.
    letter = _letter(SENTENCE + ". The platform uses Vue and FastAPI.", [6])
    kept = claims.drop(letter, claims.check(letter, [ALLO]))
    assert kept["paragraphs"] == [{"text": "The platform uses Vue and FastAPI.", "chunk_ids": [6]}]


def test_the_same_sentence_passes_when_the_profile_says_it() -> None:
    """Le bloc 6 du vrai profil le dit : la phrase passe (c'est le profil qu'il faut corriger)."""
    real = ProfileChunkData(
        id=6,
        kind="experience",
        title="Allô Remplaçant — plateforme en production (alloremplacant.ch)",
        content="Projet personnel complet, de l'infrastructure au code, en production pour "
        "l'enseignement obligatoire vaudois.",
    )
    assert claims.check(_letter(SENTENCE + ".", [6]), [real]) == []


def test_added_number() -> None:
    source = ProfileChunkData(1, "experience", "Démo SA", "Plateforme Kubernetes en production.")
    letter = _letter(
        "Chez Démo SA, j'ai mené une plateforme Kubernetes de 40 services en production.", [1]
    )
    flags = claims.check(letter, [source])
    assert flags and flags[0].reasons == ("chiffre 40",)
    # Un nom d'outil (K3s, S3) n'est pas un chiffre ; écrit en lettres, le chiffre est le même.
    assert claims.check(_letter("Un cluster K3s et des fichiers sur S3.", [1]), [source]) == []
    worded = ProfileChunkData(
        1, "experience", "Démo SA", "Déploiements de deux jours à vingt minutes."
    )
    assert claims.check(_letter("Deployments went from 2 days to 20 minutes.", [1]), [worded]) == []
    # Une durée que les années du bloc donnent : « depuis quatre ans » avec 2021-2025.
    dated = ProfileChunkData(1, "experience", "Démo SA (2021-2025)", "Plateforme Kubernetes.")
    assert (
        claims.check(_letter("Je fais tourner Kubernetes depuis quatre ans.", [1]), [dated]) == []
    )


def test_added_users() -> None:
    source = ProfileChunkData(
        2, "projet", "Outil interne", "Un outil de suivi des tickets en Python."
    )
    letter = _letter(
        "J'ai écrit un outil de suivi des tickets utilisé par des centaines de collègues.", [2]
    )
    flags = claims.check(letter, [source])
    assert flags and set(flags[0].reasons) == {"utilisateurs", "echelle"}


def test_inflated_role() -> None:
    source = ProfileChunkData(3, "experience", "NAGRA", "Membre de l'équipe SRE pendant un an.")
    letter = _letter("Chez NAGRA, j'ai dirigé l'équipe SRE pendant un an.", [3])
    flags = claims.check(letter, [source])
    assert flags and flags[0].reasons == ("direction",)
    assert (
        claims.check(
            _letter("Chez NAGRA, j'ai été membre de l'équipe SRE pendant un an.", [3]), [source]
        )
        == []
    )


def test_offer_facts_are_not_claims_about_the_person() -> None:
    """« Votre infrastructure à grande échelle » vient de l'annonce : rien à signaler."""
    source = ProfileChunkData(4, "competence", "Kubernetes", "K3s et Helm.")
    letter = _letter("Votre infrastructure à grande échelle du canton de Vaud m'attire.", [4])
    assert (
        claims.check(letter, [source], offer_text="Infrastructure à grande échelle, Canton de Vaud")
        == []
    )


def test_forbidden_claim_is_flagged_even_reworded() -> None:
    source = ProfileChunkData(5, "projet", "Site", "Un site vitrine en Vue.")
    forbidden = ["J'ai livré le site à la Ville de Lausanne"]
    letter = _letter("Ce site, je l'ai livré à la Ville de Lausanne.", [5])
    flags = claims.check(letter, [source], forbidden=forbidden)
    assert flags and "marquée « Pas vrai »" in flags[0].reasons
