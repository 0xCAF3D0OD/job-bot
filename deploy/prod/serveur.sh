#!/usr/bin/env bash
# La vraie plateforme jobA1 et la démo sur le serveur (docs/136). Lancé par le Makefile depuis
# le Mac (make deploy-install, make deploy), dans ~/joba1/deploy/prod :
#
#   bash serveur.sh installer app.joba1.ch   une fois : Docker, swap, réglages, mots de passe
#   bash serveur.sh mettre-a-jour <commit>   télécharge les images de ce commit et relance tout
#   bash serveur.sh etat                     l'état des services
#   bash serveur.sh relancer                 l'API et le worker relisent leurs réglages
#   bash serveur.sh jobbot <commande>        une commande jobbot (set-password, restore…)
#
# Rien n'est compilé ici : les images viennent de GitHub (ghcr.io), construites par
# .github/workflows/images.yml. Le script appelle sudo lui-même : lance-le avec ubuntu.
set -euo pipefail

PROD="$(cd "$(dirname "$0")" && pwd)"
PROJET="$(cd "$PROD/../.." && pwd)"
DEMO_DIR="$PROJET/deploy/demo"
ANCIENNE_DEMO="/root/job-bot/deploy/demo"   # la démo installée à la main le 18.10.2026 (docs/77)

etape() { printf '\n\033[1m▸ %s\033[0m\n' "$1"; }
erreur() { printf '\n\033[31m✗ %s\033[0m\n' "$1" >&2; exit 1; }
reglage() { grep -E "^$1=" "$2" 2>/dev/null | tail -1 | cut -d= -f2- || true; }
poser() {  # poser CLE VALEUR FICHIER : remplace la ligne, ou l'ajoute (droits du fichier gardés)
  local tmp
  tmp="$(mktemp)"
  grep -vE "^$1=" "$3" > "$tmp" || true
  printf '%s=%s\n' "$1" "$2" >> "$tmp"
  cat "$tmp" > "$3"
  rm -f "$tmp"
}

[ "$(id -un)" = "root" ] && erreur "Lance ce script avec ton utilisateur (ubuntu), pas en root : il appelle sudo lui-même."

# Les deux projets Docker : la plateforme (joba1) et la démo (joba1-demo, sur l'image de la
# plateforme). JOBA1_TAG et JOBA1_REGISTRY passent par `env`, que sudo n'efface pas.
plateforme() { sudo docker compose -f "$PROD/docker-compose.yml" "$@"; }
demo() {
  sudo env "JOBA1_TAG=$(reglage JOBA1_TAG "$PROD/.env")" \
    "JOBA1_REGISTRY=$(reglage JOBA1_REGISTRY "$PROD/.env")" \
    docker compose -p joba1-demo -f "$DEMO_DIR/docker-compose.yml" -f "$PROD/demo.yml" "$@"
}
# Une commande jobbot avec l'accès propriétaire, sans relancer la base ; la seconde garde le
# clavier (set-password, restore).
jobbot() { plateforme run --rm --no-deps -T migrate jobbot "$@"; }
jobbot_clavier() { plateforme run --rm --no-deps migrate jobbot "$@"; }

installer() {
  local domaine="${1:-}"
  domaine="$(printf '%s' "$domaine" | tr '[:upper:]' '[:lower:]' | sed -E 's#^https?://##; s#/.*$##')"
  [[ "$domaine" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]] \
    || erreur "Indique l'adresse de la plateforme, par exemple : make deploy-install DOMAIN=app.joba1.ch"

  etape "Adresse $domaine"
  local ip_dns ips
  ip_dns="$(getent ahostsv4 "$domaine" | awk 'NR==1 {print $1}' || true)"
  ips="$(hostname -I) $(curl -fsS -m 5 https://api.ipify.org 2>/dev/null || true)"
  if [ -z "$ip_dns" ]; then
    echo "  ⚠ $domaine ne pointe encore vers rien : crée un enregistrement A vers ce serveur."
    echo "    La plateforme démarre quand même ; Caddy obtiendra le certificat dès que le DNS suit."
  elif [[ " $ips " != *" $ip_dns "* ]]; then
    echo "  ⚠ $domaine pointe vers $ip_dns, pas vers ce serveur ($ips)."
  else
    echo "  OK : $domaine → $ip_dns"
  fi

  etape "Docker"
  if ! command -v docker >/dev/null; then
    curl -fsSL https://get.docker.com | sudo sh >/dev/null
  fi
  sudo docker compose version

  etape "Mémoire d'appoint (swap, 2 Go)"
  # 2 Go de mémoire sans swap : un pic (mise à jour, sauvegarde) arrêterait un service.
  if [ -z "$(swapon --show --noheadings)" ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap -q /swapfile
    sudo swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
    echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-joba1.conf >/dev/null
    sudo sysctl -q -p /etc/sysctl.d/99-joba1.conf
    echo "  Swap de 2 Go ajouté."
  else
    echo "  Déjà là."
  fi

  etape "Place sur le disque"
  # Le cache des constructions de la démo (docs/77) : inutile, les images viennent de GitHub.
  sudo docker builder prune -af >/dev/null
  df -h / | awk 'NR==2 {print "  " $4 " libres sur " $2}'

  etape "Réglages de la démo"
  if [ ! -f "$DEMO_DIR/.env" ]; then
    if sudo test -f "$ANCIENNE_DEMO/.env"; then
      # Même base, même mot de passe : la démo garde ses données et son certificat.
      sudo cp "$ANCIENNE_DEMO/.env" "$DEMO_DIR/.env"
      sudo chown "$(id -un):" "$DEMO_DIR/.env"
      echo "  Repris de $ANCIENNE_DEMO."
    else
      cp "$DEMO_DIR/.env.example" "$DEMO_DIR/.env"
      echo "  Créés depuis .env.example (demo.joba1.ch)."
    fi
    chmod 600 "$DEMO_DIR/.env"
  else
    echo "  Déjà là."
  fi

  etape "Réglages de la plateforme"
  local env="$PROD/.env"
  touch "$env"
  chmod 600 "$env"
  poser APP_DOMAIN "$domaine" "$env"
  poser DEMO_DOMAIN "$(reglage DEMO_DOMAIN "$DEMO_DIR/.env")" "$env"
  # Les mots de passe de la base : tirés au hasard une fois, jamais affichés, jamais changés
  # ensuite (la base les garde).
  for cle in POSTGRES_PASSWORD APP_DB_PASSWORD WORKER_DB_PASSWORD; do
    [ -n "$(reglage "$cle" "$env")" ] || poser "$cle" "$(openssl rand -hex 24)" "$env"
  done
  if [ ! -f "$PROD/jobbot.env" ]; then
    cp "$PROD/jobbot.env.example" "$PROD/jobbot.env"
    poser JOBBOT_DEMO_URL "https://$(reglage DEMO_DOMAIN "$env")" "$PROD/jobbot.env"
  fi
  chmod 600 "$PROD/jobbot.env"
  echo "  $env et $PROD/jobbot.env prêts."

  etape "Dossier des sauvegardes"
  mkdir -p "$PROJET/sauvegardes"
  # L'utilisateur des conteneurs (10001) y écrit ; personne d'autre ne lit.
  sudo chown 10001 "$PROJET/sauvegardes"
  sudo chmod 700 "$PROJET/sauvegardes"
  echo "  $PROJET/sauvegardes (copie sur le Mac : make prod-sauvegardes)"

  # Pare-feu : seulement le web, s'il est actif.
  if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    sudo ufw allow 80/tcp >/dev/null && sudo ufw allow 443 >/dev/null
    echo "  Pare-feu ufw : ports 80 et 443 ouverts."
  fi
}

mettre_a_jour() {
  local tag="${1:-}"
  [[ "$tag" =~ ^[0-9a-f]{40}$ ]] || erreur "Commit attendu (40 caractères), reçu « $tag »."
  [ -f "$PROD/.env" ] || erreur "Pas encore installé : make deploy-install DOMAIN=app.joba1.ch depuis le Mac."
  poser JOBA1_TAG "$tag" "$PROD/.env"

  etape "Images du commit ${tag:0:7}"
  if ! plateforme pull --quiet; then
    erreur "Images introuvables. Soit GitHub ne les a pas encore construites (gh run list --workflow images.yml),
  soit les paquets joba1-api et joba1-web sont encore privés sur GitHub (docs/136 §4)."
  fi
  demo pull --quiet api

  local en_marche=false
  if [ -n "$(plateforme ps -q api 2>/dev/null)" ]; then
    en_marche=true
    etape "Maintenance annoncée"
    jobbot maintenance on "Mise à jour de jobA1" \
      || echo "  (pas annoncée : la mise à jour continue)"
  fi

  # La démo installée à la main (docs/77) tenait les ports 80 et 443 avec son propre Caddy :
  # le Caddy de la plateforme sert désormais les deux sites.
  if [ -n "$(sudo docker ps -q --filter name='^joba1-demo-web-1$')" ]; then
    etape "Arrêt de l'ancien site de la démo"
    sudo docker rm -f joba1-demo-web-1 >/dev/null
  fi

  etape "Plateforme : schéma, API, worker, site"
  if ! plateforme up -d --wait --remove-orphans; then
    plateforme ps -a
    erreur "La plateforme ne démarre pas. Journal : make prod-logs (la maintenance reste annoncée)."
  fi

  if [ "$en_marche" = true ]; then
    etape "Maintenance levée"
    jobbot maintenance off
  fi

  etape "Démo"
  demo up -d --wait --no-build

  etape "Ménage"
  sudo docker image prune -af >/dev/null
  sudo docker builder prune -af >/dev/null

  etape "Vérification"
  plateforme exec -T api python -c "import json, urllib.request; v = json.load(urllib.request.urlopen('http://127.0.0.1:8000/version')); print('  Plateforme :', v['version'], '· migration', v['migration_head'])"
  # Caddy doit joindre la plateforme, pas la démo (les deux sont sur le réseau partagé).
  plateforme exec -T web wget -qO- http://app-api:8000/api/auth/me | grep -q '"demo":false' \
    || erreur "https://$(reglage APP_DOMAIN "$PROD/.env") ne mène pas à la plateforme (Caddy joint une autre API)"
  printf '\n\033[1;32m✓ jobA1 est à jour\033[0m : https://%s  ·  démo : https://%s\n' \
    "$(reglage APP_DOMAIN "$PROD/.env")" "$(reglage DEMO_DOMAIN "$PROD/.env")"
}

etat() {
  plateforme ps --format 'table {{.Service}}\t{{.Status}}'
  echo
  demo ps --format 'table {{.Service}}\t{{.Status}}'
  echo
  free -m | awk 'NR==2 {print "Mémoire : " $3 " Mo utilisés sur " $2} NR==3 {print "Swap : " $3 " Mo sur " $2}'
  df -h / | awk 'NR==2 {print "Disque : " $4 " libres sur " $2}'
}

case "${1:-}" in
  installer) installer "${2:-}" ;;
  mettre-a-jour) mettre_a_jour "${2:-}" ;;
  etat) etat ;;
  # Après un changement de jobbot.env ou une restauration : l'API et le worker relisent tout.
  relancer) plateforme up -d --wait --force-recreate api worker && echo "✓ API et worker relancés" ;;
  jobbot) shift; jobbot_clavier "$@" ;;
  *) erreur "Usage : serveur.sh installer <adresse> | mettre-a-jour <commit> | etat | relancer | jobbot <commande>" ;;
esac
