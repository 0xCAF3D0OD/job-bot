## Code jobup : relevé partagé de la boîte tant qu'une page attend (Kevin, 15.11.2026, 18 h 24 et 18 h 49)

- L'étape « Recopie le code de jobup » signale son attente dès son affichage, puis chaque minute tant qu'elle attend et que l'onglet est visible, 10 minutes au plus ; l'attente finit 75 s après la dernière relance, ou dès que le code du compte est arrivé. « J'attends un code » et l'extension attendent 5 minutes.
- Un seul relevé partagé lit la boîte toutes les 15 s tant qu'au moins une attente est en cours, et range chaque code selon son adresse. Plafond : 240 relevés rapides par heure, un toutes les 15 s, quel que soit le nombre d'attentes ; pas de plafond par compte.
- La boîte des invités est lue même si la boîte Gmail de l'exploitant échoue, et inversement ; l'erreur est relancée après.
- Ligne d'état de l'étape : « on vérifie toutes les 15 s » (la vraie fréquence du serveur).
- Retiré : le message « Déjà six relevés rapides cette heure-ci », qui ne pouvait plus s'afficher (Kevin, 19 h 02).
- La boîte jobA1 ne répond pas (Kevin, 19 h 02) : après 3 lectures ratées de suite de la boîte des invités (Infomaniak indisponible, erreur IMAP), la ligne d'état de l'étape 3 devient « La boîte jobA1 ne répond pas. On réessaie dans 1 minute. », même style, icône d'alerte orange. Le relevé ne relit plus la boîte qu'une fois par minute tant qu'elle ne répond pas. La ligne revient à l'attente dès qu'une lecture réussit. Aucun détail technique affiché ; dans les journaux, le type d'erreur seulement, ni adresse ni code.
