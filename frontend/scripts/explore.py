"""Les états d'une page pour les audits (docs/133) : l'état par défaut, puis chaque ligne repliable
ouverte et chaque vue choisie (le détail du Bilan, les listes du Suivi), une à la fois.

Les audits ne regardaient que la page telle qu'elle s'ouvre : des cartes dans une carte repliée
passaient sans être vues.
"""

from collections.abc import AsyncIterator

from playwright.async_api import Page

TOGGLES = ", ".join(
    [
        "button.disclosure-row[aria-expanded=false]",
        ".bilan-views [role=radio][aria-checked=false]",
        ".suivi-panel-tabs [role=radio][aria-checked=false]",
    ]
)
MAX_STATES = 12


async def states(page: Page) -> AsyncIterator[str]:
    """Donne la main à l'audit pour chaque état ; le nom de l'état dit ce qui a été ouvert."""
    yield ""
    seen: set[str] = set()
    for _ in range(MAX_STATES):
        target = None
        for handle in await page.query_selector_all(TOGGLES):
            label = (await handle.inner_text()).strip().split("\n")[0][:40]
            if label and label not in seen and await handle.is_visible():
                target = (handle, label)
                break
        if target is None:
            return
        handle, label = target
        seen.add(label)
        await handle.click()
        await page.wait_for_timeout(500)
        yield f"  [{label}]"
