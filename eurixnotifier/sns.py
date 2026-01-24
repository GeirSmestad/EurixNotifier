from __future__ import annotations

import logging
import boto3

logger = logging.getLogger(__name__)

def publish_sms(*, phone_number: str, region: str, message: str, sms_type: str) -> str:
    client = boto3.client("sns", region_name=region)
    resp = client.publish(
        PhoneNumber=str(phone_number),
        Message=str(message),
        MessageAttributes={
            "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": str(sms_type)}
        },
    )
    msg_id = str(resp.get("MessageId", ""))
    logger.info("SNS publish ok. message_id=%s sms_type=%s to=%s", msg_id, sms_type, phone_number)
    return msg_id

