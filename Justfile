set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

host := "bergenomap"
remote_dir := "/srv/eurixnotifier"
env_file := "secrets/eurixnotifier.env"

# Print usage (default).
default:
  @echo "EurixNotifyer Justfile"
  @echo ""
  @echo "Usage:"
  @echo "  just deploy        # copy code to server + run bootstrap"
  @echo "  just push-env      # upload secrets to /srv/eurixnotifier/.env"
  @echo "  just force-notify  # run job with --force-notify on server"
  @echo "  just status        # show last 10 DB rows (no web_html)"

# Copy files to the server and run bootstrap.sh.
deploy:
  ssh {{host}} "sudo mkdir -p {{remote_dir}} && sudo chown ubuntu:ubuntu {{remote_dir}}"
  scp -r \
    bootstrap.sh \
    run_job.sh \
    requirements.txt \
    README.md \
    eurixnotifier \
    prompts \
    {{host}}:{{remote_dir}}/
  ssh {{host}} "sudo chmod +x {{remote_dir}}/bootstrap.sh {{remote_dir}}/run_job.sh"
  ssh {{host}} "sudo bash {{remote_dir}}/bootstrap.sh"

# Perform a forced-notify run on the server.
force-notify:
  ssh {{host}} "cd {{remote_dir}} && ./run_job.sh --force-notify"

# Push runtime env vars (secrets) to the server.
# This is intentionally separate from deploy.
push-env:
  test -f {{env_file}}
  ssh {{host}} "sudo mkdir -p {{remote_dir}} && sudo chown ubuntu:ubuntu {{remote_dir}}"
  scp {{env_file}} {{host}}:{{remote_dir}}/.env
  ssh {{host}} "sudo chown ubuntu:ubuntu {{remote_dir}}/.env && sudo chmod 600 {{remote_dir}}/.env"

# Show last 10 DB rows excluding web_html.
status:
  ssh {{host}} "sqlite3 {{remote_dir}}/data/eurix-monitor.db \"SELECT id, checked_at, sms_content, should_notify, force_notify, notified_at FROM eurix_monitoring ORDER BY id DESC LIMIT 10;\""

