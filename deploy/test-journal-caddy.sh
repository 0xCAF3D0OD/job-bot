#!/bin/sh
# Le journal d'accès de Caddy ne garde ni identifiant ni paramètre (décision de Kevin du 17.11.2026).
# Lance les Caddyfile de deploy/prod et deploy/demo en local (journal dans un dossier temporaire au
# lieu de /data), envoie GET /api/interviews/123?x=1 et vérifie la ligne écrite :
# « /api/interviews/:id », sans adresse complète, sans paramètre, sans Referer.
# Usage : make test-journal-caddy (CADDY=/chemin/vers/caddy si caddy n'est pas dans le PATH).
set -eu

CADDY=${CADDY:-caddy}
racine=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
pid=""
trap '[ -n "$pid" ] && kill "$pid" 2>/dev/null; rm -rf "$tmp"' EXIT INT TERM

essai() {
	nom=$1
	fichier=$2
	journal=$3
	port=$4
	# Le port de l'autre site du fichier (la démo, dans deploy/prod/Caddyfile).
	autre=$5
	sed "s#/data/#$tmp/#g" "$racine/$fichier" > "$tmp/Caddyfile"
	APP_DOMAIN="http://localhost:$port" DEMO_DOMAIN="http://localhost:$autre" \
		"$CADDY" run --config "$tmp/Caddyfile" --adapter caddyfile > "$tmp/caddy.log" 2>&1 &
	pid=$!
	i=0
	until curl -s -o /dev/null "http://localhost:$port/"; do
		i=$((i + 1))
		[ "$i" -lt 50 ] || { cat "$tmp/caddy.log"; echo "ÉCHEC $nom : Caddy ne démarre pas"; exit 1; }
		sleep 0.1
	done
	curl -s -o /dev/null -H "Referer: https://exemple/candidatures?candidature=42" \
		"http://localhost:$port/api/interviews/123?x=1&code=731205"
	sleep 0.5
	kill "$pid"
	wait "$pid" 2>/dev/null || true
	pid=""
	ligne=$(grep '/api/interviews' "$tmp/$journal" | tail -n 1)
	case "$ligne" in
	*'"path":"/api/interviews/:id"'*) ;;
	*) echo "ÉCHEC $nom : chemin non masqué : $ligne"; exit 1 ;;
	esac
	for interdit in 123 'x=1' 731205 candidature '"uri"' Referer; do
		case "$ligne" in
		*"$interdit"*) echo "ÉCHEC $nom : « $interdit » dans le journal : $ligne"; exit 1 ;;
		esac
	done
	echo "OK $nom : /api/interviews/123?x=1 journalisé comme /api/interviews/:id"
}

# Plateforme : APP_DOMAIN sur 8931, la démo du même fichier à côté (8941).
essai prod deploy/prod/Caddyfile access-app.log 8931 8941
# Démo en ligne : DEMO_DOMAIN seul ; APP_DOMAIN n'y sert pas.
essai démo deploy/demo/Caddyfile access.log 8932 8932
