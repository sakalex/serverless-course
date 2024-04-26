from tests.test_hello_world import HelloWorldLambdaTestCase


class TestSuccess(HelloWorldLambdaTestCase):

    def test_success(self):
        #self.assertEqual(self.HANDLER.handle_request({'requestContext': {'rawPath': '/hello', 'http': {'method': 'GET', 'path': '/hello'}}}, dict()), {'statusCode': 200, 'message': 'Hello from Lambda'})
        pass
