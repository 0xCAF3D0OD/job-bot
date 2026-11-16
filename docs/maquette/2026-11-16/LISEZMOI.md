# Paquet jobA1_maquette_2026-11-16_bilan (extrait Bilan)

Recopié du LISEZMOI_CORRECTIONS.md du paquet : section 29 seulement. Planches dans maquettes/, rendus dans captures/bilan-etats/.

## 29. Bilan sur ordinateur : les 9 états sans planche (clair et sombre)

Planches : BilanOrdinateur(+Sombre) mises à jour, et BilanOrdinateurMois, BilanOrdinateurMoisPrecedents, BilanOrdinateurExports, BilanOrdinateurFicheSombre, BilanOrdinateurFormVide, BilanOrdinateurCatalogue, BilanOrdinateurFormEtats, BilanOrdinateurTropTot, BilanOrdinateurChargement, BilanOrdinateurErreur (chacune avec sa version Sombre, sauf la fiche qui n'existe qu'en sombre ici). Captures : captures/bilan-etats/.

ORP
- En bas de la page ORP, sous « Rendez-vous ORP » : deux boutons pilule contour (44 px) « Mois précédents » (icône calendrier) et « Autres exports » (icône téléchargement), avec chevron bas. Ils sont maintenant sur la planche principale aussi.
- Menu « Mois précédents » ouvert : s'ouvre vers le haut, largeur 300 px, rayon 16 px, ombre 0 12px 32px rgba(27,31,42,.16) ; 6 mois (octobre 2026 à mai 2026), une ligne de 44 px par mois avec l'icône calendrier. Le mois dont les justificatifs sont à remettre porte « À remettre » en orange (#8A4A16 / sombre #F2B98E), comme le bandeau du haut. Chevron du bouton vers le haut quand le menu est ouvert.
- Menu « Autres exports » : même style, 2 lignes : « Télécharger en CSV (Excel) » et « PDF avec le journal des recherches ».
- Mois déplié (?tout=1) : les 11 recherches à déclarer s'affichent toutes, sans « Voir les 8 autres ». Le chevron de la carte Novembre pointe vers le haut. « Voir tout le mois et les justificatifs » est remplacé par le lien « Replier le mois » (chevron haut), qui revient à la vue normale (retire ?tout=1). Nouveau : aujourd'hui seul le bouton Retour du navigateur permettait de revenir.
- Fiche « Pour l'ORP » en sombre : mêmes jetons sombres que le reste de l'app.

Formations
- Aucune formation suivie : l'encadré « L'ORP peut financer une formation » reste en haut ; dessous, état vide centré : scène « introuvable » (troupe), titre « Aucune formation suivie », pastille bleue (icône signet) « Garde une formation du catalogue avec son signet », bouton principal 52 px « Voir le catalogue » (icône livre). Le libellé « Chercher d'autres formations » n'est pas utilisé ici : il n'y en a pas encore.
- Catalogue : lien « ← Mes formations » en haut ; encadré pêche (#FFF1E6) « Financement possible par l'ORP / Seulement avec l'accord préalable de l'ORP » avec icône étiquette et flèche ; puces Tout / Certifications / Cours | Gratuites / En français (puce active : fond #1B1F2A, texte blanc ; sombre : fond #F3EEE6, texte #171411) ; une carte par section (« Certifications », « Cours et ateliers », avec le nombre à droite). Ligne : icône 40 px (étoile sur fond orange clair pour une certification, livre sur fond bleu clair pour un cours), titre sur 1 ligne, ligne 2 : organisme · format · niveau + pastille « Gratuit » (verte) ou « Payant » (neutre). À droite, bouton signet rond 44 px : contour gris si pas gardée, fond #E8ECFB et signet plein si gardée (aria-pressed). Puis « Chercher d'autres formations » en pilule contour.
- En cours sans nombre de modules : sous le titre, le texte libre sur 1 ligne (points de suspension) en #3D4250, et à droite le lien « Noter l'avancement ». Une formation avec modules garde la barre et « Module N sur 12 ».
- Terminée dans « Gardées » : à droite, coche + « Terminée » en vert (#17734A / sombre #62D497), puis la flèche ronde.

Résultats
- Trop tôt pour conclure : état vide centré, scène « groupe » (troupe, 300 px), pastille bleue (icône graphique) « Le Bilan se remplit avec tes premières candidatures et réponses », bouton principal « Voir les offres » (icône mallette).
- Chargement : 3 blocs gris (#ECE9E1 / sombre #2C2722) aux formes du contenu (chiffres, « Le mois en bref », « Ce qui bloque »), reflet animé ; aria-busy="true". Animation coupée si prefers-reduced-motion.
- Erreur (remplace la ligne rouge actuelle) : état vide centré, NOUVELLE scène « erreur » (illustrations/erreur-480|840.webp et erreur-sombre-480|840.webp, affichée à 360 px de large), titre « Bilan indisponible pour l'instant » (role="alert"), pastille bleue (coche) « Tes candidatures et ton suivi ORP ne sont pas touchés », bouton principal « Réessayer » (icône flèche circulaire) qui relance le chargement. Hors ligne : garder NetworkError tel quel.
