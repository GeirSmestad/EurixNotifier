#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/srv/eurixnotifier"
APP_USER="root"
CRON_FILE="/etc/cron.d/eurixnotifier"
LOG_FILE="/var/log/eurixnotifier.log"

echo "==> Ensuring base packages"
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends python3 python3-venv python3-pip sqlite3 ca-certificates
fi

echo "==> Ensuring app directory ${APP_DIR}"
mkdir -p "${APP_DIR}"

echo "==> Ensuring data directory"
mkdir -p "${APP_DIR}/data"

echo "==> Ensuring python venv"
if [[ ! -d "${APP_DIR}/.venv" ]]; then
  python3 -m venv "${APP_DIR}/.venv"
fi

echo "==> Installing dependencies"
"${APP_DIR}/.venv/bin/pip" install --upgrade pip
"${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "==> Initializing database (no network calls)"
"${APP_DIR}/.venv/bin/python" -c "from eurixnotifier.db import ensure_db; import os; ensure_db(os.environ.get('EURIX_DB_PATH','${APP_DIR}/data/eurix-monitor.db'))"

echo "==> Installing cron file ${CRON_FILE}"
# Avoid double-run on Wednesdays: daily entry skips weekday 3 (Wed), and Wed entry forces notify.
cat > "${CRON_FILE}" <<'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Eurix notifier: daily at 11:45, except Wednesday (weekday 3)
45 11 * * * root test "$(date +\%u)" -ne 3 && cd /srv/eurixnotifier && /srv/eurixnotifier/run_job.sh >> /var/log/eurixnotifier.log 2>&1

# Eurix notifier: every Wednesday at 11:45 with forced notification
45 11 * * 3 root cd /srv/eurixnotifier && /srv/eurixnotifier/run_job.sh --force-notify >> /var/log/eurixnotifier.log 2>&1
EOF

chmod 0644 "${CRON_FILE}"
touch "${LOG_FILE}"
chmod 0644 "${LOG_FILE}"

echo "==> Done"

