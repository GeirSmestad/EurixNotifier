#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/srv/eurixnotifier"
APP_USER="ubuntu"
CRON_FILE="/etc/cron.d/eurixnotifier"
LOG_FILE="/srv/eurixnotifier/eurixnotifier.log"

run_as_app_user() {
  if [[ "${APP_USER}" == "root" ]]; then
    "$@"
  else
    sudo -u "${APP_USER}" -H "$@"
  fi
}

echo "==> Ensuring base packages"
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends python3 python3-venv python3-pip sqlite3 ca-certificates
fi

echo "==> Ensuring app directory ${APP_DIR}"
mkdir -p "${APP_DIR}"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "==> Ensuring scripts are executable"
# SCP may not preserve executable bits depending on local filesystem/settings.
chmod +x "${APP_DIR}/bootstrap.sh" "${APP_DIR}/run_job.sh" 2>/dev/null || true
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/bootstrap.sh" "${APP_DIR}/run_job.sh" 2>/dev/null || true

echo "==> Ensuring data directory"
mkdir -p "${APP_DIR}/data"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/data"

echo "==> Ensuring python venv"
if [[ ! -d "${APP_DIR}/.venv" ]]; then
  run_as_app_user python3 -m venv "${APP_DIR}/.venv"
fi

echo "==> Installing dependencies"
run_as_app_user "${APP_DIR}/.venv/bin/pip" install --upgrade pip
run_as_app_user "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "==> Initializing database (no network calls)"
run_as_app_user bash -lc "cd '${APP_DIR}' && '${APP_DIR}/.venv/bin/python' -c \"from eurixnotifier.db import ensure_db; ensure_db('${APP_DIR}/data/eurix-monitor.db')\""

echo "==> Installing cron file ${CRON_FILE}"
# Avoid double-run on Wednesdays: daily entry skips weekday 3 (Wed), and Wed entry forces notify.
cat > "${CRON_FILE}" <<'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Eurix notifier: daily at 11:45, except Wednesday (weekday 3)
45 11 * * * ubuntu test "$(date +\%u)" -ne 3 && cd /srv/eurixnotifier && /srv/eurixnotifier/run_job.sh >> /srv/eurixnotifier/eurixnotifier.log 2>&1

# Eurix notifier: every Wednesday at 11:45 with forced notification
45 11 * * 3 ubuntu cd /srv/eurixnotifier && /srv/eurixnotifier/run_job.sh --force-notify >> /srv/eurixnotifier/eurixnotifier.log 2>&1
EOF

chmod 0644 "${CRON_FILE}"
touch "${LOG_FILE}"
chown "${APP_USER}:${APP_USER}" "${LOG_FILE}"
chmod 0644 "${LOG_FILE}"

echo "==> Done"

