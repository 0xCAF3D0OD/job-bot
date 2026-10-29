#!/usr/bin/env bash
# Depuis le Mac : envoie jobA1 sur le serveur et l'y pilote (docs/136). Appelé par le Makefile
# (make deploy, make deploy-install, make prod-…) ; réglages : SERVER, SSH_KEY, REMOTE_DIR.
#
# Seuls les fichiers de deploy/ du commit choisi partent sur le serveur (git archive, par SSH) :
# le code voyage dans les images construites par GitHub (.github/workflows/images.yml).
set -euo pipefail

SERVER="${SERVER:-ubuntu@179.237.122.64}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/jobbot}"
REMOTE_DIR="${REMOTE_DIR:-joba1}"
DEPOT="0xCAF3D0OD/job-bot"
SSH=(ssh -i "$SSH_KEY" -o ServerAliveInterval=30)

etape() { printf '\033[1m▸ %s\033[0m\n' "$1"; }
erreur() { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; exit 1; }
sur_le_serveur() { "${SSH[@]}" -t "$SERVER" "bash ~/$REMOTE_DIR/deploy/prod/serveur.sh $*"; }

cd "$(git rev-parse --show-toplevel)"

# Le commit à envoyer : REF s'il est donné, sinon le plus récent de main dont les tests et les
# images ont réussi. (Le commit du changelog, poussé par le robot, n'a ni l'un ni l'autre.)
reussi() {  # reussi <workflow> <commit>
  [ "$(gh run list -R "$DEPOT" --workflow "$1" --commit "$2" --status success --limit 1 \
    --json databaseId -q length)" = "1" ]
}
choisir_commit() {
  command -v gh >/dev/null || erreur "gh (GitHub CLI) manquant : brew install gh, puis gh auth login."
  git fetch -q origin
  if [ -n "${REF:-}" ]; then
    local sha
    sha="$(git rev-parse --verify "$REF^{commit}")" || erreur "Commit inconnu : $REF"
    reussi images.yml "$sha" || erreur "Pas d'images pour ${sha:0:7} : gh run list -R $DEPOT --workflow images.yml"
    reussi tests.yml "$sha" || erreur "Les tests de ${sha:0:7} n'ont pas réussi : gh run list -R $DEPOT --workflow tests.yml"
    echo "$sha"
    return
  fi
  local sha
  for sha in $(gh run list -R "$DEPOT" --workflow images.yml --branch main --event push \
      --status success --limit 15 --json headSha -q '.[].headSha'); do
    if reussi tests.yml "$sha"; then echo "$sha"; return; fi
  done
  erreur "Aucun commit récent de main n'a ses images et ses tests réussis : gh run list -R $DEPOT --workflow images.yml"
}

envoyer_fichiers() {  # envoyer_fichiers <commit>
  git archive --format=tar "$1" deploy \
    | "${SSH[@]}" "$SERVER" "mkdir -p ~/$REMOTE_DIR && tar -x -C ~/$REMOTE_DIR"
}

annoncer() {  # annoncer <commit> : ce qui part, et ce qui tourne aujourd'hui
  local actuel
  actuel="$("${SSH[@]}" "$SERVER" "grep -E '^JOBA1_TAG=' ~/$REMOTE_DIR/deploy/prod/.env 2>/dev/null | cut -d= -f2-" || true)"
  echo "  Envoi    : $(git log -1 --format='%h %s (%cd)' --date=format:'%d.%m %H:%M' "$1")"
  if [ -n "$actuel" ] && git cat-file -e "$actuel^{commit}" 2>/dev/null; then
    if [ "$actuel" = "$1" ]; then
      echo "  En place : la même version (relance)"
    else
      echo "  En place : $(git log -1 --format='%h %s' "$actuel") — $(git rev-list --count "$actuel..$1") commits de plus"
    fi
  fi
}

case "${1:-}" in
  deploy)
    sha="$(choisir_commit)"
    annoncer "$sha"
    etape "Envoi des fichiers de deploy/"
    envoyer_fichiers "$sha"
    sur_le_serveur mettre-a-jour "$sha"
    ;;
  install)
    [ -n "${DOMAIN:-}" ] || erreur "Indique l'adresse : make deploy-install DOMAIN=app.joba1.ch"
    sha="$(choisir_commit)"
    annoncer "$sha"
    etape "Envoi des fichiers de deploy/"
    envoyer_fichiers "$sha"
    sur_le_serveur installer "$DOMAIN"
    sur_le_serveur mettre-a-jour "$sha"
    echo
    echo "Ensuite : make prod-reglages (clé d'IA, boîtes e-mail, phrase des sauvegardes),"
    echo "puis make prod-restaurer FICHIER=… (tes données du Mac) ou make prod-mot-de-passe."
    ;;
  etat) sur_le_serveur etat ;;
  logs) "${SSH[@]}" -t "$SERVER" "sudo docker compose -f ~/$REMOTE_DIR/deploy/prod/docker-compose.yml logs -f --tail 100 ${SERVICES:-api worker web}" ;;
  ssh) "${SSH[@]}" -t "$SERVER" "cd ~/$REMOTE_DIR && exec \$SHELL -l" ;;
  reglages)
    "${SSH[@]}" -t "$SERVER" "nano ~/$REMOTE_DIR/deploy/prod/jobbot.env"
    sur_le_serveur relancer
    ;;
  mot-de-passe) sur_le_serveur jobbot set-password ;;
  sauvegardes)
    dest="${DEST:-$HOME/Documents/joba1-sauvegardes-serveur}"
    mkdir -p "$dest" && chmod 700 "$dest"
    rsync -a --rsync-path="sudo rsync" -e "ssh -i $SSH_KEY" "$SERVER:$REMOTE_DIR/sauvegardes/" "$dest/"
    echo "✓ Sauvegardes du serveur copiées dans $dest ($(ls "$dest" | wc -l | tr -d ' ') fichiers)"
    ;;
  restaurer)
    [ -f "${FICHIER:-}" ] || erreur "Fichier introuvable : « ${FICHIER:-} ». Indique le chemin complet d'une sauvegarde (dossier JOBBOT_BACKUP_PATH du .env) : make prod-restaurer FICHIER=\"…/jobA1-AAAA-MM-JJ-HHMM.jobA1backup\""
    nom="$(basename "$FICHIER")"
    etape "Envoi de $nom"
    scp -q -i "$SSH_KEY" "$FICHIER" "$SERVER:/tmp/$nom"
    "${SSH[@]}" "$SERVER" "sudo mv /tmp/$nom ~/$REMOTE_DIR/sauvegardes/ && sudo chown 10001 ~/$REMOTE_DIR/sauvegardes/$nom && sudo chmod 600 ~/$REMOTE_DIR/sauvegardes/$nom"
    sur_le_serveur jobbot restore "$nom"
    sur_le_serveur relancer
    ;;
  *) erreur "Usage : mac.sh deploy | install | etat | logs | ssh | reglages | mot-de-passe | sauvegardes | restaurer" ;;
esac
