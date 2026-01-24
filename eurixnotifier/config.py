import os
from dataclasses import dataclass

# All non-secret config is hard-coded here (per v1 requirements).
# Only secrets should be provided via environment variables, prefixed with EN_.

# Non-secret config (hard-coded)
OPENAI_MODEL = "gpt-5.2"
AWS_REGION = "eu-west-1"
DB_PATH = "data/eurix-monitor.db"

# Non-secret but environment-specific; hard-coded by editing this file.
# Example: arn:aws:sns:eu-north-1:123456789012:eurix-notifier
SNS_TOPIC_ARN = "arn:aws:sns:eu-west-1:471112760902:EurixNotifyer"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    aws_region: str
    sns_topic_arn: str
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

        sns_topic_arn = SNS_TOPIC_ARN.strip()
        if require_sns and (not sns_topic_arn or "REPLACE_ME" in sns_topic_arn):
            raise RuntimeError(
                "SNS topic ARN is not configured. Set SNS_TOPIC_ARN in eurixnotifier/config.py "
                "(or run with --no-sns/--dry-run)."
            )

        return Settings(
            openai_api_key=openai_api_key,
            openai_model=OPENAI_MODEL,
            aws_region=AWS_REGION,
            sns_topic_arn=sns_topic_arn,
            db_path=DB_PATH,
        )

