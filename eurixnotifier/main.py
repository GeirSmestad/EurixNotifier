from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_URL = "https://felixruckert.de/2015/10/01/eurix/"


@dataclass(frozen=True)
class CliArgs:
    force_notify: bool
    dry_run: bool
    no_sns: bool
    debug: bool
    url: str


def _parse_args(argv: List[str]) -> CliArgs:
    p = argparse.ArgumentParser(prog="eurixnotifier")
    p.add_argument(
        "--force-notify",
        action="store_true",
        help="Send SMS regardless of model should_notify.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to SNS (still writes DB).",
    )
    p.add_argument(
        "--no-sns",
        action="store_true",
        help="Disable SNS publish (still writes DB).",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (prints details to stderr / cron log).",
    )
    p.add_argument("--url", default=DEFAULT_URL, help="Override URL to fetch.")
    ns = p.parse_args(argv)
    return CliArgs(
        force_notify=bool(ns.force_notify),
        dry_run=bool(ns.dry_run),
        no_sns=bool(ns.no_sns),
        debug=bool(ns.debug),
        url=str(ns.url),
    )


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # Lazy imports so `--help` doesn't require dependencies.
    from eurixnotifier.config import Settings
    from eurixnotifier.db import MonitoringRow, ensure_db, insert_monitoring_row, mark_notified
    from eurixnotifier.fetch_page import fetch_html
    from eurixnotifier.openai_analyze import analyze_html_for_sms
    from eurixnotifier.sns import publish_sms

    require_sns = not (args.dry_run or args.no_sns)
    settings = Settings.from_env(require_sns=require_sns)
    ensure_db(settings.db_path)

    checked_at = datetime.now(timezone.utc)
    web_html = fetch_html(args.url)

    analysis = analyze_html_for_sms(
        html=web_html,
        today=checked_at.date(),
        model=settings.openai_model,
        api_key=settings.openai_api_key,
    )

    row = MonitoringRow(
        checked_at=checked_at,
        web_html=web_html,
        sms_content=analysis.sms_content,
        should_notify=analysis.should_notify,
        force_notify=args.force_notify,
        notified_at=None,
    )
    row_id = insert_monitoring_row(settings.db_path, row)

    will_notify = args.force_notify or analysis.should_notify
    sns_message_id: str | None = None
    sns_ok = False
    if will_notify and not (args.dry_run or args.no_sns):
        # Settings.from_env() already validates SNS topic ARN and AWS creds when needed.
        try:
            sns_message_id = publish_sms(
                topic_arn=settings.sns_topic_arn,
                region=settings.aws_region,
                message=row.sms_content,
                debug=args.debug,
            )
            sns_ok = True
            mark_notified(settings.db_path, row_id=row_id, notified_at=datetime.now(timezone.utc))
        except Exception:
            logger.exception("SNS publish failed.")
            # Keep the DB row, but return non-zero to surface failure in cron.
            sns_ok = False

    # Human-friendly stdout, while keeping logs in DB.
    print(
        json.dumps(
            {
                "row_id": row_id,
                "checked_at": checked_at.isoformat(),
                "should_notify": analysis.should_notify,
                "force_notify": args.force_notify,
                "will_notify": will_notify,
                "sns_sent": bool(sns_ok),
                "sns_message_id": sns_message_id,
            },
            ensure_ascii=False,
        )
    )
    if will_notify and not (args.dry_run or args.no_sns) and not sns_ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

