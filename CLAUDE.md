# Consignes pour Claude Code

- Interface : lire docs/regles-ui-ergonomie.md, puis le cadre Figma correspondant avant toute modification. Ne coder que des composants et variables présents dans Figma. Si un écran manque dans Figma, s'arrêter et le signaler.
  - Exception (décidée le 2026-10-23) : la migration des échelles 1.6.x (docs/135) est dispensée de la règle « écran manquant dans Figma », parce qu'elle n'ajoute aucune structure : elle remplace des valeurs par les variables de Figma, page par page. Limite : dès qu'une version 1.6.x ajouterait, retirerait ou déplacerait un élément, la règle s'applique de nouveau et il faut s'arrêter.
