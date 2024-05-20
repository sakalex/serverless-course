import json

import requests

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda


class OpenMeteoAPI:

    def __init__(self) -> None:
        self.url = "https://api.open-meteo.com/v1/forecast"

    def get_weather_forecast(self, latitude: float, longitude: float) -> dict: 
        
        try:
            response = requests.get(
                url=self.url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
                }
            )
            response.raise_for_status()
            forecast = response.json()
        except Exception as e:
            _LOG.error(f"Failed to get weather forecast: {e}")
            raise 
        return forecast


_LOG = get_logger('ApiHandler-handler')
open_meteo_api = OpenMeteoAPI()


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        """
        Explain incoming event here
        """

        print("Event: ", event)

        method = event["requestContext"]["http"]["method"]
        path = event["requestContext"]["http"]["path"]

        if method == "GET" and path == "/weather":

            latitude = 48.8566
            longitude = 2.3522
            forecast = open_meteo_api.get_weather_forecast(latitude=latitude, longitude=longitude)

            return {
                "statusCode": 200,
                "body": json.dumps(forecast)
            }

    

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
