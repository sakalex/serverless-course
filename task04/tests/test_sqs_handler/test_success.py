from tests.test_sqs_handler import SqsHandlerLambdaTestCase


class TestSuccess(SqsHandlerLambdaTestCase):

    def test_success(self):
        self.assertEqual(self.HANDLER.handle_request({
            "Records": [
                {
                    "body": "Hello from SQS"
                }
            ]
        }, dict()), None)

