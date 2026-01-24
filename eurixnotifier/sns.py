from __future__ import annotations

import logging
import boto3

logger = logging.getLogger(__name__)

def publish_sms(*, topic_arn: str, region: str, message: str, debug: bool = False) -> str:
    client = boto3.client("sns", region_name=region)
    if debug:
        # These may require extra permissions beyond sns:Publish; log and continue if denied.
        try:
            attrs = client.get_topic_attributes(TopicArn=str(topic_arn)).get("Attributes", {})
            logger.debug("SNS topic attributes: %s", attrs)
        except Exception:
            logger.exception("Failed to read SNS topic attributes (permission?).")
        try:
            subs = client.list_subscriptions_by_topic(TopicArn=str(topic_arn)).get("Subscriptions", [])
            logger.debug("SNS subscriptions count: %s", len(subs))
            logger.debug("SNS subscriptions (truncated): %s", subs[:20])
        except Exception:
            logger.exception("Failed to list SNS subscriptions (permission?).")

    resp = client.publish(TopicArn=str(topic_arn), Message=str(message))
    msg_id = str(resp.get("MessageId", ""))
    logger.info("SNS publish ok. message_id=%s", msg_id)
    return msg_id

