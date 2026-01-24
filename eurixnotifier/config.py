import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    aws_region: str
    sns_topic_arn: Optional[str]
    db_path: str

    @staticmethod
    def from_env(*, require_sns: bool) -> "Settings":
        openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not openai_api_key:
            raise RuntimeError("Missing required env var OPENAI_API_KEY")

        sns_topic_arn = os.environ.get("SNS_TOPIC_ARN", "").strip()
        if require_sns and not sns_topic_arn:
            raise RuntimeError("Missing required env var SNS_TOPIC_ARN")

        aws_region = os.environ.get("AWS_REGION", "").strip() or os.environ.get("AWS_DEFAULT_REGION", "").strip()
        if not aws_region:
            aws_region = "eu-north-1"

        db_path = os.environ.get("EURIX_DB_PATH", "data/eurix-monitor.db").strip()

        openai_model = os.environ.get("OPENAI_MODEL", "GPT-5.2-Thinking").strip()

        return Settings(
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            aws_region=aws_region,
            sns_topic_arn=sns_topic_arn or None,
            db_path=db_path,
        )

