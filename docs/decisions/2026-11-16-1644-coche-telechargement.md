## Coche après le téléchargement de la lettre et du CV (Kevin, 16.11.2026, 16 h 44)

- Dans « 3. Postuler », la pastille Lettre.pdf (et CV.pdf) remplace son icône de téléchargement par une coche une fois le fichier téléchargé. « Tout télécharger » coche les deux. Sur téléphone, où la pastille n'a pas d'icône, la coche s'ajoute de la même façon.
- La pastille reste un lien cliquable pour retélécharger. Son nom accessible devient « Lettre.pdf, téléchargée » (« CV.pdf, téléchargé »), pas l'icône seule.
- La coche est posée au clic (le navigateur ne dit pas si le fichier est arrivé). Elle est gardée dans ce navigateur (`localStorage`, clé `jobA1.telecharges`, 100 entrées au plus), par version du document : une lettre ou un CV refait repart sans coche. Rien n'est envoyé au serveur. La clé est effacée à la déconnexion (règle A-7).
- Aucune planche ne dessine cet état : cette décision en tient lieu. Les certificats joints et les liens « Partager » du téléphone ne sont pas concernés.
