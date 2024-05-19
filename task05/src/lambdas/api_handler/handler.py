import boto3
import datetime
import json
import uuid

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('ApiHandler-handler')


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):

        # print the content of the API Gateway request
        _LOG.info(event)
    
        request_body = event 

        principalId = request_body["principalId"]
        content = request_body["content"]
        id = str(uuid.uuid4())
        time_format = "%Y-%m-%dT%H:%M:%S.%f"
        created_at = datetime.datetime.now().strftime(time_format)
        event = {
            "id": id,
            "principalId": principalId,
            "createdAt": created_at,
            "body": content,
        }

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("cmtr-62505701-Events")
        table.put_item(Item=event)

        response = {
            "statusCode": 201,
            "event": event
        }

        return response
    

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
