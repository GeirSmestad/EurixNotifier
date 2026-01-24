set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

host := "bergenomap"
remote_dir := "/srv/eurixnotifier"

# Copy files to the server and run bootstrap.sh.
deploy:
  ssh {{host}} "mkdir -p {{remote_dir}}"
  scp -r \
    bootstrap.sh \
    run_job.sh \
    requirements.txt \
    README.md \
    eurixnotifier \
    prompts \
    {{host}}:{{remote_dir}}/
  ssh {{host}} "sudo bash {{remote_dir}}/bootstrap.sh"

# Perform a forced-notify run on the server.
force-notify:
  ssh {{host}} "cd {{remote_dir}} && ./run_job.sh --force-notify"

# Show last 10 DB rows excluding web_html.
status:
  ssh {{host}} "sqlite3 {{remote_dir}}/data/eurix-monitor.db \"SELECT id, checked_at, sms_content, should_notify, force_notify, notified_at FROM eurix_monitoring ORDER BY id DESC LIMIT 10;\""

