from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests_cache
import openmeteo_requests
from retry_requests import retry
import math
import logging

logger = logging.getLogger(__name__)

class ChatView(APIView):
    """
    Fetches weather data using the Open-Meteo API and returns it to the client.
    """
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Setup the Open-Meteo API client
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        self.retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=self.retry_session)

    def fetch_weather_data(self, latitude, longitude):
        """
        Fetch weather data from Open-Meteo API.
        """
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "wave_height", "wave_direction", "wave_period",
                "wind_wave_height", "wind_wave_direction", "wind_wave_period",
                "wind_wave_peak_period", "ocean_current_velocity", "ocean_current_direction"
            ],
            "daily": [
                "wave_height_max", "wave_direction_dominant", "wave_period_max",
                "wind_wave_height_max", "wind_wave_direction_dominant", "wind_wave_period_max",
                "wind_wave_peak_period_max"
            ],
            "timeformat": "unixtime",
            "timezone": "Asia/Singapore"
        }
        response = self.openmeteo.weather_api(url, params=params)
        return response[0]  # Assume a single location response for simplicity

    def clean_value(self, value):
        """
        Ensure float values are JSON-compliant by replacing NaN, inf, and -inf with None.
        """
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None  # Replace with a default value if needed
        return value

    def validate_json(self, data):
        """
        Validate the data to ensure it's JSON-serializable.
        """
        import json
        try:
            json.dumps(data)  # Test if data is serializable
            return data
        except (TypeError, ValueError):
            logger.error("Non-serializable data encountered: %s", data)
            return {}  # Return an empty dictionary or error message

    def get(self, request):
        """
        Fetch weather data and return to the client.
        """
        latitude = request.query_params.get("latitude", 54.544587)  # Default latitude
        longitude = request.query_params.get("longitude", 10.227487)  # Default longitude

        try:
            # Fetch weather data
            weather_data = self.fetch_weather_data(float(latitude), float(longitude))
            current = weather_data.Current()
            current_data = {
                "wave_height": self.clean_value(current.Variables(0).Value()),
                "wave_direction": self.clean_value(current.Variables(1).Value()),
                "wave_period": self.clean_value(current.Variables(2).Value()),
                "wind_wave_height": self.clean_value(current.Variables(3).Value()),
                "wind_wave_direction": self.clean_value(current.Variables(4).Value()),
                "wind_wave_period": self.clean_value(current.Variables(5).Value()),
                "wind_wave_peak_period": self.clean_value(current.Variables(6).Value()),
                "ocean_current_velocity": self.clean_value(current.Variables(7).Value()),
                "ocean_current_direction": self.clean_value(current.Variables(8).Value()),
            }

            # Validate JSON response
            return Response(
                self.validate_json({
                    "weather_data": current_data,
                    "latitude": weather_data.Latitude(),
                    "longitude": weather_data.Longitude(),
                }),
                status=status.HTTP_200_OK,
            )
        except ValueError as ve:
            logger.error("ValueError: %s", str(ve))
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as re:
            logger.error("RuntimeError: %s", str(re))
            return Response({"error": str(re)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
