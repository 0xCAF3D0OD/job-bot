## Le poids des PR contrôlé avant la fusion, pas après sur main

Kevin, 19.11.2026, 14 h 36, après que #928 puis #930, vertes chacune, ont fait dépasser Préparer sur main (main rouge,
`make deploy` bloqué) : « ajoute à la CI de chaque PR un contrôle de poids par page, qui échoue avant la fusion et pas
après sur main ». Workflow `poids-prs.yml` : à chaque changement de main, chaque PR ouverte est fusionnée à blanc avec
le nouveau main et mesurée (mêmes limites, mêmes tolérances) ; statut « Poids avec le main actuel » sur son dernier
commit. Les limites ne bougent pas.
