# EurixNotifyer

This app runs as a cron job on a Linux server, monitors a website with an LLM and notifies people by SMS if registration for the Eurix festival has been opened.

## What it does
- Fetches `https://felixruckert.de/2015/10/01/eurix/`
- Asks OpenAI for JSON (`sms_content`, `should_notify`) about **Eurix 2027**
- Logs every run to SQLite (`data/eurix-monitor.db`)
- Sends SMS via AWS SNS direct publish when `should_notify=true` (or when forced)

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
  - `EN_OPENAI_API_KEY` (required)
- **Recipients**:
  - `EN_RECIPIENT_PHONE_NUMBERS` (required for sending)
- **AWS (Option B / IAM user keys)**:
  - `AWS_ACCESS_KEY_ID` (required for SNS publish)
  - `AWS_SECRET_ACCESS_KEY` (required for SNS publish)
  - `AWS_DEFAULT_REGION` (optional; the code also sets a region explicitly)

Non-secret settings are hard-coded in `eurixnotifier/config.py` (model, region, db path, SMS type).

## Server deployment
The app is intended to live at `/srv/eurixnotifier` and be executed by cron.

- `bootstrap.sh` is idempotent and installs dependencies, initializes the DB, and installs `/etc/cron.d/eurixnotifier`.
- `run_job.sh` loads `/srv/eurixnotifier/.env` (if present) and runs the job using the venv.

Recommended: create `/srv/eurixnotifier/.env` on the server with at least:

```bash
EN_OPENAI_API_KEY=...
EN_RECIPIENT_PHONE_NUMBERS=["+4712345678", "+4787654321"]
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=eu-west-1
```

## Just commands
- `just deploy`: scp files to server and run bootstrap
- `just force-notify`: run a forced notification on the server
- `just status`: show last 10 DB rows (excluding `web_html`)
