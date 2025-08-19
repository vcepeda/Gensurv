# script to give you full control and everyone else read-only on a repo directory.
```bash
#!/usr/bin/env bash
# secure_repo.sh — make repo owned by you; u=rwX,go=rX everywhere

set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 /path/to/reponame" >&2
  exit 1
fi

# Create the directory if it doesn't exist
mkdir -p "$TARGET"

# 1) Make sure YOU own it (owner: your user, group: your primary group)
sudo chown -R "$USER":"$(id -gn)" "$TARGET"

# 2) Permissions: you=rwX; group/others= rX  (dirs stay traversable; files non-exec unless already exec)
chmod -R u=rwX,go=rX "$TARGET"

# 3) Helpful: ensure parent is at least traversable so others can read inside (optional)
# chmod o+x "$(dirname "$TARGET")"

echo "Done."
ls -ld "$TARGET"
```
Usage:
```bash
chmod +x secure_repo.sh
./secure_repo.sh /path/to/reponame
```
