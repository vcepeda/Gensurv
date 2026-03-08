#!/bin/bash

# ============================================================
# RESTART GENSURV SITE
# Pulls latest code, applies migrations, collects static files,
# and restarts gunicorn and nginx
#
# USAGE:
#   1. Give execute permissions (only needed once):
#        chmod +x restart_site.sh
#   2. Run the script:
#        ./restart_site.sh
#
# NOTE: run backup_total.sh before this if deploying a new branch
# ============================================================

# --- Paths ---
REPO_DIR="/mnt/web_data/html/Gensurv"
LOGS_DIR="/mnt/storage/ahcepev1/backups/logs"

# --- Mamba env ---
MAMBA_ENV="gensurv"
PYTHON_ENV="/home/$USER/.local/share/mamba/envs/$MAMBA_ENV/bin/python"

# ============================================================
# Create logs folder if it doesn't exist
mkdir -p "$LOGS_DIR"

# All stdout and stderr goes to both terminal and a timestamped log file
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/restart-$DATE.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "RESTARTING GENSURV — $DATE"
echo "============================================================"

# ------------------------------------------------------------
# 1. GIT PULL
# Downloads latest code from the current branch
# ------------------------------------------------------------
echo ""
echo "[1/5] Pulling latest code from git..."
cd "$REPO_DIR"
git pull
echo "  Git pull complete"
echo "  Branch: $(git branch --show-current)"
echo "  Commit: $(git rev-parse --short HEAD)"

# ------------------------------------------------------------
# 2. RUN MIGRATIONS
# Applies any new database migrations from the pulled code
# ------------------------------------------------------------
echo ""
echo "[2/5] Running database migrations..."
$PYTHON_ENV manage.py migrate
echo "  Migrations complete"

# ------------------------------------------------------------
# 3. COLLECT STATIC FILES
# Copies all static files (CSS, JS, images) to STATIC_ROOT
# --noinput: skips confirmation prompt
# ------------------------------------------------------------
echo ""
echo "[3/5] Collecting static files..."
$PYTHON_ENV manage.py collectstatic --noinput
echo "  Static files collected"

# ------------------------------------------------------------
# 4. RESTART GUNICORN
# Picks up the new code and any changes to the service file
# daemon-reload: needed if the service file itself was changed
# ------------------------------------------------------------
echo ""
echo "[4/5] Restarting gunicorn..."
sudo systemctl daemon-reload
sudo systemctl restart gunicorn_gensurv
echo "  Gunicorn restarted"

# ------------------------------------------------------------
# 5. RELOAD NGINX
# Applies any nginx config changes without dropping connections
# reload is safer than restart — it gracefully applies changes
# ------------------------------------------------------------
echo ""
echo "[5/5] Reloading nginx..."
sudo systemctl reload nginx
echo "  Nginx reloaded"

# ============================================================
echo ""
echo "============================================================"
echo "RESTART COMPLETE — $DATE"
echo "  Branch:  $(git -C $REPO_DIR branch --show-current)"
echo "  Commit:  $(git -C $REPO_DIR rev-parse --short HEAD)"
echo "  Log:     $LOG_FILE"
echo "============================================================"