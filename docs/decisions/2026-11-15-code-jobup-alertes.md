## Code jobup dans l'étape Alertes (Kevin, 14 et 15.11.2026)

- 14.11 : le code de vérification de jobup s'affiche dans l'étape Alertes des Premiers pas (choix « Code dans l'étape Alertes »).
- 14.11 : format d'adresse avec sous-adressage, `JOBBOT_ALERT_DOMAIN=alertes@joba1.ch` → `alertes+nom-code@joba1.ch` ; Kevin règle le serveur.
- 15.11 : la relecture toutes les 5 s ne tourne que pendant l'attente et quand l'écran est visible ; elle s'arrête dès que le code arrive ou au bout de 10 minutes sans code (état expiré, « Renvoyer »).
- 15.11 : la route ne renvoie que le dernier code du compte connecté, sans contenu de l'e-mail ; le code n'est pas journalisé.
- 15.11 : durée de validité lue dans l'e-mail de jobup, 10 minutes par défaut ; l'étape du code seulement pour jobup.
- 15.11 : l'état expiré réutilise les jetons existants `--peach-soft` / `--peach-text` (valeurs claires de la planche).
- 15.11 (réponses de Kevin sur #725) : l'état expiré garde `--peach-soft` / `--peach-text` aussi en sombre (#3A281E / #F2B98E, contraste 8,1:1) ; le libellé reste « Renvoyer », aria-label « Renvoyer le code depuis jobup » (la capture sombre du téléphone était périmée). Poids : l'allègement est fusionné d'abord, puis #723 et #725, sans toucher à la limite.
