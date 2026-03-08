#!/bin/bash

# ============================================================
# ROLLBACK — restores the site to a previous backup state
# Restores: project folder (via nginx/gunicorn switch),
#           PostgreSQL DB, and optionally the mamba env
#
# USAGE:
#   1. Give execute permissions (only needed once):
#        chmod +x rollback.sh
#   2. Run with the DATE from the backup you want to restore:
#        ./rollback.sh 20240315_143022
#   The DATE is printed at the end of backup_total.sh output.
#
# DRY RUN (check available backups before running):
#   ls /mnt/storage/ahcepev1/backups/legacy
# ============================================================

DATE=$1   # backup date passed as argument, e.g: 20240315_143022

# --- Paths --- must match backup_total.sh
REPO_DIR="/mnt/web_data/html/Gensurv"
REPO_NAME=$(basename "$REPO_DIR")
BACKUP_ROOT="/mnt/storage/ahcepev1/backups/legacy"
NGINX_CONF="/etc/nginx/sites-enabled/reverse-proxy.conf"
# NGINX_CONF="/etc/nginx/sites-available/reverse-proxy.conf"  # same file, sites-enabled is a symlink to sites-available
GUNICORN_SERVICE="/etc/systemd/system/gunicorn_gensurv.service"

# --- This backup's folder ---
BACKUP_DIR="$BACKUP_ROOT/${REPO_NAME}-${DATE}"

# --- PostgreSQL credentials ---
DB_NAME="gensurv_db"
DB_USER="gensurv_user"

# --- Mamba env name ---
MAMBA_ENV="gensurv"

# ============================================================

# Check that a DATE argument was provided
if [ -z "$DATE" ]; then
  echo "ERROR: no backup date provided"
  echo "Usage: ./rollback.sh 20240315_143022"
  echo ""
  echo "Available backups:"
  ls "$BACKUP_ROOT" | grep "${REPO_NAME}-" | sed "s/${REPO_NAME}-//"
  exit 1
fi

# Check that the backup folder actually exists
if [ ! -d "$BACKUP_DIR" ]; then
  echo "ERROR: backup not found: $BACKUP_DIR"
  echo ""
  echo "Available backups:"
  ls "$BACKUP_ROOT" | grep "${REPO_NAME}-" | sed "s/${REPO_NAME}-//"
  exit 1
fi

# Show backup metadata so user knows what they're restoring
echo "============================================================"
echo "ROLLBACK to backup: $DATE"
echo ""
echo "Backup info:"
cat "$BACKUP_DIR/backup_info.txt"
echo "============================================================"
echo ""
echo "WARNING: this will overwrite the current site and database."
echo "Are you sure? (y/n)"
read CONFIRM
[ "$CONFIRM" != "y" ] && echo "Cancelled." && exit 0

# All stdout and stderr from this point on goes to both terminal AND rollback log
# Log filename includes timestamp in case rollback is run multiple times on the same backup
ROLLBACK_LOG="$BACKUP_DIR/rollback-$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$ROLLBACK_LOG") 2>&1

echo ""
echo "Rollback started — $(date +%Y%m%d_%H%M%S)"

# ------------------------------------------------------------
# 1. SWITCH NGINX TO LEGACY FOLDER
# Instead of reverting git, we just point nginx to the backup folder.
# This is instant and leaves the current repo untouched.
#
# IMPORTANT: nginx config is shared with another website, so we
# back it up before modifying it in case we need to restore manually.
#
# NOTE: sites-enabled is a symlink to sites-available, so editing
# through sites-enabled automatically updates sites-available too.
# No need to edit both files.
# ------------------------------------------------------------
echo ""
echo "[1/4] Switching nginx to legacy folder..."

# Backup current nginx config before modifying it
# shared with another site so we never modify without saving first
NGINX_BACKUP="$BACKUP_DIR/nginx-pre-rollback-$(date +%Y%m%d_%H%M%S).conf"
sudo cp "$NGINX_CONF" "$NGINX_BACKUP"
echo "  Current nginx config backed up to: $NGINX_BACKUP"

# Switch nginx to point to the legacy folder
sudo sed -i "s|$REPO_DIR|$BACKUP_DIR/$REPO_NAME|g" "$NGINX_CONF"
sudo systemctl reload nginx
echo "  Nginx now pointing to: $BACKUP_DIR/$REPO_NAME"

# ------------------------------------------------------------
# 2. RESTORE POSTGRESQL DATABASE (optional)
# Drops the current DB and restores from the pg_dump backup.
# WARNING: all data added after the backup date will be lost.
#
# Skip this if you want to keep current user data and just
# revert the code — Django migrations will handle schema changes.
# Only restore if the DB itself is corrupted or you need a full reset.
# ------------------------------------------------------------
echo ""
echo "[2/4] Restore PostgreSQL database? (y/n)"
echo "      WARNING: restoring will DELETE all current data"
echo "      Skip (n) to keep current data and only revert the code"
read RESTORE_DB

if [ "$RESTORE_DB" = "y" ]; then
  echo ""
  echo "  Are you absolutely sure? This will delete ALL current data. (yes/no)"
  read RESTORE_DB_CONFIRM

  if [ "$RESTORE_DB_CONFIRM" = "yes" ]; then
    # Close all active connections to the DB so we can drop it
    psql -U "$DB_USER" -h localhost -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME' AND pid <> pg_backend_pid();"

    dropdb -U "$DB_USER" -h localhost "$DB_NAME"                                # drop current DB
    createdb -U "$DB_USER" -h localhost "$DB_NAME"                              # create empty DB
    pg_restore -U "$DB_USER" -h localhost -d "$DB_NAME" "$BACKUP_DIR/db.dump"  # restore backup
    echo "  Database restored from: $BACKUP_DIR/db.dump"
  else
    echo "  Database restore cancelled — current data kept"
  fi

else
  echo "  Skipped database restore — current data kept"
  echo "  Note: if the legacy code expects a different schema, run:"
  echo "  $PYTHON_ENV $BACKUP_DIR/$REPO_NAME/manage.py migrate"
fi

# ------------------------------------------------------------
# 3. RESTORE MAMBA ENVIRONMENT (optional)
# Only needed if the new branch changed dependencies and caused issues.
# Creates a versioned env (gensurv-v1, v2, etc.) based on existing
# envs on the system. User can also delete an existing one to reuse
# its slot instead of creating a new version number.
# The original 'gensurv' env is never touched.
# ------------------------------------------------------------
echo ""
echo "[3/4] Restore mamba environment? (y/n)"
echo "      (only needed if dependency changes caused issues)"
read RESTORE_ENV

if [ "$RESTORE_ENV" = "y" ]; then

  # Find all existing versioned rollback envs (gensurv-v1, gensurv-v2, etc.)
  EXISTING=$(mamba env list | grep "${MAMBA_ENV}-v" | awk '{print $1}' | sort)

  # Find the next available version number
  LAST_VERSION=$(echo "$EXISTING" | grep -oP 'v\K[0-9]+' | sort -n | tail -1)
  NEXT_VERSION=$((${LAST_VERSION:-0} + 1))
  ROLLBACK_ENV="${MAMBA_ENV}-v${NEXT_VERSION}"

  # Show user what already exists
  echo ""
  echo "  Existing rollback envs:"
  if [ -z "$EXISTING" ]; then
    echo "    none"
  else
    echo "$EXISTING" | while read e; do echo "    $e"; done
  fi
  echo ""
  echo "  New env will be created as: $ROLLBACK_ENV"
  echo ""
  echo "  Options:"
  echo "    1) Continue — create $ROLLBACK_ENV"
  echo "    2) Delete an existing env and reuse its name"
  echo "    3) Skip env restore"
  read ENV_OPTION

  if [ "$ENV_OPTION" = "1" ]; then
    # Create new versioned env — does not touch the current gensurv env
    mamba env create -n "$ROLLBACK_ENV" -f "$BACKUP_DIR/gensurv.yml"
    echo "  Rollback env created: $ROLLBACK_ENV"

  elif [ "$ENV_OPTION" = "2" ]; then
    echo ""
    echo "  Which env do you want to delete? (type full name, e.g. ${MAMBA_ENV}-v1)"
    echo "  Existing: $EXISTING"
    read ENV_TO_DELETE

    # Confirm deletion
    echo "  Are you sure you want to delete '$ENV_TO_DELETE'? (y/n)"
    read CONFIRM_DELETE

    if [ "$CONFIRM_DELETE" = "y" ]; then
      mamba env remove -n "$ENV_TO_DELETE"
      echo "  Deleted: $ENV_TO_DELETE"

      # Reuse the deleted env's name for the new one
      ROLLBACK_ENV="$ENV_TO_DELETE"
      mamba env create -n "$ROLLBACK_ENV" -f "$BACKUP_DIR/gensurv.yml"
      echo "  Rollback env created: $ROLLBACK_ENV"
    else
      echo "  Deletion cancelled — creating $ROLLBACK_ENV instead"
      mamba env create -n "$ROLLBACK_ENV" -f "$BACKUP_DIR/gensurv.yml"
      echo "  Rollback env created: $ROLLBACK_ENV"
    fi

  else
    echo "  Skipped mamba env restore"
    ROLLBACK_ENV=""
  fi

  if [ -n "$ROLLBACK_ENV" ]; then
    echo ""
    echo "  The original '$MAMBA_ENV' env was NOT deleted and remains as fallback"
    echo ""
    echo "  To use the rollback env, update gunicorn_gensurv.service ExecStart to:"
    echo "  /home/$USER/.local/share/mamba/envs/$ROLLBACK_ENV/bin/gunicorn"
    echo "  Then run: sudo systemctl daemon-reload && sudo systemctl restart gunicorn_gensurv"
  fi

else
  echo "  Skipped mamba env restore"
fi

# ------------------------------------------------------------
# 4. UPDATE GUNICORN SERVICE AND RESTART
# Backs up the service file, updates WorkingDirectory to point
# to the legacy folder, reloads systemd, and restarts gunicorn
# ------------------------------------------------------------
echo ""
echo "[4/4] Updating and restarting gunicorn..."

# Backup gunicorn service file before modifying it
# shared infrastructure so we never modify without saving first
GUNICORN_BACKUP="$BACKUP_DIR/gunicorn_gensurv-pre-rollback-$(date +%Y%m%d_%H%M%S).service"
sudo cp "$GUNICORN_SERVICE" "$GUNICORN_BACKUP"
echo "  Gunicorn service backed up to: $GUNICORN_BACKUP"

# Update WorkingDirectory to point to the legacy folder
sudo sed -i "s|WorkingDirectory=$REPO_DIR|WorkingDirectory=$BACKUP_DIR/$REPO_NAME|g" "$GUNICORN_SERVICE"

# Reload systemd so it picks up the service file change
sudo systemctl daemon-reload

# Restart gunicorn_gensurv (not the generic gunicorn)
sudo systemctl restart gunicorn_gensurv
echo "  Gunicorn restarted — WorkingDirectory: $BACKUP_DIR/$REPO_NAME"

# ============================================================
echo ""
echo "============================================================"
echo "ROLLBACK COMPLETE — site restored to: $DATE"
echo ""
echo "The site is now running from: $BACKUP_DIR/$REPO_NAME"
echo "The current repo ($REPO_DIR) was NOT modified."
echo ""
echo "When ready to try the new deploy again:"
echo "  1. Fix the issues in $REPO_DIR"
echo "  2. Revert nginx:"
echo "     sudo sed -i \"s|$BACKUP_DIR/$REPO_NAME|$REPO_DIR|g\" $NGINX_CONF"
echo "  3. Revert gunicorn WorkingDirectory:"
echo "     sudo sed -i \"s|WorkingDirectory=$BACKUP_DIR/$REPO_NAME|WorkingDirectory=$REPO_DIR|g\" $GUNICORN_SERVICE"
echo "  4. Reload and restart:"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl reload nginx"
echo "     sudo systemctl restart gunicorn_gensurv"
echo "============================================================"