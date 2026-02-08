#!/usr/bin/env bash
# preflight_py_env.sh
# Usage examples:
#   ./preflight_py_env.sh -r requirements.txt -v ~/venvs/Gensurv_venv --check-only
#   ./preflight_py_env.sh -r requirements.txt -v ~/venvs/Gensurv_venv --install-missing
#   ./preflight_py_env.sh -r requirements.txt -v ~/venvs/Gensurv_venv --install-all

set -euo pipefail

REQ="requirements.txt"
VENV=".venv"
MODE="check"   # check | install-missing | install-all

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

# Expand leading ~ if present (in case user passed it quoted)
[[ "$VENV" == "~/"* ]] && VENV="${HOME}/${VENV#~/}"

require() { command -v "$1" >/dev/null || { echo "Missing command: $1"; exit 1; }; }

APT=0; command -v apt-get >/dev/null && APT=1
OS_PKGS=(build-essential pkg-config libffi-dev libssl-dev libicu-dev
         libdbus-1-dev libgirepository1.0-dev libcairo2-dev libsystemd-dev
         libpq-dev python3-venv python3-dev)

check_apt() {
  [[ $APT -eq 1 ]] || { echo "[apt] not found; skipping OS package checks."; return; }
  local missing=()
  for p in "${OS_PKGS[@]}"; do
    dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" || missing+=("$p")
  done
  if ((${#missing[@]})); then
    echo "[apt] Missing: ${missing[*]}"
    if [[ "$MODE" != "check" ]]; then
      sudo apt-get update
      sudo apt-get install -y --no-install-recommends "${missing[@]}"
    fi
  else
    echo "[apt] All OS packages present."
  fi
}

filter_requirements() {
  local in="$1" out="$2"
  # Drop OS-managed / non-pip lines (incl. certbot bits)
  grep -Ev '^(python-apt|ubuntu-pro-client|ufw|unattended-upgrades|language-selector|command-not-found|distro-info|dbus-python|PyGObject|systemd-python|iotop|sos|wadllib|python-debian|certbot|certbot-nginx|acme|josepy)\b' \
    "$in" > "$out"
}

setup_venv() {
  if [[ ! -d "$VENV" ]]; then
    echo "[venv] creating: $VENV"
    python3 -m venv "$VENV"
  fi
  PY="$VENV/bin/python"
  PIP="$PY -m pip"
  # Upgrade tooling in that venv
  $PIP install -U pip wheel setuptools >/dev/null
  echo "[venv] python: $($PY -c 'import sys; print(sys.executable)')"
  echo "[venv] pip:    $($PY -c 'import sys,site; import pip; print(pip.__version__)')"
  # Export for other functions
  export PY PIP
}

check_pip() {
  local reqfile="$1"
  $PY - "$reqfile" <<'PYCODE'
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
PYCODE
}

install_missing() {
  local miss="$1" oo="$2"
  if [[ -n "$miss$oo" ]]; then
    echo "[pip] Installing: $miss $oo"
    # shellcheck disable=SC2086
    $PIP install $miss $oo
  else
    echo "[pip] Nothing to install."
  fi
}

main() {
  require python3; require grep
  echo "[info] Python: $(python3 --version)"
  check_apt

  # create temp req and clean it safely on exit
  tmpreq="$(mktemp)"
  trap 'rm -f "${tmpreq:-}"' EXIT

  filter_requirements "$REQ" "$tmpreq"
  echo "[pip] Filtered requirements -> $tmpreq"

  setup_venv

  local out; out="$(check_pip "$tmpreq")"
  echo "$out" | sed -n '1,200p'
  local MISSING_LIST OUTOFSPEC_LIST
  MISSING_LIST=$(printf '%s\n' "$out" | awk '/^MISSING_LIST=/{sub(/^MISSING_LIST=/,""); print}')
  OUTOFSPEC_LIST=$(printf '%s\n' "$out" | awk '/^OUTOFSPEC_LIST=/{sub(/^OUTOFSPEC_LIST=/,""); print}')

  case "$MODE" in
    check)            echo "[mode] check-only; not installing.";;
    install-missing)  install_missing "$MISSING_LIST" "$OUTOFSPEC_LIST";;
    install-all)      $PIP install -r "$tmpreq";;
  esac

  echo "[done]"
}
main

