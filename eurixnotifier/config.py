import os
from dataclasses import dataclass
from typing import List

# All non-secret config is hard-coded here (per v1 requirements).
# Only secrets should be provided via environment variables, prefixed with EN_.

# Non-secret config (hard-coded)
OPENAI_MODEL = "gpt-5.2"
AWS_REGION = "eu-west-1"
DB_PATH = "data/eurix-monitor.db"

# AWS SNS SMS type to use for API publishes.
# Valid values: "Transactional" or "Promotional"
# Transactional is semantically correct for this notifier.
SNS_SMS_TYPE = "Transactional"

RECIPIENT_PHONE_NUMBERS_ENV = "EN_RECIPIENT_PHONE_NUMBERS"


def _parse_recipient_phone_numbers(raw: str) -> List[str]:
    """
    Accepts either:
      - A comma-separated string: "+471..., +472..."
      - A JSON array string: ["+471...","+472..."]
      - Your provided format: ["+471..., +472..."] (single element that is comma-separated)
    Returns normalized E.164-ish strings like +47xxxxxxxx.
    """
    raw = (raw or "").strip()
    if not raw:
        return []

    items: List[str] = []
    if raw.startswith("["):
        import json

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None

        if isinstance(parsed, list):
            # Handle the single-element "comma list inside list" case.
            if len(parsed) == 1 and isinstance(parsed[0], str) and "," in parsed[0]:
                items = [p.strip() for p in parsed[0].split(",")]
            else:
                items = [str(x).strip() for x in parsed]
        else:
            # Fall back to comma split
            items = [p.strip() for p in raw.strip("[]").split(",")]
    else:
        items = [p.strip() for p in raw.split(",")]

    # Normalize: strip quotes/spaces, enforce leading +, remove internal spaces
    out: List[str] = []
    for it in items:
        it = it.strip().strip('"').strip("'")
        it = it.replace(" ", "")
        if not it:
            continue
        if not it.startswith("+"):
            raise RuntimeError(f"Invalid phone number '{it}': must start with + and country code (E.164).")
        out.append(it)
    return out


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    aws_region: str
    sns_sms_type: str
    recipient_phone_numbers: List[str]
    db_path: str

    @staticmethod
    def from_env(*, require_sns: bool) -> "Settings":
        openai_api_key = os.environ.get("EN_OPENAI_API_KEY", "").strip()
        if not openai_api_key:
            raise RuntimeError("Missing required env var EN_OPENAI_API_KEY")

        # Option B: IAM user credentials supplied as standard AWS_* env vars (not EN_*).
        # We validate presence for clarity, while still allowing --no-sns/--dry-run.
        if require_sns:
            akid = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
            sak = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
            if not (akid and sak):
                raise RuntimeError(
                    "Missing AWS credentials. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
                    "in /srv/eurixnotifier/.env (Option B), or run with --no-sns/--dry-run."
                )

        recipients_raw = os.environ.get(RECIPIENT_PHONE_NUMBERS_ENV, "").strip()
        recipients = _parse_recipient_phone_numbers(recipients_raw)
        if require_sns and not recipients:
            raise RuntimeError(
                f"Missing recipients. Set {RECIPIENT_PHONE_NUMBERS_ENV} in /srv/eurixnotifier/.env, "
                'e.g. EN_RECIPIENT_PHONE_NUMBERS=["+4712345678", "+4787654321"]'
            )

        return Settings(
            openai_api_key=openai_api_key,
            openai_model=OPENAI_MODEL,
            aws_region=AWS_REGION,
            sns_sms_type=SNS_SMS_TYPE,
            recipient_phone_numbers=recipients,
            db_path=DB_PATH,
        )

