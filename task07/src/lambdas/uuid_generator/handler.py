import boto3
import datetime
import json
import uuid

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('UuidGenerator-handler')
s3_client = boto3.client("s3")

class UuidGenerator(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):

        payload = {
            "ids": []
        }
        for _ in range(10):
            id = str(uuid.uuid4())
            payload["ids"].append(id)
    
        _LOG.info(f"payload: {payload}")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        _LOG.info(f"timestamp: {timestamp}")
        s3_client.put_object(
            Bucket="cmtr-cmtr-62505701-uuid-storage-test",
            Key=timestamp,
            Body=bytes(json.dumps(payload).encode("utf-8"))
        )


HANDLER = UuidGenerator()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
