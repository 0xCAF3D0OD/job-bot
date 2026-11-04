"""Le catalogue des sources des Actualités (docs/16 §4.1).

Les Actualités ont quitté la plateforme (docs/135) : le catalogue ne sert plus qu'à la migration
0064, qui en crée les sources sur une base neuve.
"""

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files


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
