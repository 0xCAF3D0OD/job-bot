"""Sources suggérées (docs/16 §4.1) et veilles par recherche (docs/16 §4.2)."""

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from urllib.parse import urlencode

GOOGLE_NEWS = "https://news.google.com/rss/search?"


@dataclass(frozen=True)
class CatalogSource:
    id: str
    name: str
    kind: str
    url: str
    feed_url: str
    domains: list[str]
    country: str
    language: str | None
    labour_market: bool
    match: str | None
    description: str


@dataclass(frozen=True)
class Catalog:
    domains: dict[str, str]
    sources: list[CatalogSource]

    def get(self, source_id: str) -> CatalogSource | None:
        return next((s for s in self.sources if s.id == source_id), None)


@cache
def load() -> Catalog:
    data = json.loads(files("jobbot.news").joinpath("catalog.json").read_text("utf-8"))
    return Catalog(domains=data["domains"], sources=[CatalogSource(**s) for s in data["sources"]])


def search_feed(query: str, country: str, language: str) -> str:
    """Flux public de Google Actualités pour une recherche ; seuls ces trois champs partent."""
    region = "US" if country == "INT" else country
    return GOOGLE_NEWS + urlencode(
        {"q": query, "hl": language, "gl": region, "ceid": f"{region}:{language}"}
    )
