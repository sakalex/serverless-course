from tests.test_api_handler import ApiHandlerLambdaTestCase


class TestSuccess(ApiHandlerLambdaTestCase):

    def test_success(self):
        self.assertEqual(True, True)

