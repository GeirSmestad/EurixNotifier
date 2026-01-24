from __future__ import annotations

import boto3


def publish_sms(*, topic_arn: str, region: str, message: str) -> None:
    client = boto3.client("sns", region_name=region)
    client.publish(TopicArn=str(topic_arn), Message=str(message))

