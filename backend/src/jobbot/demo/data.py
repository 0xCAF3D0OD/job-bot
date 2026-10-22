"""Le jeu de données fictif de la démo (docs/72 §4).

Tout est inventé : la personne (Camille Exemple), les entreprises (« Exemple SA », « Démo
Sàrl »…), les adresses (rue du Test, rue de l'Exemple…) et les liens (exemple.ch). Aucune
donnée ne vient d'une vraie base. Les dates sont relatives au jour du remplissage : un mois
(0 : le mois en cours, 1 : le précédent…) et une fraction du mois.
"""

from dataclasses import dataclass

IDENTITY = {
    "identity_name": "Camille Exemple",
    "identity_street": "Rue du Test 1",
    "identity_postcode": "1020",
    "identity_city": "Renens",
    "identity_phone": "+41 79 000 00 00",
    "identity_email": "camille@exemple.ch",
    "identity_website": "https://camille.exemple.ch",
    "apply_availability": "Dès le 1er du mois prochain",
    "apply_salary": "CHF 100'000 par an",
    "apply_permit": "Permis C",
}
TRADE = "DevOps"
OCCUPATION = "Ingénieur·e DevOps"
ORP_TARGET = 10
DOMAIN_KEYWORDS = ["DevOps", "Kubernetes", "Cloud"]

# Prérequis : la Suisse romande, au moins 80 %, ni stage ni temporaire.
LOCATIONS = ("VD", "GE", "FR", "NE")
MIN_RATE = 80
EXCLUDED_TYPES = ("stage", "temporaire")


@dataclass(frozen=True)
class Chunk:
    key: str
    kind: str
    title: str
    content: str
    tags: tuple[str, ...] = ()


CHUNKS = [
    Chunk(
        "exp_platform",
        "experience",
        "Ingénieur·e DevOps, Exemple Logistique SA (2021-2026)",
        "Mise en place d'une plateforme Kubernetes pour 40 services ; déploiements continus avec "
        "GitLab CI et Argo CD ; temps de mise en production passé de deux jours à vingt minutes.",
        ("Kubernetes", "GitLab CI", "Argo CD"),
    ),
    Chunk(
        "exp_cloud",
        "experience",
        "Administrateur·rice systèmes et cloud, Démo Services Sàrl (2017-2021)",
        "Migration de l'infrastructure vers le cloud (Azure) ; infrastructure décrite en "
        "Terraform ; supervision avec Prometheus et Grafana ; astreintes et gestion d'incidents.",
        ("Azure", "Terraform", "Prometheus"),
    ),
    Chunk(
        "exp_support",
        "experience",
        "Technicien·ne systèmes, Témoin Informatique SA (2014-2017)",
        "Postes de travail et serveurs Linux pour 300 personnes ; scripts d'automatisation en "
        "Bash et Python.",
        ("Linux", "Python"),
    ),
    Chunk(
        "comp_k8s",
        "competence",
        "Conteneurs et orchestration",
        "Docker, Kubernetes, Helm, Argo CD ; mise à l'échelle, sécurité des clusters.",
        ("Docker", "Kubernetes", "Helm"),
    ),
    Chunk(
        "comp_iac",
        "competence",
        "Infrastructure as code et cloud",
        "Terraform, Ansible ; Azure et AWS ; réseaux, identités et coûts du cloud.",
        ("Terraform", "Ansible", "AWS", "Azure"),
    ),
    Chunk(
        "comp_obs",
        "competence",
        "Observabilité et fiabilité",
        "Prometheus, Grafana, Loki ; objectifs de niveau de service ; post-mortems sans reproche.",
        ("Prometheus", "Grafana", "SRE"),
    ),
    Chunk(
        "langues",
        "competence",
        "Langues",
        "Français (langue maternelle), anglais (C1), allemand (B1).",
    ),
    Chunk(
        "formation",
        "formation",
        "Bachelor HES en informatique de gestion (2014)",
        "Haute école fictive de Suisse romande.",
    ),
    Chunk(
        "pref",
        "preference",
        "Ce que je cherche",
        "Une équipe plateforme ou SRE, en Suisse romande, à 80-100 %, avec du télétravail partiel.",
    ),
]

# Canton de chaque lieu : les alertes l'écrivent avec la ville (« Lausanne, VD »).
CANTONS = {
    "Lausanne": "VD",
    "Genève": "GE",
    "Renens": "VD",
    "Morges": "VD",
    "Nyon": "VD",
    "Fribourg": "FR",
    "Vevey": "VD",
    "Neuchâtel": "NE",
    "Yverdon-les-Bains": "VD",
    "Zürich": "ZH",
}
CITIES = {
    "Lausanne": "1003",
    "Genève": "1204",
    "Renens": "1020",
    "Morges": "1110",
    "Nyon": "1260",
    "Fribourg": "1700",
    "Vevey": "1800",
    "Neuchâtel": "2000",
    "Yverdon-les-Bains": "1400",
    "Zürich": "8001",
}


@dataclass(frozen=True)
class Applied:
    """La candidature envoyée : quand, et ce qu'elle est devenue."""

    month: int
    fraction: float
    status: str = "en_attente"
    reason: str | None = None
    method: str = "electronique"
    contact: str | None = None
    # Entretien : « upcoming » (à venir, jeudi prochain), « held » (passé, avec retour).
    interview: str | None = None
    followed_up: bool = False
    letter: bool = False


@dataclass(frozen=True)
class OfferSpec:
    key: str
    title: str
    company: str
    city: str
    source: str
    score: int | None
    rate: tuple[int, int] = (80, 100)
    remote: str = "hybrid"
    # Pour une offre pas (encore) envoyée : to_review, preparing, later, ignored ; filtered :
    # écartée par les prérequis (le filtre dit pourquoi).
    state: str = "to_review"
    days_ago: int = 3
    applied: Applied | None = None
    contract: str = "CDI"
    asks: tuple[str, ...] = ("Kubernetes", "Terraform", "CI/CD")
    missing: tuple[str, ...] = ()
    extra: str = ""
    # Un poste hors du domaine du profil (la donnée pour un profil plateforme) : ce qu'il fait,
    # la phrase « pourquoi » et ses points forts suivent l'offre (docs/121 §C.1).
    role: str = ""
    why: str = ""
    # Le niveau, seulement quand l'annonce le dit (docs/121 §C.2).
    level: str | None = None
    level_detail: str = ""


def _a(month: int, fraction: float, **kwargs: object) -> Applied:
    return Applied(month, fraction, **kwargs)  # type: ignore[arg-type]


OFFERS = [
    # --- Le mois en cours : six candidatures, un entretien jeudi --------------------------
    OfferSpec(
        "o1",
        "Ingénieur·e DevOps",
        "Exemple SA",
        "Lausanne",
        "jobup",
        86,
        applied=_a(0, 0.15, letter=True, contact="Alex Démo"),
    ),
    OfferSpec(
        "o2",
        "Platform Engineer",
        "Démo Sàrl",
        "Genève",
        "indeed",
        78,
        applied=_a(0, 0.3, letter=True),
        asks=("Kubernetes", "Go", "Argo CD"),
        missing=("Go",),
    ),
    OfferSpec(
        "o3",
        "Site Reliability Engineer",
        "Essai Systèmes SA",
        "Renens",
        "jobsch",
        88,
        applied=_a(
            0, 0.45, status="entretien", interview="upcoming", letter=True, contact="Sam Exemple"
        ),
        asks=("Prometheus", "Kubernetes", "astreintes"),
    ),
    OfferSpec(
        "o4",
        "Cloud Engineer Azure",
        "Modèle Assurances SA",
        "Lausanne",
        "jobup",
        72,
        applied=_a(0, 0.6),
        asks=("Azure", "Terraform", "réseau"),
    ),
    OfferSpec(
        "o5",
        "Ingénieur·e infrastructure",
        "Prototype Fintech SA",
        "Genève",
        "linkedin",
        69,
        applied=_a(0, 0.75, method="electronique"),
        asks=("Linux", "Ansible", "PCI"),
    ),
    OfferSpec(
        "o6",
        "DevOps Engineer (80-100 %)",
        "Échantillon Santé SA",
        "Morges",
        "jobup",
        81,
        applied=_a(0, 0.9, letter=True),
    ),
    # --- Le mois précédent : dix candidatures ---------------------------------------------
    OfferSpec(
        "o7",
        "Ingénieur·e systèmes Linux",
        "Test Logistique SA",
        "Yverdon-les-Bains",
        "indeed",
        64,
        applied=_a(1, 0.05, status="refus", reason="profil plus orienté développement"),
    ),
    OfferSpec(
        "o8",
        "Kubernetes Engineer",
        "Bac à sable SA",
        "Lausanne",
        "jobup",
        90,
        applied=_a(
            1, 0.12, status="entretien", interview="held", letter=True, contact="Robin Essai"
        ),
    ),
    OfferSpec(
        "o9",
        "DevOps Engineer",
        "Maquette Médias Sàrl",
        "Vevey",
        "jobsch",
        74,
        applied=_a(1, 0.2, status="relancee", followed_up=True),
    ),
    OfferSpec(
        "o10",
        "Ingénieur·e cloud AWS",
        "Brouillon Énergie SA",
        "Nyon",
        "indeed",
        66,
        applied=_a(1, 0.28, status="sans_reponse"),
        asks=("AWS", "Terraform", "Python"),
    ),
    OfferSpec(
        "o11",
        "Platform Engineer",
        "Essai Systèmes SA",
        "Renens",
        "linkedin",
        79,
        applied=_a(1, 0.36, status="refus", reason="poste pourvu en interne"),
    ),
    OfferSpec(
        "o12",
        "SRE junior",
        "Témoin Industrie SA",
        "Fribourg",
        "jobup",
        70,
        extra="Premier poste, ou deux ans d'expérience au plus.",
        level="below",
        level_detail="Le poste vise deux ans d'expérience au plus ; tu en as plus de dix.",
        applied=_a(1, 0.44, status="en_attente", method="ecrit"),
    ),
    OfferSpec(
        "o13",
        "Ingénieur·e DevOps",
        "Fictif Cloud SA",
        "Genève",
        "indeed",
        83,
        applied=_a(1, 0.55, status="refus", reason="niveau d'allemand insuffisant"),
    ),
    OfferSpec(
        "o14",
        "Administrateur·rice systèmes",
        "Exemple Commune",
        "Morges",
        "jobsch",
        58,
        applied=_a(1, 0.66, status="sans_reponse", method="ecrit"),
    ),
    OfferSpec(
        "o15",
        "Cloud Platform Engineer",
        "Démo Data SA",
        "Lausanne",
        "jobup",
        85,
        applied=_a(1, 0.78, status="relancee", followed_up=True, letter=True),
    ),
    OfferSpec(
        "o16",
        "Ingénieur·e automatisation",
        "Prototype Fintech SA",
        "Genève",
        "jobup",
        62,
        applied=_a(1, 0.9, status="en_attente", method="telephone"),
    ),
    # --- Il y a deux mois : neuf candidatures ---------------------------------------------
    OfferSpec(
        "o17",
        "DevOps Engineer",
        "Modèle Assurances SA",
        "Lausanne",
        "indeed",
        77,
        applied=_a(
            2, 0.08, status="refus", interview="refused", reason="profil plus senior recherché"
        ),
    ),
    OfferSpec(
        "o18",
        "Ingénieur·e systèmes",
        "Échantillon Santé SA",
        "Vevey",
        "jobup",
        61,
        applied=_a(2, 0.16, status="sans_reponse"),
    ),
    OfferSpec(
        "o19",
        "SRE",
        "Bac à sable SA",
        "Lausanne",
        "jobsch",
        80,
        applied=_a(2, 0.25, status="refus", reason="candidature arrivée trop tard"),
    ),
    OfferSpec(
        "o20",
        "Ingénieur·e infrastructure",
        "Test Logistique SA",
        "Yverdon-les-Bains",
        "indeed",
        59,
        applied=_a(2, 0.35, status="sans_reponse", method="ecrit"),
    ),
    OfferSpec(
        "o21",
        "Platform Engineer",
        "Fictif Cloud SA",
        "Genève",
        "linkedin",
        73,
        applied=_a(2, 0.45, status="refus", reason="autre candidature retenue"),
    ),
    OfferSpec(
        "o22",
        "Cloud Engineer",
        "Maquette Médias Sàrl",
        "Lausanne",
        "jobup",
        68,
        applied=_a(2, 0.55, status="sans_reponse"),
    ),
    OfferSpec(
        "o23",
        "DevOps Engineer",
        "Brouillon Énergie SA",
        "Neuchâtel",
        "jobsch",
        75,
        applied=_a(2, 0.68, status="refus", reason="pas de réponse détaillée"),
    ),
    OfferSpec(
        "o24",
        "Administrateur·rice Linux",
        "Exemple Commune",
        "Nyon",
        "indeed",
        55,
        applied=_a(2, 0.8, status="sans_reponse", method="personnel"),
    ),
    OfferSpec(
        "o25",
        "Ingénieur·e DevOps",
        "Témoin Industrie SA",
        "Fribourg",
        "jobup",
        71,
        applied=_a(2, 0.92, status="refus", reason="profil plus junior recherché"),
    ),
    # --- Pas encore envoyées --------------------------------------------------------------
    OfferSpec(
        "o26",
        "Senior Platform Engineer",
        "Démo Data SA",
        "Lausanne",
        "jobup",
        87,
        state="preparing",
        days_ago=2,
        extra="Équipe de six, Kubernetes sur trois clouds.",
    ),
    OfferSpec(
        "o27",
        "Ingénieur·e SRE",
        "Fictif Cloud SA",
        "Genève",
        "indeed",
        82,
        state="preparing",
        days_ago=4,
    ),
    OfferSpec("o28", "DevOps Engineer", "Prototype Fintech SA", "Genève", "jobsch", 76, days_ago=1),
    OfferSpec(
        "o29",
        "Cloud Engineer (Azure)",
        "Témoin Industrie SA",
        "Fribourg",
        "jobup",
        67,
        days_ago=2,
        asks=("Azure", "Bicep", "PowerShell"),
        missing=("Bicep",),
    ),
    OfferSpec(
        "o30", "Ingénieur·e infrastructure", "Bac à sable SA", "Neuchâtel", "indeed", 63, days_ago=5
    ),
    OfferSpec(
        "o31",
        "Data Engineer",
        "Démo Data SA",
        "Lausanne",
        "linkedin",
        41,
        days_ago=3,
        asks=("Spark", "Python", "SQL"),
        missing=("Spark", "SQL"),
        role="construire et faire tourner les flux de données de l'entreprise.",
        why="Le poste vise la donnée (Spark, SQL) ; ton parcours est la plateforme et le cloud.",
    ),
    OfferSpec(
        "o32",
        "Ingénieur·e plateforme cloud",
        "Maquette Médias Sàrl",
        "Vevey",
        "jobup",
        74,
        state="later",
        days_ago=6,
    ),
    OfferSpec(
        "o33",
        "Technicien·ne support",
        "Exemple Commune",
        "Morges",
        "indeed",
        35,
        state="ignored",
        days_ago=8,
    ),
    # Écartées par les prérequis.
    OfferSpec(
        "o34",
        "Platform Engineer",
        "Témoin Industrie SA",
        "Zürich",
        "jobsch",
        None,
        state="filtered",
        days_ago=2,
    ),
    OfferSpec(
        "o35",
        "Stage DevOps",
        "Échantillon Santé SA",
        "Lausanne",
        "jobup",
        None,
        state="filtered",
        days_ago=3,
        contract="Stage",
    ),
    OfferSpec(
        "o36",
        "Ingénieur·e cloud à 40 %",
        "Brouillon Énergie SA",
        "Nyon",
        "indeed",
        None,
        state="filtered",
        days_ago=4,
        rate=(40, 40),
    ),
]

# Candidatures saisies à la main (sans offre reçue par alerte), pour l'historique ORP : le
# troisième mois avant le mois en cours, et une de plus il y a deux mois.
MANUAL_APPLICATIONS = [
    # (mois, fraction, entreprise, poste, lieu, statut)
    (3, 0.05, "Exemple SA", "Administrateur·rice systèmes", "Lausanne", "refus"),
    (3, 0.12, "Démo Sàrl", "Technicien·ne infrastructure", "Genève", "sans_reponse"),
    (3, 0.2, "Essai Systèmes SA", "Ingénieur·e systèmes", "Renens", "refus"),
    (3, 0.3, "Témoin Industrie SA", "Ingénieur·e DevOps", "Fribourg", "sans_reponse"),
    (3, 0.4, "Fictif Cloud SA", "Cloud Engineer", "Genève", "refus"),
    (3, 0.5, "Maquette Médias Sàrl", "Administrateur·rice Linux", "Vevey", "sans_reponse"),
    (3, 0.6, "Bac à sable SA", "Ingénieur·e infrastructure", "Lausanne", "refus"),
    (3, 0.7, "Brouillon Énergie SA", "DevOps Engineer", "Nyon", "sans_reponse"),
    (3, 0.82, "Test Logistique SA", "Ingénieur·e systèmes", "Yverdon-les-Bains", "refus"),
    (3, 0.93, "Exemple Commune", "Technicien·ne systèmes", "Morges", "sans_reponse"),
    (2, 0.5, "Prototype Fintech SA", "Ingénieur·e systèmes", "Genève", "sans_reponse"),
]

INTERVIEW_HELD = {
    "kind": "technique",
    "format": "visio",
    "duration": "30_60",
    "interviewers": ["manager", "equipe"],
    "people_count": 2,
    "rating": 4,
    "stress": 2,
    "interest": "more",
    "outlook": "positive",
    "questions": [
        {"text": "Comment gérez-vous un incident en production ?", "difficult": False},
        {"text": "Expliquez un déploiement blue/green avec Argo CD.", "difficult": True},
        {"text": "Pourquoi quitter votre poste actuel ?", "difficult": False},
    ],
    "salary_asked": True,
    "salary_answer": "Entre 95'000 et 105'000 selon le poste",
    "went_well": "L'exemple de la migration vers Kubernetes a beaucoup intéressé l'équipe.",
    "went_badly": "Hésitation sur les stratégies de déploiement progressif.",
    "to_prepare": ["Revoir les déploiements canary", "Préparer deux questions sur l'équipe"],
    "learned": "Ils cherchent quelqu'un pour structurer leurs astreintes.",
    "next_step": "reponse",
    "thanks": "sent",
}
INTERVIEW_REFUSED = {
    "kind": "rh",
    "format": "telephone",
    "duration": "moins_30",
    "interviewers": ["rh"],
    "people_count": 1,
    "rating": 3,
    "stress": 3,
    "interest": "same",
    "outlook": "unsure",
    "questions": [{"text": "Quelles sont vos prétentions salariales ?", "difficult": True}],
    "salary_asked": True,
    "salary_answer": "100'000",
    "went_badly": "Pas assez d'exemples chiffrés.",
    "next_step": "rien",
    "thanks": "no",
    "employer_feedback": "Profil plus senior recherché pour ce poste.",
}

NEWS = [
    (
        "Le chômage reste stable en Suisse romande (article d'exemple)",
        "Les chiffres du mois montrent une légère baisse dans les métiers de l'informatique.",
    ),
    (
        "Kubernetes : ce que cherchent les recruteurs en 2026 (exemple)",
        "Plateformes internes, sécurité et coûts du cloud reviennent dans la plupart des annonces.",
    ),
    (
        "Comment préparer un entretien technique (article d'exemple)",
        "Trois conseils pour raconter un incident et ce qu'il vous a appris.",
    ),
    (
        "Formations continues : ce que l'assurance-chômage peut financer (exemple)",
        "Les mesures du marché du travail en quelques questions.",
    ),
    (
        "Télétravail : les entreprises romandes restent hybrides (exemple)",
        "Deux à trois jours au bureau par semaine restent la norme.",
    ),
    (
        "Les métiers du cloud en tête des recrutements (article d'exemple)",
        "DevOps, SRE et ingénieurs plateforme sont les profils les plus demandés.",
    ),
]
