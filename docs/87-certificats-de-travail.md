# 87 — Les certificats de travail, décodés (versions 0.69.0 et 0.69.1)

> Statut : **validé** le 2026-10-19.
> Origine : ton choix du 2026-10-19 pour démarquer jobA1 d'ApplyCH et de SwissJobs.app. Ni l'une ni l'autre ne s'occupe des certificats de travail.

## 1. Le constat

En Suisse, un certificat de travail doit rester bienveillant. Les employeurs ont donc pris l'habitude de formules codées :
- « toujours à notre **plus grande** satisfaction » veut dire *très bien* ;
- « à notre **entière** satisfaction », *bien* ;
- « à notre satisfaction », *suffisant* ;
- « **s'est efforcé** de… », *insuffisant*.

D'autres détails comptent aussi :
- dans le comportement, l'ordre des mentions (supérieurs avant collègues) ;
- une formule de fin avec ou sans regrets, remerciements et vœux ;
- le motif du départ, s'il est donné ;
- et surtout **ce qui manque**.

En allemand, l'*Arbeitszeugnis* suit un code plus strict encore.

La personne qui cherche un emploi ne le sait souvent pas. Elle joint tous ses certificats, y compris celui qui la dessert. Les recruteurs, eux, savent lire ce code.

## 2. En clair

Dans **Profil › Parcours**, chaque document déposé peut être marqué comme **certificat de travail**. Pour chacun, jobA1 affiche :

1. **La note** : *très bon*, *bon*, *suffisant* ou *à revoir*, avec une phrase qui l'explique. Par exemple : « Les formules de prestation sont celles d'un très bon certificat ; la formule de fin ne contient pas de regrets. »
2. **Phrase par phrase** : les passages codés sont surlignés, avec ce qu'ils veulent dire. Par exemple, « à notre entière satisfaction » signifie *bien, pas très bien*.
3. **Ce qui te dessert**, s'il y a quelque chose :
   - une formule faible ;
   - un ordre inhabituel ;
   - des tâches importantes passées sous silence ;
   - une fin sans remerciements.
4. **Le conseil** : *à joindre*, *à joindre si on le demande*, ou *à faire corriger d'abord*.

Pour l'ensemble des certificats, une ligne résume ce qu'il faut joindre : « Joins Acme SA et Exemple Sàrl. Pour Démo SA, demande d'abord une correction. »

## 3. Avec ou sans IA

- **Sans IA**, gratuit et immédiat : une liste écrite des formules connues, en français et en allemand, repère les passages codés et donne une première note. Ce sont des règles visibles, que l'on peut tester.
- **Avec l'IA**, sur demande (« Lire en détail », environ 0,03 CHF par certificat) :
  - la note expliquée ;
  - ce qui manque ;
  - l'ordre des mentions ;
  - le conseil.

  L'IA part des passages déjà repérés par les règles et ne peut pas inventer de formule.
- **Ce qui part à l'IA** : le texte du certificat seulement. Avant l'envoi, jobA1 retire :
  - ton nom ;
  - tes coordonnées ;
  - les noms des personnes : signataires et supérieurs, repérés après « M. », « Mme », « Herr », « Frau » et dans le bloc de signature.

  Le nom des entreprises reste, comme pour les offres. Si un nom de personne échappe à ce filtre, il est remplacé dans l'affichage, mais il aura pu partir : la page le dit.

## 4. En 0.69.1

- **Demander une correction** : jobA1 rédige une lettre polie à l'ancien employeur pour demander de reformuler un passage précis, avec ta formulation proposée. Tu la relis, puis tu l'envoies toi-même.
- **Le certificat intermédiaire** : si tu es encore en poste ou en préavis, jobA1 propose de le demander, avec une lettre prête.
- **Dans Préparer ma candidature** : la liste des pièces jointes propose les certificats marqués *à joindre*, dans l'ordre chronologique inverse.

## 5. Ce qu'on ne fait pas

- **Pas d'avis juridique** sur tes droits ni sur un litige avec un employeur. La lettre de correction demande poliment, elle ne menace pas. Pour aller plus loin, la page renvoie vers ton conseiller ORP ou un service juridique.
- **Rien n'est modifié** dans tes documents. jobA1 lit, explique et conseille.
- **Pas de note sur la personne** : c'est le document qui est évalué, jamais toi.
- **Pas de certitude** : une lecture reste une interprétation. La page le dit, et montre toujours la phrase d'origine.

## 6. Données

- `documents` gagne une colonne `kind`, avec `certificate` pour un certificat de travail. Rien ne change pour les autres documents.
- Une table **`certificate_readings`**, personnelle, une ligne par certificat :
  - les passages repérés ;
  - la note ;
  - la lecture de l'IA ;
  - le conseil ;
  - la date.

  Elle est rangée dans la famille **personnelle**, avec sa règle `account_isolation`, comme les autres (docs/78).
- La liste des formules est un fichier du code (`certificates/formulas.py`), avec des tests. Elle s'enrichit d'une version à l'autre.

## 7. Livraison en deux PR

| Version | Contenu |
|---|---|
| **0.69.0** | Marquer un certificat ; la lecture sans IA (formules, note, passages) ; « Lire en détail » avec l'IA ; le conseil et le résumé « quoi joindre » |
| **0.69.1** | La lettre de correction, le certificat intermédiaire, les certificats dans Préparer ma candidature |

Vérifié à chaque fois :
- tests serveur et interface, dont une série de certificats fictifs (très bon, bon, faible, codé en allemand) ;
- un test qui vérifie que ni ton nom ni ceux des signataires ne partent à l'IA ;
- captures sur ordinateur et téléphone, en clair et en sombre ;
- la démo, avec deux certificats fictifs.

## Points à valider

1. **Marquer un document comme certificat**, dans Profil › Parcours (§2).
2. **La lecture sans IA d'abord**, avec les formules connues en français et en allemand ; l'IA seulement sur demande, environ 0,03 CHF (§3).
3. **Les noms retirés avant l'IA** : le tien et ceux des personnes ; le nom des entreprises reste (§3).
4. **Le conseil** (*à joindre*, *si on le demande*, *à faire corriger*), et la lettre de correction en 0.69.1 (§2, §4).
5. **Pas d'avis juridique** ; la lettre reste polie (§5).

## Écarts avec le cadrage (0.69.0)

- **Marquer un certificat** : depuis le menu ⋯ du document ouvert (« C'est un certificat de travail »). Une phrase sous la liste des documents le rappelle tant qu'aucun n'est marqué. Un certificat n'affiche plus « Proposer des blocs ».
- **La section « Certificats de travail »** suit les documents. Elle montre :
  - le résumé : quoi joindre, quoi faire corriger ;
  - pour chaque certificat, la note, la formule clé et le conseil ;
  - « Voir phrase par phrase » pour les passages repérés et ce qui manque.
- **La note** est la plus basse des formules de prestation trouvées, par prudence. Si l'IA a lu le certificat, sa note, son explication et son conseil passent devant.
- **Les noms retirés avant l'IA** : ton nom (entier et chaque mot), les personnes nommées après un titre (M., Mme, Madame, Monsieur, Herr, Frau, Dr, Prof), et, dans les 10 dernières lignes, une ligne de deux ou trois mots capitalisés (la signature). Le test vérifie qu'aucun de ces noms ne part.
- **La démo** a deux certificats fictifs : un très bon, un à faire corriger.
- **Vérifié** :
  - 529 tests serveur, dont 4 nouveaux (`test_certificates.py`) ; la table entre dans la famille personnelle, et le test des liens en compte 22 ;
  - les tests de l'interface, dont 3 nouveaux ;
  - sur une démo de brouillon : la section sur ordinateur (clair) et téléphone (sombre), sans débordement.

## Écarts avec le cadrage (0.69.1)

- **La lettre de correction** s'ouvre d'abord sur un modèle simple, sans IA et gratuit. Il cite chaque passage qui dessert, avec une proposition :
  - « toujours à notre entière satisfaction » pour une formule de prestation faible ;
  - une phrase sans « s'efforcer » ;
  - ne pas mentionner le motif du départ ;
  - ajouter une formule de fin.

  « Rédiger avec l'IA » (environ 0,02 CHF) la reformule, sans ton nom ni les personnes nommées ; ta signature est ajoutée par jobA1. La lettre est en allemand pour un certificat en allemand.
- **La lettre modèle se lit sans rien enregistrer** (GET) : elle marche aussi dans la démo. La version de l'IA passe par POST.
- **« Demander une correction »** est proposé pour les certificats *à faire corriger* et *si on le demande*, pas pour ceux *à joindre*.
- **Le certificat intermédiaire** : un lien sous la liste des documents, et en tête de la section des certificats. La lettre est un modèle, sans IA.
- **Dans Préparer ma candidature**, les certificats *à joindre* sont dans la section « À recopier sur le site de l'employeur », visible aussi sur téléphone ; ceux *à faire corriger* sont rappelés à part. L'ordre suit la dernière année citée dans chaque certificat, la plus récente d'abord.
- **La limite du retrait des noms** est maintenant dite sur la page : un nom cité seul dans une phrase, sans titre, pourrait partir à l'IA.
- **Vérifié** :
  - 530 tests serveur, dont 1 nouveau sur les lettres ;
  - 312 tests de l'interface, dont 4 nouveaux (le test du routeur dépasse son délai dans la suite complète, comme sur main) ;
  - sur une démo de brouillon : la lettre ouverte (ordinateur), et « Postuler » avec les certificats (téléphone, sombre), sans débordement.

