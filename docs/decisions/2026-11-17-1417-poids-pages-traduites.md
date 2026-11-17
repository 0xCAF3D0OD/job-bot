## Poids des pages traduites : la page avec son catalogue le plus lourd (Kevin, 17.11.2026, 14 h 17)

Remplace 2026-11-17-1330-poids-catalogues-langues.md (limite propre à chaque catalogue et budget public de 365 Kio).

- Pour chaque page : sa taille, plus ce qu'elle charge hors du français (i18n.ts, son catalogue et le catalogue `commun`), dans la langue la plus lourde. Toutes les langues sont mesurées et on prend le maximum ; la langue n'est jamais fixée en dur, elle peut changer d'une page à l'autre.
- On compare aux limites actuelles des pages. Pas de nouvelle limite.
- En CI, un échec indique la page, la langue et l'écart en octets.
- La description de chaque PR de traduction contient un tableau page / langue la plus lourde / taille / limite / marge (`poids.mjs` l'imprime).
- Une page qui dépasse dans une langue suit la règle d'aujourd'hui : une décision écrite dans docs/decisions/, jamais une hausse silencieuse.
