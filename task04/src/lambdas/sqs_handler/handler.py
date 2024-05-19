from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger('SqsHandler-handler')


class SqsHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):

        # print the content of the SQS message
        for record in event["Records"]:
            _LOG.info(record["body"])
    

HANDLER = SqsHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
