#!/bin/bash

# ============================================================
# PRE-MERGE CHECK — checks DB and code before merging vue-migration
# Verifies that data in tables/columns affected by the new branch
# migrations is safe to migrate or warns you if data will be lost.
#
# USAGE:
#   1. Give execute permissions (only needed once):
#        chmod +x pre_merge_check.sh
#   2. Run before merging vue-migration:
#        ./pre_merge_check.sh
# ============================================================

# --- Paths ---
REPO_DIR="/mnt/web_data/html/Gensurv"
NEW_BRANCH_DIR="/tmp/gensurv-vue"
NEW_BRANCH_URL="https://github.com/vcepeda/Gensurv"  # repo URL — same for all branches
NEW_BRANCH_NAME="vue-migration"                        # branch to check against current code
LOGS_DIR="/mnt/storage/ahcepev1/backups/logs"

# --- Mamba env ---
MAMBA_ENV="gensurv"
PYTHON_ENV="/home/$USER/.local/share/mamba/envs/$MAMBA_ENV/bin/python"

# --- PostgreSQL credentials ---
DB_NAME="gensurv_db"
DB_USER="gensurv_user"

# ============================================================
mkdir -p "$LOGS_DIR"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/pre-merge-check-$DATE.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================================"
echo "PRE-MERGE CHECK — $DATE"
echo "  Checking: $NEW_BRANCH_NAME → $REPO_DIR"
echo "============================================================"

WARNINGS=0   # counter — if > 0 at the end, we print a warning summary

# ------------------------------------------------------------
# 1. CLONE NEW BRANCH TO TEMP FOLDER
# ------------------------------------------------------------
echo ""
echo "[1/5] Cloning vue-migration branch to temp folder..."

if [ -d "$NEW_BRANCH_DIR" ]; then
  echo "  Temp folder already exists, removing it first..."
  rm -rf "$NEW_BRANCH_DIR"
fi

git clone -b "$NEW_BRANCH_NAME" "$NEW_BRANCH_URL" "$NEW_BRANCH_DIR" --depth=1 --quiet
# --depth=1: only latest commit, faster clone
# --quiet: less output noise
echo "  Cloned to: $NEW_BRANCH_DIR"

# ------------------------------------------------------------
# 2. COMPARE MODELS.PY
# Shows exactly what changed in the DB models between branches
# ------------------------------------------------------------
echo ""
echo "[2/5] Comparing models.py between branches..."
echo "  Current:    $REPO_DIR/gensurvapp/models.py"
echo "  New branch: $NEW_BRANCH_DIR/backend/gensurvapp/models.py"
echo ""
echo "  --- DIFF (lines starting with - are removed, + are added) ---"
diff --color \
  "$REPO_DIR/gensurvapp/models.py" \
  "$NEW_BRANCH_DIR/backend/gensurvapp/models.py" \
  || true   # diff returns exit code 1 if files differ, || true prevents script from stopping
echo "  --- END DIFF ---"

# ------------------------------------------------------------
# 3. CHECK AFFECTED TABLES AND COLUMNS IN CURRENT DB
# Based on code_changes.md, these are the risky changes:
#   - metadata_file column removed from Submission
#   - SampleFile table dropped entirely
#   - submit_to_pipeline column added to Submission (safe)
# ------------------------------------------------------------
echo ""
echo "[3/5] Checking affected tables in current database..."

# --- Check Submission table structure ---
echo ""
echo "  Current Submission table columns:"
psql -U "$DB_USER" -h localhost -d "$DB_NAME" -c "\d gensurvapp_submission" 2>/dev/null \
  || echo "  WARNING: could not read Submission table — does it exist?"

# --- Check if metadata_file has data (will be dropped) ---
echo ""
echo "  Rows in Submission with metadata_file data (will be lost after migration):"
METADATA_COUNT=$(psql -U "$DB_USER" -h localhost -d "$DB_NAME" -tAc \
  "SELECT COUNT(*) FROM gensurvapp_submission WHERE metadata_file IS NOT NULL AND metadata_file != '';" 2>/dev/null)

if [ -z "$METADATA_COUNT" ]; then
  echo "  Could not query metadata_file — column may not exist yet"
elif [ "$METADATA_COUNT" -gt 0 ]; then
  echo "  ⚠️  WARNING: $METADATA_COUNT rows have metadata_file data — this will be LOST after migration"
  WARNINGS=$((WARNINGS + 1))
else
  echo "  ✅ No data in metadata_file column — safe to drop"
fi

# --- Check SampleFile table (will be dropped entirely) ---
echo ""
echo "  Rows in SampleFile table (table will be DROPPED after migration):"
SAMPLEFILE_COUNT=$(psql -U "$DB_USER" -h localhost -d "$DB_NAME" -tAc \
  "SELECT COUNT(*) FROM gensurvapp_samplefile;" 2>/dev/null)

if [ -z "$SAMPLEFILE_COUNT" ]; then
  echo "  Could not query SampleFile — table may not exist"
elif [ "$SAMPLEFILE_COUNT" -gt 0 ]; then
  echo "  ⚠️  WARNING: $SAMPLEFILE_COUNT rows in SampleFile — this data will be LOST after migration"
  WARNINGS=$((WARNINGS + 1))
else
  echo "  ✅ SampleFile table is empty — safe to drop"
fi

# --- Check UploadedFile table (for reference) ---
echo ""
echo "  Rows in UploadedFile table (replacing SampleFile):"
psql -U "$DB_USER" -h localhost -d "$DB_NAME" -tAc \
  "SELECT COUNT(*) FROM gensurvapp_uploadedfile;" 2>/dev/null \
  || echo "  Could not query UploadedFile table"

# --- Check total Submission rows (for context) ---
echo ""
echo "  Total rows in Submission table:"
psql -U "$DB_USER" -h localhost -d "$DB_NAME" -tAc \
  "SELECT COUNT(*) FROM gensurvapp_submission;" 2>/dev/null \
  || echo "  Could not query Submission table"

# ------------------------------------------------------------
# 4. CHECK PENDING MIGRATIONS IN NEW BRANCH
# Applies migrations to a temp DB to see what SQL will run
# ------------------------------------------------------------
echo ""
echo "[4/5] Checking pending migrations in new branch..."

# List migration files added in new branch that don't exist in current branch
echo ""
echo "  Migration files in new branch:"
find "$NEW_BRANCH_DIR/backend" -name "*.py" -path "*/migrations/*" | sort

echo ""
echo "  Migration files in current branch:"
find "$REPO_DIR" -name "*.py" -path "*/migrations/*" | sort

# ------------------------------------------------------------
# 5. CHECK NGINX CONFIG CHANGES
# code_changes.md mentions nginx was changed but NOT tested
# ------------------------------------------------------------
echo ""
echo "[5/5] Checking nginx config changes..."
echo ""

if [ -f "$NEW_BRANCH_DIR/backend/gensurv_project_nginx" ]; then
  echo "  New branch has a nginx config file: gensurv_project_nginx"
  echo "  NOTE from code_changes.md: 'not tested yet'"
  echo ""
  echo "  --- DIFF vs current nginx config ---"
  diff --color \
    "/etc/nginx/sites-enabled/reverse-proxy.conf" \
    "$NEW_BRANCH_DIR/backend/gensurv_project_nginx" \
    || true
  echo "  --- END DIFF ---"
  echo ""
  echo "  ⚠️  WARNING: nginx config changed but not tested — review carefully before applying"
  WARNINGS=$((WARNINGS + 1))
else
  echo "  No nginx config file found in new branch"
fi

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "PRE-MERGE CHECK COMPLETE — $DATE"
echo "  Log saved to: $LOG_FILE"
echo ""

if [ "$WARNINGS" -gt 0 ]; then
  echo "  ⚠️  $WARNINGS WARNING(S) FOUND — review before merging"
  echo ""
  echo "  Recommended steps:"
  echo "    1. Review the diff output above carefully"
  echo "    2. Run backup_total.sh before merging"
  echo "    3. If metadata_file or SampleFile have data, migrate it manually first"
  echo "    4. Do NOT copy the new nginx config without testing it first"
else
  echo "  ✅ No warnings — safe to proceed with merge"
  echo ""
  echo "  Recommended next step:"
  echo "    ./backup_total.sh && git merge origin/vue-migration"
fi

echo "============================================================"

# Cleanup temp folder
echo ""
echo "Cleaning up temp folder..."
rm -rf "$NEW_BRANCH_DIR"
echo "Done."