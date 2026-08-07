#!/usr/bin/env bash
#
# setup.sh — installa QGIS headless in WSL2/Linux via micromamba.
#
# Idempotente: se micromamba o l'ambiente 'qgis' esistono gia', non li
# reinstalla. Non modifica file di sistema; tutto resta nella home utente.
#
# Uso:
#   bash setup.sh                  # installa micromamba (se manca) + ambiente 'qgis'
#                                  # (versione QGIS pinnata in environment.yml)
#   bash setup.sh --init           # come sopra, e aggiunge l'init a ~/.bashrc
#   bash setup.sh --version 3.40.* # ignora environment.yml e installa questa versione
#
set -euo pipefail

ENV_NAME="qgis"
MAMBA_BIN="$HOME/.local/bin/micromamba"
ENV_FILE="$(cd "$(dirname "$0")" && pwd)/environment.yml"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$HOME/micromamba}"
DO_INIT=0
QGIS_VERSION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --init)    DO_INIT=1 ;;
    --version) QGIS_VERSION="${2:?--version richiede un valore, es. 3.40.*}"; shift ;;
    *) echo "Opzione sconosciuta: $1" >&2; exit 2 ;;
  esac
  shift
done

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# 1. micromamba ------------------------------------------------------------
if command -v micromamba >/dev/null 2>&1; then
  MAMBA="$(command -v micromamba)"
  say "micromamba gia' presente: $MAMBA"
elif [[ -x "$MAMBA_BIN" ]]; then
  MAMBA="$MAMBA_BIN"
  say "micromamba gia' presente: $MAMBA"
else
  say "Installo micromamba in ~/.local/bin ..."
  mkdir -p "$HOME/.local/bin"
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xj -C /tmp bin/micromamba
  cp /tmp/bin/micromamba "$MAMBA_BIN"
  chmod +x "$MAMBA_BIN"
  MAMBA="$MAMBA_BIN"
fi
"$MAMBA" --version

# 2. ambiente qgis ---------------------------------------------------------
if "$MAMBA" env list 2>/dev/null | grep -qE "/envs/${ENV_NAME}\b|[[:space:]]${ENV_NAME}[[:space:]]"; then
  say "Ambiente '${ENV_NAME}' gia' esistente: nessuna installazione."
else
  say "Creo l'ambiente '${ENV_NAME}' da conda-forge (qualche minuto, ~3-5 GB) ..."
  if [[ -n "$QGIS_VERSION" ]]; then
    "$MAMBA" create -n "$ENV_NAME" -c conda-forge "qgis=${QGIS_VERSION}" -y
  elif [[ -f "$ENV_FILE" ]]; then
    say "Uso environment.yml (versione QGIS pinnata) ..."
    "$MAMBA" create -f "$ENV_FILE" -y
  else
    "$MAMBA" create -n "$ENV_NAME" -c conda-forge qgis -y
  fi
  say "Pulisco la cache dei pacchetti ..."
  "$MAMBA" clean -a -y
fi

# 3. init shell (opzionale) ------------------------------------------------
if [[ "$DO_INIT" -eq 1 ]]; then
  say "Aggiungo l'init di micromamba a ~/.bashrc ..."
  "$MAMBA" shell init -s bash -r "$MAMBA_ROOT_PREFIX"
  echo "   Riapri il terminale (o 'source ~/.bashrc'), poi: micromamba activate ${ENV_NAME}"
fi

# 4. verifica --------------------------------------------------------------
say "Verifica:"
QT_QPA_PLATFORM=offscreen "$MAMBA" run -n "$ENV_NAME" \
  python -c "import qgis.core as q; print('QGIS', q.Qgis.QGIS_VERSION)"

say "Fatto. Esempi d'uso:"
cat <<EOF
  export QT_QPA_PLATFORM=offscreen
  $MAMBA run -n ${ENV_NAME} qgis_process --version
  $MAMBA run -n ${ENV_NAME} qgis_process list
  $MAMBA run -n ${ENV_NAME} python tuo_script.py
EOF
