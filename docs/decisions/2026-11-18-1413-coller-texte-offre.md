## Texte d'une offre sur téléphone : « Coller » d'abord, puis « Importer une capture ou un PDF », pas de raccourci iPhone (Kevin, 18.11.2026, 14 h 13)

Fil « Simplifier l'ajout du texte d'une offre ». Options proposées : A (captures lues par l'IA), B (raccourci iPhone
depuis Safari), C (bouton « Coller »). Kevin choisit **C puis A, pas B**.

- **« Coller » en premier** : le bouton qui ouvre le collage (« Coller le texte de l'annonce » sur téléphone,
  « Pas de lien ? Colle le texte » sur ordinateur) lit le presse-papiers (`navigator.clipboard.readText`), avec la
  demande d'autorisation du système. Le texte copié arrive dans la fenêtre de collage existante, à vérifier avant
  « Refaire la note ». Si l'accès est refusé (ou le presse-papiers vide, ou un simple lien) : la fenêtre s'ouvre vide,
  et on colle à la main. Un texte déjà commencé n'est jamais remplacé. Aucun élément ajouté : les libellés et la
  fenêtre restent ceux de la planche OffreProvisoire (paquet du 16.11).
- **Ensuite « Importer une capture ou un PDF »** : PNG, JPG ou PDF, un fichier à la fois, compté dans la formule
  (comme Q1). Le menu « + » de la planche OffreProvisoire (« Importer le PDF de l'annonce », « Importer une capture
  d'écran ») sert de dessin. PR à part.
- **Pas de raccourci iPhone.**
