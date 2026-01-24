from __future__ import annotations

import logging
import boto3

logger = logging.getLogger(__name__)

def publish_sms(*, topic_arn: str, region: str, message: str) -> str:
    client = boto3.client("sns", region_name=region)
    resp = client.publish(TopicArn=str(topic_arn), Message=str(message))
    msg_id = str(resp.get("MessageId", ""))
    logger.info("SNS publish ok. message_id=%s", msg_id)
    return msg_id

