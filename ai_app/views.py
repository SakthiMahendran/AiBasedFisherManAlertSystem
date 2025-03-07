from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
import math
import logging
from global_land_mask import globe  # Import the land mask library

logger = logging.getLogger(__name__)

class ChatView(APIView):
    """
    Fetches weather data from Open-Meteo's Marine API.
    Before fetching, it checks if the location is land or water using Global Land Mask.
    """
    permission_classes = [AllowAny]

    def clean_value(self, value):
        """ Safely handle numeric data for marine calls. """
        try:
            value = float(value)
            if math.isnan(value) or math.isinf(value) or abs(value) > 1e5:
                return None
            return value
        except (TypeError, ValueError):
            return None

    def validate_json(self, data):
        """ Validate that 'data' is JSON-serializable before returning. """
        import json
        try:
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            logger.error("Non-serializable data encountered: %s", data, exc_info=True)
            return {}

    def is_land(self, lat, lon):
        """ Check if the selected coordinates are on land using Global Land Mask. """
        return globe.is_land(lat, lon)

    def fetch_marine_data(self, lat, lon):
        """ Fetch Marine data for the given lat/lon using Open-Meteo Marine API. """
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "wave_height,wave_direction,wave_period,"
                       "wind_wave_height,wind_wave_direction,wind_wave_period,"
                       "wind_wave_peak_period,ocean_current_velocity,ocean_current_direction",
            "daily": "wave_height_max,wave_direction_dominant,wave_period_max,"
                     "wind_wave_height_max,wind_wave_direction_dominant,wind_wave_period_max,"
                     "wind_wave_peak_period_max",
            "timeformat": "unixtime",
            "timezone": "Asia/Singapore"
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()

    def get(self, request):
        """ Main GET handler: Checks land/water first, then fetches marine data if valid. """
        latitude = request.query_params.get("latitude", 54.544587)
        longitude = request.query_params.get("longitude", 10.227487)

        try:
            lat_f = float(latitude)
            lon_f = float(longitude)

            # Check if the selected point is land
            if self.is_land(lat_f, lon_f):
                return Response(
                    {"error": "You selected a land area where data cannot be fetched."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Fetch Marine Data
                marine_data = self.fetch_marine_data(lat_f, lon_f)
                current = marine_data.get('current', {})

                current_data = {
                    "wave_height":           self.clean_value(current.get("wave_height")),
                    "wave_direction":        self.clean_value(current.get("wave_direction")),
                    "wave_period":           self.clean_value(current.get("wave_period")),
                    "wind_wave_height":      self.clean_value(current.get("wind_wave_height")),
                    "wind_wave_direction":   self.clean_value(current.get("wind_wave_direction")),
                    "wind_wave_period":      self.clean_value(current.get("wind_wave_period")),
                    "wind_wave_peak_period": self.clean_value(current.get("wind_wave_peak_period")),
                    "ocean_current_velocity": self.clean_value(current.get("ocean_current_velocity")),
                    "ocean_current_direction": self.clean_value(current.get("ocean_current_direction")),
                }

                response_data = {
                    "weather_data": current_data,
                    "latitude": marine_data.get("latitude"),
                    "longitude": marine_data.get("longitude"),
                    "endpoint_used": "marine"
                }

            except Exception as marine_err:
                logger.warning(
                    "Marine endpoint failed for lat=%s lon=%s. Error: %s",
                    latitude, longitude, marine_err,
                    exc_info=True
                )
                return Response(
                    {"error": "Weather data could not be retrieved at this time."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                self.validate_json(response_data),
                status=status.HTTP_200_OK,
            )

        except ValueError as ve:
            logger.exception("ValueError when processing lat/lon or data: %s", ve)
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
