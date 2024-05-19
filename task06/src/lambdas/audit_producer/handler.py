import boto3
import datetime
import uuid

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('AuditProducer-handler')
dynamodb = boto3.resource("dynamodb")
audit_table = dynamodb.Table("cmtr-62505701-Audit-test")


class AuditProducer(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):

        _LOG.info(f"Event: {event}")
        
        for record in event["Records"]:

            if record["eventName"] == "INSERT":
                audit_item = {
                    "newValue": {
                        "key": record["dynamodb"]["NewImage"]["key"]["S"],
                        "value": int(record["dynamodb"]["NewImage"]["value"]["N"])
                    }
                }
            elif record["eventName"] == "MODIFY":
                audit_item = {
                    "updatedAttribute": "value",
                    "oldValue": int(record["dynamodb"]["OldImage"]["value"]["N"]),
                    "newValue": int(record["dynamodb"]["NewImage"]["value"]["N"])
                }
            else:
                continue
            
            audit_item["id"] = str(uuid.uuid4())
            audit_item["itemKey"] = record["dynamodb"]["NewImage"]["key"]["S"]
            audit_item["modificationTime"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            _LOG.info(f"Audit item: {audit_item}")
            audit_table.put_item(Item=audit_item)
    

HANDLER = AuditProducer()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
