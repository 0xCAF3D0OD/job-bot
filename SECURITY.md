# Signaler une faille de sécurité

Merci de prendre le temps de signaler un problème de sécurité dans jobA1.

## Comment

Par le **signalement privé de GitHub** : onglet **Security** du dépôt, puis **Report a vulnerability**. Le signalement n'est visible que de l'auteur du dépôt.

**N'ouvre pas d'issue publique** pour une faille, et n'y mets aucune donnée personnelle.

Décris :
- ce qui est touché (fichier, route de l'API, page) ;
- comment le reproduire, sur ta propre installation ;
- ce qu'un attaquant pourrait obtenir.

## Ce qui est couvert

- Le code de ce dépôt : le serveur (`backend/`), l'interface (`frontend/`), l'extension du navigateur (`extension/`) et le paquet de la démo (`deploy/demo/`).
- En particulier, tout ce qui permettrait à un compte de voir ou de modifier les données d'un autre compte.

## Ce qui ne l'est pas

- **Les installations elles-mêmes**, y compris la plateforme de l'auteur et la démo en ligne : ne fais aucun essai dessus. Installe jobA1 chez toi (`make setup`, `make dev`, ou `make demo-image`) pour tes essais.
- Les attaques par saturation, l'ingénierie sociale, les failles des services tiers (Anthropic, GitHub, hébergeur).

## Délais

- Une première réponse sous **7 jours**.
- Une correction, ou un plan daté, sous **30 jours** pour une faille grave.
- La faille est rendue publique après sa correction, avec ton accord sur la mention de ton nom.

Les règles de sécurité de la plateforme sont dans [docs/securite.md](docs/securite.md).
