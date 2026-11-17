## Ajouter une offre déjà là (Kevin, 17.11.2026, 0 h 29)

Retour de Kevin sur la #818. On ne crée plus directement une offre déjà présente.

1. Pas d'encadré. Le message va sous le champ « Lien ou texte de l'annonce » (icône et texte, `role="alert"`), puis
   ses boutons. Tant qu'il est affiché, ces boutons remplacent « Ajouter l'offre » du bas.
2. Doublon sûr (même lien) : « Cette offre est déjà dans tes candidatures (ajoutée le {date}). » Un seul bouton plein,
   « Ouvrir l'offre ». Pas d'« Ajouter quand même » : le serveur ouvre l'offre déjà là même si on le lui demande.
3. Doublon probable (même titre et même entreprise, lien différent) : « Une offre très proche est déjà là : {titre}
   chez {entreprise}, ajoutée le {date}. » Bouton plein « Ouvrir l'offre », bouton contour « Ajouter quand même ».
   L'offre ajoutée quand même porte la pastille « Déjà postulé le … » si une candidature a été envoyée, comme dans le
   fil (#810).
4. Changer le lien ou le texte du champ fait disparaître le message et revenir « Ajouter l'offre ».
