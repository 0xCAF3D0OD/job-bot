# 125 — Le cadre du freemium : ce qui reste gratuit, ce qui est limité, comment payer

> Statut : **validé** le 2026-10-22 (« oui pour tout »), puis les limites gratuites relevées au niveau des concurrents (« oui pour tout, vas-y ») : 150 offres notées, 10 lettres, 10 CV, 30 messages, 1 entraînement ; Plus à 7 CHF par mois ; la note avec un modèle moins cher, après comparaison.
> Origine : ta demande du 2026-10-22 : « définir le cadre du freemium […] une limite sur des features de la plateforme afin de monétiser notre plateforme, car elle nous coûte ». Reprend le point 9 et le K de l'audit des concurrents (offre payante, quotas clairs, CGU).
> Se construit sur docs/65 §4 (la clé de l'exploitant, 5 CHF par invité, 50 CHF au total), docs/102 (les comptes sur demande), docs/38, 83, 87 (chaque fonction IA a un repli sans IA).

## 1. Ce qui coûte aujourd'hui

### Les coûts fixes (par mois, quel que soit le nombre de comptes)

| Poste | Aujourd'hui | Ordre de grandeur |
|---|---|---|
| Hébergement (serveur, base, sauvegardes) | un petit serveur suffit (1 CPU, 2 Go) | 10 à 30 CHF |
| Boîte des alertes des invités (`alertes@joba1.ch`, Infomaniak) | une seule boîte, une adresse `+code` par invité | 2 à 5 CHF |
| Domaine | joba1.ch | ~1 CHF |
| Notifications (ntfy.sh), registres, flux RSS | gratuits | 0 |

### Le coût variable : l'IA, par compte actif

L'IA est presque le seul coût qui grandit avec le nombre de comptes. Estimation pour **un mois de recherche active** (les prix sont ceux écrits dans le code ; 1 $ ≈ 0,80 CHF) :

| Usage | Combien | Coût unitaire | Par mois |
|---|---|---|---|
| Notation des offres (`score`, modèle principal) | ~60 offres | 0,03 $ | ~1,80 $ |
| Lecture des e-mails d'alerte (`alert`, modèle léger) | ~30 e-mails | 0,01 à 0,03 $ | ~0,30 à 0,90 $ |
| Lettres (`letter`) et CV adaptés (`cv`) | ~8 + 8 | 0,10 $ et 0,05 $ | ~1,20 $ |
| Assistant (`chat`) | ~20 messages | 0,02 $ | ~0,40 $ |
| Entraînement à l'entretien (`practice`) | ~2 séances | 0,30 $ | ~0,60 $ |
| Le reste (relances, contacts, certificats, feuille ORP, propositions de blocs…) | | | ~0,30 $ |
| **Total** | | | **~4,50 à 5 $, soit ~3,60 à 4 CHF** |

Le plafond actuel de **5 CHF par invité** couvre donc un mois actif, et le plafond de **50 CHF au total** limite la plateforme à **une douzaine de comptes actifs**. C'est là que le freemium doit agir : au-delà, chaque compte coûte ~4 CHF par mois sans rien rapporter.

## 2. Les principes (ce qu'on ne fait pas)

1. **Le cycle ORP reste gratuit, entier, pour toujours** : la collecte des offres par les alertes, le Suivi, les preuves ORP (PDF, CSV, Job-Room), l'objectif du mois et le rattrapage, les rappels de relance, le rendez-vous ORP sans IA, le bilan. C'est ce qui distingue jobA1, et une personne au chômage ne doit jamais payer pour remplir une obligation de l'ORP.
2. **On limite l'IA, pas l'accès** : ce qui coûte, c'est l'IA ; tout ce qui ne l'appelle pas reste illimité. Chaque fonction IA garde son **repli sans IA** au-delà de la limite (un modèle de lettre, de relance, la liste triée par date…), comme aujourd'hui au plafond.
3. **Des limites en nombre, pas en francs** : « 3 lettres sur 5 ce mois-ci » se comprend ; « 2,40 CHF sur 5 CHF » non. Le plafond en francs reste caché, comme garde-fou de l'exploitant.
4. **Pas de piège** : pas d'essai qui se transforme en abonnement sans le dire, pas de résiliation cachée, pas de compte à rebours ni de culpabilité. Résilier se fait en un clic, et l'accès payé dure jusqu'à la fin du mois payé.
5. **Rien ne se perd en redescendant** : une personne qui arrête de payer garde ses lettres, ses CV, ses notes, son Suivi. Seules les nouvelles actions IA reviennent à la limite gratuite.
6. **Le prix tient compte du public** : beaucoup de personnes sont au chômage. Un prix bas, et une gratuité possible par un tiers (§5).

## 3. Les deux formules proposées

| | **Essentiel** (gratuit) | **Plus** (payant) |
|---|---|---|
| Collecte, Suivi, preuves ORP, objectif, rappels, bilan, actualités, formations | ✓ illimité | ✓ illimité |
| Offres notées par l'IA (avec la phrase « pourquoi ») | **40 par mois** ; au-delà, triées par date et par mots-clés | **200 par mois** |
| Lecture des alertes par l'IA (sites sans analyseur) | ✓ (nécessaire pour recevoir les offres) | ✓ |
| Lettres et CV adaptés par l'IA | **3 par mois** ; au-delà, le modèle à compléter | **30 par mois** |
| Assistant | **15 messages par mois** | **150 par mois** |
| Entraînement à l'entretien | **1 séance par mois** | **8 par mois** |
| Relances, contacts, certificats, feuille ORP rédigée, propositions de blocs | ✓ (coût très faible) | ✓ |

- **Le prix de Plus** : je propose **7 CHF par mois**, sans engagement (ou 60 CHF par an). Son coût IA au maximum des limites est d'environ 6 à 7 CHF ; en pratique, la plupart restent loin des maximums (~4 CHF). La marge paie l'hébergement.
- **Pourquoi 40 offres notées gratuites** : c'est environ deux semaines de recherche ; la note est la valeur la plus visible de jobA1, il faut qu'on la goûte vraiment. Coût : ~1 $.
- **Le coût d'un compte Essentiel au maximum** : ~2 CHF par mois. À couvrir par Plus et par les comptes offerts (§5).
- **L'exploitant** (ton compte) n'a pas de limite, comme aujourd'hui.

## 4. Ce que la personne voit

- **Près de chaque action IA**, au survol (là où est écrit aujourd'hui « Environ 0,10 $ ») : « 2 lettres sur 3 ce mois-ci ». Plus de prix en dollars pour un invité.
- **À la limite** : l'action reste là, avec son repli. Par exemple « Écrire la lettre » devient « Partir du modèle », et une ligne grise : « Les 3 lettres du mois sont utilisées. Elles reviennent le 1er novembre. » et un lien « Passer à Plus ». Une seule fois par écran, jamais en bandeau ni en fenêtre qui bloque.
- **Réglages › Compte › Formule** : la formule, ce qui reste ce mois-ci (une ligne par usage, en nombres), « Passer à Plus » ou « Gérer l'abonnement » (factures, moyen de paiement, résilier).
- **Aujourd'hui et le cycle ORP** : rien ne change, aucune mention de la formule.

## 5. Les comptes offerts

- **Par l'exploitant** : comme aujourd'hui, tu peux mettre un compte en Plus sans paiement (Réglages › Plateforme), pour une personne que tu accompagnes.
- **Par un tiers** (plus tard) : un code « Plus offert » que l'exploitant crée pour un organisme (une association de chômeurs, une mesure du marché du travail, un ORP qui accepterait de payer pour ses inscrits). L'organisme paie par facture ; la personne entre le code, rien d'autre. À discuter avant de construire : c'est un autre modèle (B2B), qui pourrait à terme payer davantage que les particuliers.

## 6. Le paiement

| | **Stripe** | **Payrexx** |
|---|---|---|
| Moyens | cartes, **TWINT**, Apple Pay, Google Pay, prélèvement | cartes, **TWINT**, PostFinance, Apple Pay |
| Où sont les données | entreprise américaine (données de paiement hors de Suisse) | entreprise suisse, hébergée en Suisse |
| Abonnements, factures, résiliation par la personne | oui, très complet (portail client) | oui |
| Coût | ~2,9 % + 0,30 CHF par paiement, sans frais fixes | frais fixes mensuels selon la formule + commission |
| Intégration | la plus simple et la mieux documentée | plus simple que la moyenne, moins outillée |

- **Ma recommandation** : **Payrexx**, pour rester cohérent avec « tes données restent en Suisse » ; Stripe si les frais fixes de Payrexx pèsent trop au début (à comparer avec les tarifs du moment).
- **jobA1 ne voit jamais la carte** : la page de paiement est celle du prestataire ; jobA1 ne garde que l'état de l'abonnement (formule, date de fin), reçu par un webhook signé.
- **La TVA** : pas due sous 100 000 CHF de chiffre d'affaires annuel ; à revoir si on dépasse.

## 7. Ce qu'il faut écrire avant d'encaisser

- **Des conditions d'utilisation** (CGU) : ce que fait jobA1, les formules, la résiliation, la responsabilité (jobA1 n'envoie pas les candidatures à ta place, la note n'est pas une garantie), le droit suisse.
- **La page Données personnelles** complétée : le prestataire de paiement et ce qu'il reçoit (nom, e-mail, moyen de paiement), la durée de conservation des factures (10 ans, obligation comptable).
- **Une adresse de contact** et l'identité de l'exploitant (obligation pour un service payant).
- Je peux préparer des projets de textes, mais **un juriste devrait les relire** avant d'encaisser.

## 8. Ce qui change dans le code (pour mémoire)

- **Le compte** : une formule (`essentiel`, `plus`, `offert`) et sa date de fin ; l'exploitant la règle à la main dans Plateforme.
- **Les quotas** : une seule fonction « cet usage est-il encore permis ce mois-ci ? » qui compte les appels déjà enregistrés (`llm_calls.purpose`, par compte et par mois) ; elle s'ajoute au contrôle du plafond en francs, qui reste le dernier garde-fou.
- **L'interface** : les compteurs au survol, la ligne grise à la limite, Réglages › Compte › Formule.
- **Le paiement** : la page du prestataire, le webhook, le portail pour gérer l'abonnement.

## 9. Livraison proposée

1. **0.98.0, les formules sans paiement** : la formule du compte, les quotas, l'affichage des limites, l'exploitant qui passe un compte en Plus. On mesure pendant quelques semaines ce que les comptes consomment vraiment (la rubrique Plateforme le montre déjà en francs, on l'ajoute en nombres).
2. **0.99.0, le paiement** : le prestataire choisi, l'abonnement, les CGU et la page Données personnelles à jour, après relecture des textes.
3. **Plus tard, si tu le veux** : les codes offerts par un organisme.

## Les questions

1. **Les principes (§2)** : le cycle ORP gratuit pour toujours, limiter l'IA et pas l'accès, des limites en nombres : d'accord ?
2. **Les limites gratuites (§3)** : 40 offres notées, 3 lettres ou CV, 15 messages à l'assistant, 1 entraînement par mois : trop, pas assez ?
3. **Le prix de Plus** : 7 CHF par mois (60 CHF par an) : d'accord, ou un autre prix ?
4. **Le paiement** : Payrexx (suisse) ou Stripe ?
5. **Les comptes offerts par un organisme** : à garder pour plus tard, ou à creuser maintenant (c'est peut-être le meilleur modèle pour ce public) ?
6. **L'ordre** : les formules sans paiement d'abord (0.98.0), puis le paiement (0.99.0) ?

## Complément : face aux concurrents (2026-10-22)

| | Gratuit | Payant |
|---|---|---|
| ApplyNow | ~150 offres notées (5 par jour), 25 CV et 25 lettres par mois | 18,90 CHF par mois |
| SwissJobs.app | 10 CV par semaine, 10 lettres, 5 questions d'entretien par mois | 15 CHF par mois (après un essai avec carte) |
| **jobA1** | **150 offres notées, 10 lettres, 10 CV, 30 messages, 1 entraînement**, et tout le cycle ORP | **7 CHF par mois** : 600 offres notées, 60 lettres, 60 CV, 300 messages, 8 entraînements |

- **Pourquoi relever la formule gratuite** : avec 3 lettres et 40 offres notées, la première comparaison était perdue. À ce niveau, un compte Essentiel actif coûte environ 2 CHF par mois **si la note passe à un modèle moins cher** (~0,005 $ par offre au lieu de ~0,03 $) ; sinon ~5 CHF, couverts par le plafond en francs.
- **La note moins chère** : un réglage (`JOBBOT_LLM_SCORE_MODEL`) et une commande pour comparer sur tes offres avant de changer (`uv run jobbot score-compare --model claude-sonnet-5 --limit 20`) : l'écart moyen en points, la part d'offres qui gardent le même mot, le coût moyen par offre avant et après.

## Écarts (0.98.0)

- **Règles relues avant de construire** (`docs/interface.md`), vérifiées sur captures à 1440 et 390 px : la carte Formule (Réglages › Compte), la rubrique IA d'une personne invitée, la ligne à la limite dans Préparer (lettre) et en haut des Offres (notes).
- **Les limites** : 150 offres notées, 10 lettres, 10 CV, 30 messages à l'assistant, 1 entraînement par mois en Essentiel ; 600, 60, 60, 300, 8 en Plus. Dans le code (`jobbot/plans.py`), comptées sur les appels déjà enregistrés, par mois civil. **Une offre compte une fois par mois**, même renotée (profil changé, « Je l'ai ») ; **un entraînement compte une séance**, quel que soit le nombre de questions.
- **La note dans la limite** : la notation ne prend que les nouvelles offres permises ; les autres arrivent sans note (« Pas encore notée : les offres notées du mois sont utilisées » au survol), avec une ligne en haut des Offres : « Les 150 offres notées du mois sont utilisées : elles reviennent le 1er novembre. Les nouvelles offres arrivent sans note jusque-là. Voir la formule ». Un lot déjà parti peut dépasser la limite de quelques offres.
- **À la limite d'une action** (lettre, CV, entraînement, assistant) : le bouton reste, désactivé, avec la ligne grise dessous (le même texte que l'API qui refuse, une seule source) et « Voir la formule ». **Pas de repli « Partir du modèle » pour la lettre et le CV** : ils n'existent qu'avec l'IA aujourd'hui ; les versions déjà écrites restent modifiables et téléchargeables. Un modèle de lettre sans IA serait une version à part.
- **Au survol** : pour une personne invitée, « Lettres : 2 sur 10 ce mois-ci. » sur les actions limitées, et **plus aucun prix** sur les autres actions IA (le reste de la description reste) ; l'exploitant garde les coûts.
- **Réglages › Compte › Formule** : le nom de la formule et ce qu'elle limite en une ligne grise, une ligne par usage (« 37 sur 150 » et une jauge courte) séparées par un filet, « Les compteurs repartent le 1er novembre. », puis Plus sur fond gris (ce qu'on consulte) : « Plus · 7 CHF par mois : 60 lettres, 60 CV, 8 entraînements, 600 offres notées. Le paiement arrive bientôt. » Pas de bouton tant que le paiement n'existe pas.
- **Réglages › IA** d'une personne invitée : « Formule Essentiel », ce que l'IA fait chaque mois, « Voir ce qui reste ce mois-ci » ; plus de plafond en francs ni de dépense en CHF (ils restent pour l'exploitant).
- **Réglages › Plateforme** (l'exploitant) : une liste « Formule » (Essentiel, Plus) sur chaque compte, à côté du plafond en francs, qui reste le garde-fou.
- **L'exploitant** n'a ni limite ni carte Formule.
- Migration 0068 (`users.plan`).

## Vérifié (0.98.0)

- Tests backend : le comptage par usage (une offre une fois par mois, une séance d'entraînement), les messages à la limite (accords, singulier, élision), le premier du mois suivant, la note dans la limite (renote sans compter, nouvelles offres coupées), la formule vue par une personne invitée et réglée par l'exploitant, l'exploitant sans limite. 625 tests, ruff, mypy.
- Tests de l'interface : la carte Formule, les descriptions au survol (compteur, rien, coût pour l'exploitant), la ligne à la limite, la formule choisie dans Plateforme, la rubrique IA d'une personne invitée sans francs. 438 tests, lint, vue-tsc.
- Les trois audits sur la démo à zéro.

## Écarts (0.99.0 : le paiement)

- **Fermé par défaut** : rien n'est proposé tant que `JOBBOT_BILLING_ENABLED` n'est pas vrai, et il ne l'est qu'avec l'instance, la clé de l'API et la clé de signature des webhooks de Payrexx. À ouvrir après la relecture des textes par un juriste et un essai en mode test (docs/exploitation.md, « Le paiement de Plus »).
- **Payrexx** (choisi en §6) : la page de paiement est la sienne ; jobA1 ne voit jamais la carte. Une page par achat, en abonnement mensuel, avec le retour sur Réglages › Compte.
- **On ne croit que l'API de Payrexx** : au retour de la page de paiement, jobA1 demande l'état de la page ; un webhook (public, signé HMAC-SHA256) ne sert qu'à relire la transaction auprès de l'API. Une transaction qui n'est pas à nous, ou pas confirmée, ne change rien ; la même transaction reçue deux fois ne compte qu'une fois.
- **La durée** : un paiement confirmé donne Plus jusqu'au même jour du mois suivant, plus 3 jours de grâce ; chaque renouvellement prolonge. Sans renouvellement (résilié, carte refusée, abonnement arrêté chez Payrexx), Plus s'arrête seul à cette date : le compte repasse en Essentiel, rien n'est effacé.
- **À vérifier en mode test** : la documentation de Payrexx ne détaille ni le contenu exact des webhooks ni la durée de `subscriptionPeriod` ; le code lit l'identifiant de la transaction et celui de l'abonnement s'il est là, et la période est d'un mois (à allonger si Payrexx arrête l'abonnement après un mois).
- **Réglages › Compte › Formule**, une fois le paiement ouvert : « Sans engagement. » dans la ligne de Plus, la case « J'accepte les conditions d'utilisation » (le lien mène à la page), puis « Passer à Plus » (un seul bouton plein, sans prix dans le libellé). Au retour : « Merci : Plus est actif jusqu'au 25 novembre. », « Paiement annulé : rien n'a été débité. » ou « Le paiement n'a pas abouti : rien n'a été débité. Réessaie. ». Plus payé : « Plus jusqu'au 25 novembre, renouvelé chaque mois. » et la pilule « Résilier », confirmée sur place (« Il reste actif jusqu'au 25 novembre, sans nouveau paiement. ») ; résilié : « …, puis Essentiel. Pas de nouveau paiement. ». Les paiements reçus en liste (date, montant). Plus offert : « Plus, offerte par l'exploitant », sans paiement ni résiliation.
- **Conditions d'utilisation** (`/conditions`, publique) : le service, les formules, le paiement et la résiliation (un mois commencé n'est pas remboursé), les données (lien vers Données personnelles), la responsabilité, le droit suisse, l'exploitant (ses coordonnées de Données personnelles). **Un projet** : à faire relire.
- **Données personnelles** : une rubrique « Le paiement de Plus (Payrexx) », seulement une fois le paiement ouvert : ce que Payrexx reçoit, ce que jobA1 garde, les justificatifs gardés 10 ans par Payrexx et l'exploitant.
- **La TVA** : « sans TVA (l'exploitant n'y est pas assujetti) », vrai sous 100 000 CHF de chiffre d'affaires par an.
- Migration 0069 (`users.plan_until`, `plan_cancelled_at`, références Payrexx ; la table `payments`, personnelle).

## Vérifié (0.99.0)

- Tests backend : le mois suivant (31 janvier, décembre), la page de paiement refusée sans les conditions, ouverte avec la bonne référence et le bon retour, Plus au retour confirmé, pas de seconde page une fois payé ; le webhook refusé avec une fausse signature, la transaction relue, un paiement compté une fois, une transaction étrangère ignorée, l'abonnement retenu ; Essentiel le lendemain de la fin ; la résiliation chez Payrexx, Plus gardé jusqu'au bout ; rien d'ouvert sans réglage. 629 tests, ruff, mypy.
- Tests de l'interface : le bouton désactivé tant que les conditions ne sont pas acceptées, la page de Payrexx ouverte ; le retour confirmé, l'adresse nettoyée, la date de fin, les paiements, la résiliation confirmée sur place ; le paiement annulé ; la page des conditions publique ; la rubrique paiement de Données personnelles seulement une fois ouvert. 443 tests, lint, vue-tsc.
- Captures à 1440 et 390 px de la carte Formule (paiement ouvert, Plus payé, résilié) et des conditions ; les trois audits sur la démo à zéro.
