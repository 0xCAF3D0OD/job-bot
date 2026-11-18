## Retour d'une candidature et bouton rond flottant (Kevin, 17.11.2026, 21 h 05)

- Téléphone : une candidature ouverte a sa propre adresse (`?candidature=ID`). Le retour du navigateur et le retour de l'app ferment la fiche et ramènent à la liste, à la même position de défilement (audit du 17.11, N25).
- Bouton rond flottant (Candidatures sur téléphone, Assistant sur ordinateur) : il ne se masque pas au défilement. La page a un `scroll-padding-bottom` égal à la hauteur du bouton plus sa marge : un élément qui reçoit le focus ne passe jamais dessous (WCAG 2.4.11), et le dernier élément de la page reste entièrement visible au-dessus du bouton.
