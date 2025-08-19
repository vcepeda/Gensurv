#!/usr/bin/env bash
# Checks OS deps, filters pip requirements, compares installed versions,
# then (optionally) installs missing/out-of-spec packages.
# keep it outside the web root (safer on servers) with ~/
# Usage:
#   ./preflight_py_env.sh -r requirements.txt -v  ~/venvs/Gensurv_venv --check-only
#   ./preflight_py_env.sh -r requirements.txt -v  ~/venvs/Gensurv_venv --install-missing
#   ./preflight_py_env.sh -r requirements.txt -v  ~/venvs/Gensurv_venv --install-all

set -euo pipefail

REQ="requirements.txt"
VENV="Gensurv_venv"
MODE="check" # check | install-missing | install-all

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--requirements) REQ="$2"; shift 2;;
    -v|--venv)         VENV="$2"; shift 2;;
    --check-only)      MODE="check"; shift;;
    --install-missing) MODE="install-missing"; shift;;
    --install-all)     MODE="install-all"; shift;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

require() { command -v "$1" >/dev/null || { echo "Missing command: $1"; exit 1; }; }

APT=0; command -v apt-get >/dev/null && APT=1
OS_PKGS=(build-essential pkg-config libffi-dev libssl-dev libicu-dev libdbus-1-dev libgirepository1.0-dev libcairo2-dev libsystemd-dev libpq-dev)

check_apt() {
  [[ $APT -eq 1 ]] || { echo "[apt] not found; skipping OS package checks."; return; }
  local missing=()
  for p in "${OS_PKGS[@]}"; do
    dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" || missing+=("$p")
  done
  if ((${#missing[@]})); then
    echo "[apt] Missing: ${missing[*]}"
    if [[ "$MODE" != "check" ]]; then
      echo "[apt] Installing missing OS packages with sudo..."
      sudo apt-get update
      sudo apt-get install -y "${missing[@]}"
    fi
  else
    echo "[apt] All OS packages present."
  fi
}

filter_requirements() {
  local in="$1" out="$2"
  # Remove lines that should be installed via apt/snap (not pip)
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
    check)            echo "[mode] check-only; not installing.";;
    install-missing)  install_missing "$MISSING_LIST" "$OUTOFSPEC_LIST";;
    install-all)      pip install -r "$tmpreq";;
  esac
  rm -f "$tmpreq"
  echo "[done]"
}
main
