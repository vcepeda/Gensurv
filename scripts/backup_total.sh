#!/bin/bash

# ============================================================
# FULL BACKUP BEFORE DEPLOY
# Saves: full project folder, PostgreSQL DB, mamba env,
#        nginx config, gunicorn service, and Django migration state
#
# OUTPUT STRUCTURE:
#   /mnt/storage/ahcepev1/backups/legacy/Gensurv-DATE/
#   ├── Gensurv/                  full project copy
#   ├── gensurv.yml               mamba env (exact, for rollback)
#   ├── gensurv-nobuilds.yml      mamba env (portable, for new servers)
#   ├── db.dump                   postgresql backup
#   ├── nginx.conf                nginx config
#   ├── gunicorn_gensurv.service  gunicorn service file
#   ├── migrations.txt            django migration state
#   ├── backup_info.txt           metadata (date, user, git commit)
#   └── backup.log                full stdout log of this script
#
# USAGE:
#   1. Give execute permissions (only needed once):
#        chmod +x backup_total.sh
#   2. Run the script (from the same folder):
#        ./backup_total.sh
#   Or run from anywhere using the full path:
#        /home/youruser/backup_total.sh
#
# DRY RUN (test paths before running the full script):
#   echo $(basename "/mnt/web_data/html/Gensurv")  # should print: Gensurv
#   ls /mnt/storage/ahcepev1/backups/legacy         # should show backup folder
# ============================================================

# Timestamp to identify this backup
DATE=$(date +%Y%m%d_%H%M%S)

# --- Paths --- adjust these to your server
REPO_DIR="/mnt/web_data/html/Gensurv"
REPO_NAME=$(basename "$REPO_DIR")
CONFIG_FILE="/mnt/web_data/html/Gensurv/gensurv_project/settings.py"
NGINX_CONF="/etc/nginx/sites-enabled/reverse-proxy.conf"
# NGINX_CONF="/etc/nginx/sites-available/reverse-proxy.conf"  # same file, sites-enabled is a symlink to sites-available
GUNICORN_SERVICE="/etc/systemd/system/gunicorn_gensurv.service"
BACKUP_ROOT="/mnt/storage/ahcepev1/backups/legacy"

# --- This backup's folder — all files go here
BACKUP_DIR="$BACKUP_ROOT/${REPO_NAME}-${DATE}"

# --- PostgreSQL credentials ---
DB_NAME="gensurv_db"
DB_USER="gensurv_user"

# --- Mamba env name ---
MAMBA_ENV="gensurv"

# --- Absolute path to python inside the mamba env ---
# Most reliable way to run Django commands inside a script
PYTHON_ENV="/home/$USER/.local/share/mamba/envs/$MAMBA_ENV/bin/python"

# ============================================================
# Create this backup's folder
mkdir -p "$BACKUP_DIR"

# All stdout and stderr from this point on goes to both terminal AND backup.log
# tee -a: appends to log file while still printing to terminal
exec > >(tee -a "$BACKUP_DIR/backup.log") 2>&1

echo "============================================================"
echo "Starting full backup — $DATE"
echo "  Backup folder: $BACKUP_DIR"
echo "============================================================"

# ------------------------------------------------------------
# BACKUP INFO FILE
# Metadata about this backup — useful for quick reference
# without having to open any of the actual backup files
# ------------------------------------------------------------
echo "Backup date:  $DATE"                                                    > "$BACKUP_DIR/backup_info.txt"
echo "User:         $USER"                                                   >> "$BACKUP_DIR/backup_info.txt"
echo "Hostname:     $(hostname)"                                             >> "$BACKUP_DIR/backup_info.txt"
echo "Repo dir:     $REPO_DIR"                                               >> "$BACKUP_DIR/backup_info.txt"
echo "Git branch:   $(git -C $REPO_DIR branch --show-current 2>/dev/null)"  >> "$BACKUP_DIR/backup_info.txt"
echo "Git commit:   $(git -C $REPO_DIR rev-parse --short HEAD 2>/dev/null)" >> "$BACKUP_DIR/backup_info.txt"
echo "Rollback cmd: ./rollback.sh $DATE"                                     >> "$BACKUP_DIR/backup_info.txt"

# ------------------------------------------------------------
# 1. FULL PROJECT FOLDER COPY
# Includes .env, media, logs, and everything not tracked by git
# ------------------------------------------------------------
echo ""
echo "[1/6] Copying full project folder..."
cp -r "$REPO_DIR" "$BACKUP_DIR/$REPO_NAME"
echo "  Saved to: $BACKUP_DIR/$REPO_NAME"

# ------------------------------------------------------------
# 2. EXPORT MAMBA ENVIRONMENT
# Saves all dependencies including gunicorn
# Two versions: exact (for rollback) and portable (for new servers)
# ------------------------------------------------------------
echo ""
echo "[2/6] Exporting mamba environment..."

# Exact version — best for rollback on the same machine
mamba env export -n "$MAMBA_ENV" > "$BACKUP_DIR/gensurv.yml"

# Portable version — better for recreating on a different OS
mamba env export -n "$MAMBA_ENV" --no-builds > "$BACKUP_DIR/gensurv-nobuilds.yml"
echo "  Saved to: $BACKUP_DIR/gensurv.yml"

# ------------------------------------------------------------
# 3. POSTGRESQL BACKUP
# -F c: compressed format
# -b: include large objects
# -v: verbose output
# ------------------------------------------------------------
echo ""
echo "[3/6] Dumping PostgreSQL database..."
pg_dump -U "$DB_USER" -h localhost -d "$DB_NAME" -F c -b -v -f "$BACKUP_DIR/db.dump"
echo "  Saved to: $BACKUP_DIR/db.dump"

# ------------------------------------------------------------
# 4. NGINX CONFIG BACKUP
# Shared with another website — always back up before any changes
# ------------------------------------------------------------
echo ""
echo "[4/6] Copying nginx config..."
sudo cp "$NGINX_CONF" "$BACKUP_DIR/nginx.conf"
echo "  Saved to: $BACKUP_DIR/nginx.conf"

# ------------------------------------------------------------
# 5. GUNICORN SERVICE FILE BACKUP
# Shared infrastructure — always back up before any changes
# Contains hardcoded paths (WorkingDirectory, ExecStart) that
# need to be updated if the project folder changes
# ------------------------------------------------------------
echo ""
echo "[5/6] Copying gunicorn service file..."
sudo cp "$GUNICORN_SERVICE" "$BACKUP_DIR/gunicorn_gensurv.service"
echo "  Saved to: $BACKUP_DIR/gunicorn_gensurv.service"

# ------------------------------------------------------------
# 6. DJANGO MIGRATION STATE
# Saved as a human-readable reference — useful to know which
# migration each app was on without having to restore the full dump.
# Note: the pg_dump already contains the real migration state,
# this is just a quick reference file.
# ------------------------------------------------------------
echo ""
echo "[6/6] Saving Django migration state..."
cd "$REPO_DIR"

# --- OPTION 0: assumes the env is already activated ---
# Not recommended: will fail if script is run from a different shell context
# python manage.py showmigrations > "$BACKUP_DIR/migrations.txt"

# --- OPTION 1: mamba run ---
# Runs the command inside the env without activating it
# Usually works but can have issues depending on mamba version
# mamba run -n "$MAMBA_ENV" python manage.py showmigrations > "$BACKUP_DIR/migrations.txt"

# --- OPTION 2: absolute path to python inside the env --- (ACTIVE - most reliable)
# Bypasses shell activation entirely — always works inside bash scripts
$PYTHON_ENV manage.py showmigrations > "$BACKUP_DIR/migrations.txt"

# --- OPTION 3: mamba activate (DOES NOT WORK IN SCRIPTS) ---
# 'mamba activate' cannot modify the parent shell from inside a script.
# Requires shell initialization first with:
#   eval "$(mamba shell hook --shell bash)"
# or permanently with:
#   mamba shell init --shell bash --root-prefix=~/.local/share/mamba
# Left here for reference only — do not use in scripts.
# eval "$(mamba shell hook --shell bash)"
# mamba activate "$MAMBA_ENV"
# python manage.py showmigrations > "$BACKUP_DIR/migrations.txt"
# mamba deactivate

echo "  Saved to: $BACKUP_DIR/migrations.txt"

# ============================================================
echo ""
echo "============================================================"
echo "BACKUP COMPLETE — $DATE"
echo ""
echo "  $BACKUP_DIR/"
echo "  ├── $REPO_NAME/               full project copy"
echo "  ├── gensurv.yml               mamba env (exact)"
echo "  ├── gensurv-nobuilds.yml      mamba env (portable)"
echo "  ├── db.dump                   postgresql backup"
echo "  ├── nginx.conf                nginx config"
echo "  ├── gunicorn_gensurv.service  gunicorn service"
echo "  ├── migrations.txt            django migration state"
echo "  ├── backup_info.txt           metadata"
echo "  └── backup.log                this log"
echo ""
echo "To rollback if something goes wrong, run:"
echo "  ./rollback.sh $DATE"
echo "============================================================"