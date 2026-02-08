from __future__ import annotations

import logging
import boto3

logger = logging.getLogger(__name__)

def publish_sms(
    *, phone_number: str, region: str, message: str, sms_type: str, sender_id: str
) -> str:
    client = boto3.client("sns", region_name=region)
    message_attributes = {
        "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": str(sms_type)},
        "AWS.SNS.SMS.SenderID": {"DataType": "String", "StringValue": str(sender_id)},
    }
    resp = client.publish(
        PhoneNumber=str(phone_number),
        Message=str(message),
        MessageAttributes=message_attributes,
    )
    msg_id = str(resp.get("MessageId", ""))
    logger.info(
        "SNS publish ok. message_id=%s sms_type=%s sender_id=%s to=%s",
        msg_id,
        sms_type,
        sender_id,
        phone_number,
    )
    return msg_id

