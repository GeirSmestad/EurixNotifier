# EurixNotifyer

This app runs as a cron job on a Linux server, and notifies people by SMS if registration for the Eurix festival has been opened.

## What it does
- Fetches `https://felixruckert.de/2015/10/01/eurix/`
- Asks OpenAI for JSON (`sms_content`, `should_notify`) about **Eurix 2027**
- Logs every run to SQLite (`data/eurix-monitor.db`)
- Sends an SMS via AWS SNS topic when `should_notify=true` (or when forced)

## Local usage
Install deps:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run (requires env vars below):

```bash
python -m eurixnotifier
python -m eurixnotifier --force-notify
python -m eurixnotifier --no-sns
```

## Configuration (env vars)
- **OpenAI**:
  - `OPENAI_API_KEY` (required)
  - `OPENAI_MODEL` (optional, defaults to `GPT-5.2-Thinking`)
- **AWS / SNS**:
  - `AWS_REGION` (optional, defaults to `eu-north-1`)
  - `SNS_TOPIC_ARN` (required unless you run with `--no-sns` or `--dry-run`)
- **DB**:
  - `EURIX_DB_PATH` (optional, defaults to `data/eurix-monitor.db`)

## Server deployment
The app is intended to live at `/srv/eurixnotifier` and be executed by cron.

- `bootstrap.sh` is idempotent and installs dependencies, initializes the DB, and installs `/etc/cron.d/eurixnotifier`.
- `run_job.sh` loads `/srv/eurixnotifier/.env` (if present) and runs the job using the venv.

Recommended: create `/srv/eurixnotifier/.env` on the server with at least:

```bash
OPENAI_API_KEY=...
SNS_TOPIC_ARN=...
AWS_REGION=eu-north-1
EURIX_DB_PATH=/srv/eurixnotifier/data/eurix-monitor.db
```

## Just commands
- `just deploy`: rsync to server and run bootstrap
- `just force-notify`: run a forced notification on the server
- `just status`: show last 10 DB rows (excluding `web_html`)