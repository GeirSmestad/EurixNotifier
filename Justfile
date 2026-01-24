set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

host := "bergenomap"
remote_dir := "/srv/eurixnotifier"

# Copy files to the server and run bootstrap.sh.
deploy:
  rsync -av --delete \
    --exclude ".git/" \
    --exclude ".venv/" \
    --exclude "data/" \
    --exclude ".env" \
    ./ {{host}}:{{remote_dir}}/
  ssh {{host}} "sudo bash {{remote_dir}}/bootstrap.sh"

# Perform a forced-notify run on the server.
force-notify:
  ssh {{host}} "cd {{remote_dir}} && ./run_job.sh --force-notify"

# Show last 10 DB rows excluding web_html.
status:
  ssh {{host}} "sqlite3 {{remote_dir}}/data/eurix-monitor.db \"SELECT id, checked_at, sms_content, should_notify, force_notify, notified_at FROM eurix_monitoring ORDER BY id DESC LIMIT 10;\""

