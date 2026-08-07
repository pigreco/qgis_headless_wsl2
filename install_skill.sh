#!/usr/bin/env bash
#
# install_skill.sh — installa (o aggiorna) la skill 'qgis-headless' per
# Claude Code. Installare e aggiornare sono lo stesso gesto: rilancia lo
# script dopo ogni 'git pull'.
#
# Uso:
#   bash install_skill.sh              # copia in ~/.claude/skills/ (utente)
#   bash install_skill.sh --project    # copia in <repo>/.claude/skills/
#                                      # (versionata col progetto, per team)
#   bash install_skill.sh --symlink    # symlink al repo invece della copia:
#                                      # gli aggiornamenti arrivano col pull
#                                      # (ma si rompe se sposti il repo)
#
# I file locali extra nella skill installata (non presenti nel repo) vengono
# preservati.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/skill/qgis-headless"
DEST_ROOT="$HOME/.claude/skills"
MODE="copy"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) DEST_ROOT="$HERE/.claude/skills" ;;
    --symlink) MODE="symlink" ;;
    *) echo "Opzione sconosciuta: $1 (usa --project e/o --symlink)" >&2; exit 2 ;;
  esac
  shift
done

DEST="$DEST_ROOT/qgis-headless"
[[ -d "$SRC" ]] || { echo "Skill non trovata nel repo: $SRC" >&2; exit 1; }

mkdir -p "$DEST_ROOT"

if [[ "$MODE" == "symlink" ]]; then
  if [[ -e "$DEST" && ! -L "$DEST" ]]; then
    echo "ERRORE: $DEST esiste ed e' una copia, non un symlink." >&2
    echo "Rimuovila prima ('rm -r $DEST') se vuoi passare al symlink." >&2
    exit 1
  fi
  ln -sfn "$SRC" "$DEST"
  echo "Symlink creato: $DEST -> $SRC"
else
  if [[ -L "$DEST" ]]; then
    echo "ERRORE: $DEST e' un symlink; l'aggiornamento avviene gia' col pull." >&2
    echo "Rimuovilo prima ('rm $DEST') se vuoi passare alla copia." >&2
    exit 1
  fi
  action="Installata"
  [[ -d "$DEST" ]] && action="Aggiornata"
  # copia sovrascrivendo i file del repo, senza toccare eventuali extra locali
  mkdir -p "$DEST"
  cp -r "$SRC/." "$DEST/"
  echo "$action: $DEST"
  # segnala i file locali non presenti nel repo (preservati)
  extra=$(cd "$DEST" && find . -type f | while read -r f; do
            [[ -f "$SRC/$f" ]] || echo "  $f"
          done)
  if [[ -n "$extra" ]]; then
    echo "File locali preservati (non presenti nel repo):"
    echo "$extra"
  fi
fi

echo "Riavvia Claude Code per (ri)caricare la skill."
