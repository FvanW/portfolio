#!/bin/bash
# Auto-resolve git sync with pull-before-push and retry logic
# Designed for cron jobs where multiple devices push to the same repo

set -euo pipefail

REPO_DIR="/home/apache/obsidian-vault"
REMOTE="origin"
BRANCH="main"
LOG_FILE="/tmp/vault-sync.log"

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

cd "$REPO_DIR" || exit 1

# Stage all changes
git add -A

# Commit if there are changes
if ! git diff --cached --quiet; then
    git commit -m "Auto-sync: $(date -Iminutes)"
    log "Committed local changes"
else
    log "No local changes to commit"
fi

# Pull remote changes with auto-merge
if git pull --no-rebase "$REMOTE" "$BRANCH"; then
    log "Pulled remote changes successfully"
else
    log "ERROR: git pull failed"
    exit 1
fi

# Push to remote
if git push "$REMOTE" "$BRANCH"; then
    log "Push successful"
else
    log "Push failed, retrying..."
    sleep 5
    if git pull --no-rebase "$REMOTE" "$BRANCH" && git push "$REMOTE" "$BRANCH"; then
        log "Retry successful"
    else
        log "ERROR: Push failed after retry"
        exit 1
    fi
fi

log "Sync complete"
