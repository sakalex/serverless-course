from tests.test_sns_handler import SnsHandlerLambdaTestCase


class TestSuccess(SnsHandlerLambdaTestCase):

    def test_success(self):
        self.assertEqual(self.HANDLER.handle_request({
            "Records": [
                {
                    "Sns": {
                        "Message": "Hello from SNS"
                    }
                }
            ]
        }, dict()), None)

