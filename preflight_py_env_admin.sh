#!/usr/bin/env bash
# Preflight for Python env + optional Postgres (Ubuntu/Debian).
# Modes:
#   --check-only        : only check, don't install
#   --install-missing   : install only what's missing
#   --install-all       : pip install all filtered requirements
# Postgres:
#   --pg server|client|none   (default: none)
#   --db-name NAME --db-user USER --db-pass PASS   (optional; for --pg server)

set -euo pipefail

REQ="requirements.txt"
VENV=".venv"
MODE="check"          # check | install-missing | install-all
PG_MODE="none"        # none | client | server
DB_NAME=""
DB_USER=""
DB_PASS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--requirements) REQ="$2"; shift 2;;
    -v|--venv)         VENV="$2"; shift 2;;
    --check-only)      MODE="check"; shift;;
    --install-missing) MODE="install-missing"; shift;;
    --install-all)     MODE="install-all"; shift;;
    --pg)              PG_MODE="$2"; shift 2;;
    --db-name)         DB_NAME="$2"; shift 2;;
    --db-user)         DB_USER="$2"; shift 2;;
    --db-pass)         DB_PASS="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

require() { command -v "$1" >/dev/null || { echo "Missing command: $1"; exit 1; }; }

APT=0; command -v apt-get >/dev/null && APT=1
OS_PKGS=(build-essential pkg-config libffi-dev libssl-dev libicu-dev libdbus-1-dev libgirepository1.0-dev libcairo2-dev libsystemd-dev libpq-dev)

add_pg_pkgs() {
  case "$PG_MODE" in
    client) OS_PKGS+=("postgresql-client" "libpq5");;
    server) OS_PKGS+=("postgresql" "postgresql-contrib" "postgresql-client" "libpq5");;
    none|*) ;;
  esac
}

check_apt() {
  [[ $APT -eq 1 ]] || { echo "[apt] not found; skipping OS package checks."; return; }
  add_pg_pkgs
  local missing=()
  for p in "${OS_PKGS[@]}"; do
    dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" || missing+=("$p")
  done
  if ((${#missing[@]})); then
    echo "[apt] Missing: ${missing[*]}"
    if [[ "$MODE" != "check" ]]; then
      echo "[apt] Installing missing OS packages with sudo..."
      sudo apt-get update
      sudo apt-get install -y --no-install-recommends "${missing[@]}"
    fi
  else
    echo "[apt] All OS packages present."
  fi
}

start_postgres_if_needed() {
  [[ "$PG_MODE" == "server" ]] || return 0
  if [[ "$MODE" != "check" ]]; then
    if command -v systemctl >/dev/null; then
      sudo systemctl enable --now postgresql || true
    fi
  fi
  if command -v pg_isready >/dev/null; then
    pg_isready || true
  fi
}

create_db_user_if_requested() {
  [[ "$PG_MODE" == "server" ]] || return 0
  [[ -n "$DB_NAME" && -n "$DB_USER" && -n "$DB_PASS" ]] || { 
    echo "[pg] DB creation skipped (set --db-name/--db-user/--db-pass to create)."; return 0; 
  }
  [[ "$MODE" == "check" ]] && { echo "[pg] Would create DB/user (check-only mode)."; return 0; }
  echo "[pg] Creating role '$DB_USER' and database '$DB_NAME' if they don't exist..."
  sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}') THEN
    CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
  END IF;
END
\$\$;
SQL
  echo "[pg] Done. Example URL: postgresql://${DB_USER}:********@localhost:5432/${DB_NAME}"
}

filter_requirements() {
  local in="$1" out="$2"
  # Remove OS-managed / non-pip lines
  grep -Ev '^(python-apt|ubuntu-pro-client|ufw|unattended-upgrades|language-selector|command-not-found|distro-info|dbus-python|PyGObject|systemd-python|iotop|sos|wadllib|python-debian|certbot|certbot-nginx)\b' \
    "$in" > "$out"
}

setup_venv() {
  if [[ ! -d "$VENV" ]]; then
    python3 -m venv "$VENV"
  fi
  # shellcheck disable=SC1090
  source "$VENV/bin/activate"
  python -m pip install -U pip wheel setuptools >/dev/null
}

check_pip() {
  local reqfile="$1"
  python - "$reqfile" <<'PY'
import sys, re
from importlib.metadata import version, PackageNotFoundError
req_path = sys.argv[1]
missing=[]; outof=[]
pat = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*(==\s*([^\s#]+))?\s*(#.*)?$')
with open(req_path) as f:
  for line in f:
    s=line.strip()
    if not s or s.startswith('#'): continue
    m=pat.match(s)
    if not m:
      print(f"[pip] WARN: skip '{s}'"); 
      continue
    name, _, ver = m.group(1), m.group(2), m.group(3)
    try:
      cur = version(name)
    except PackageNotFoundError:
      missing.append((name, ver))
      continue
    if ver and cur != ver:
      outof.append((name, ver, cur))
print("=== Python packages status ===")
print("Missing:", ", ".join(f"{n}=={v}" if v else n for n,v in missing) or "none")
print("Out-of-spec:", ", ".join(f"{n}=={v} (have {c})" for n,v,c in outof) or "none")
print("MISSING_LIST=" + " ".join(f"{n}=={v}" if v else n for n,v in missing))
print("OUTOFSPEC_LIST=" + " ".join(f"{n}=={v}" for n,v,c in outof))
PY
}

install_missing() {
  local miss="$1" oo="$2"
  if [[ -n "$miss$oo" ]]; then
    echo "[pip] Installing: $miss $oo"
    pip install $miss $oo
  else
    echo "[pip] Nothing to install."
  fi
}

main() {
  require python3; require grep
  echo "[info] Python: $(python3 --version)"
  check_apt
  start_postgres_if_needed

  local tmpreq; tmpreq="$(mktemp)"
  filter_requirements "$REQ" "$tmpreq"
  echo "[pip] Filtered requirements -> $tmpreq"

  setup_venv
  local out; out="$(check_pip "$tmpreq")"
  echo "$out" | sed -n '1,200p'
  local MISSING_LIST OUTOFSPEC_LIST
  MISSING_LIST=$(echo "$out" | awk -F= '/^MISSING_LIST=/{print $2}')
  OUTOFSPEC_LIST=$(echo "$out" | awk -F= '/^OUTOFSPEC_LIST=/{print $2}')

  case "$MODE" in
    check)            echo "[mode] check-only; not installing pip packages.";;
    install-missing)  install_missing "$MISSING_LIST" "$OUTOFSPEC_LIST";;
    install-all)      pip install -r "$tmpreq";;
  esac

  create_db_user_if_requested
  rm -f "$tmpreq"
  echo "[done]"
}
main

