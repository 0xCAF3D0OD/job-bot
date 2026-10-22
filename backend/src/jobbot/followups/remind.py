"""Quand relancer une candidature (docs/38, docs/124 §G) : le jour choisi dans l'étape
« Suivre » (`follow_up_on`), sinon 10 jours après l'envoi. Une seule règle pour Aujourd'hui, les
notifications, l'assistant et le bilan."""

from datetime import date, timedelta

from sqlalchemy import ColumnElement, and_, or_

from jobbot.db.models import Application, ApplicationStatus

REMIND_AFTER_DAYS = 10
# Le jour choisi : entre 5 et 30 jours après l'envoi.
MIN_DAYS = 5
MAX_DAYS = 30


def remind_on(application: Application) -> date:
    return application.follow_up_on or application.sent_at + timedelta(days=REMIND_AFTER_DAYS)


def remind_due(today: date) -> ColumnElement[bool]:
    """Les candidatures en attente dont le jour de relance est arrivé."""
    return and_(
        Application.status == ApplicationStatus.EN_ATTENTE,
        or_(
            and_(Application.follow_up_on.is_not(None), Application.follow_up_on <= today),
            and_(
                Application.follow_up_on.is_(None),
                Application.sent_at <= today - timedelta(days=REMIND_AFTER_DAYS),
            ),
        ),
    )
