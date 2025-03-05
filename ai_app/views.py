from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests_cache
import openmeteo_requests
from retry_requests import retry
import requests
import math
import logging

logger = logging.getLogger(__name__)

class ChatView(APIView):
    """
    Attempts to fetch weather data from Open-Meteo's Marine API first.
    If that fails (e.g., because the coordinate is landlocked), falls back
    to the normal forecast endpoint using plain 'requests'.
    """
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Setup the Open-Meteo API client (marine)
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        self.retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=self.retry_session)

    def clean_value(self, value):
        """
        Safely handle numeric data for the marine call.
        If the library itself fails, we won't reach here, but we keep it for completeness.
        """
        if not isinstance(value, (int, float)):
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        # If wave data is absurdly large, discard it.
        if abs(value) > 1e5:
            return None
        return float(value)

    def validate_json(self, data):
        """
        Validate that 'data' is JSON-serializable before returning.
        """
        import json
        try:
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            logger.error("Non-serializable data encountered: %s", data, exc_info=True)
            return {}  # or raise an exception

    def fetch_marine_data(self, lat, lon):
        """
        Fetch Marine data for the given lat/lon using openmeteo_requests.
        Returns a WeatherApiResponse object, which has .Current(), etc.
        Raises an exception if the data is invalid for these coords.
        """
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": lat,
            "longitude": lon,
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
        print(response)
        # response is typically a list of 1 or more WeatherApiResponse objects
        # Take the first item
        return response[0]

    def fetch_fallback_data(self, lat, lon):
        """
        Fetch standard forecast data directly with 'requests', parse as JSON, and return as a dict.
        This bypasses openmeteo_requests for the fallback to avoid attribute errors.
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relativehumidity_2m",
            "current_weather": True,
            "timezone": "Asia/Singapore",
        }
        # Make a standard requests call
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()  # Raises HTTPError if non-200
        return r.json()       # Return a plain Python dictionary

    def get(self, request):
        """
        Main GET handler. Calls the Marine API first; if that fails, uses the fallback standard forecast.
        """
        latitude = request.query_params.get("latitude", 54.544587)
        longitude = request.query_params.get("longitude", 10.227487)

        print(type(latitude))
        print(latitude)
        print(float(latitude))

        try:
            lat_f = float(latitude)
            lon_f = float(longitude)

            try:
                # 1) Try Marine data first
                marine_data = self.fetch_marine_data(lat_f, lon_f)
                current = marine_data.Current()

                print(self.clean_value(current.Variables(8).Value()))

                current_data = {
                    "wave_height":           self.clean_value(current.Variables(0).Value()),
                    "wave_direction":        self.clean_value(current.Variables(1).Value()),
                    "wave_period":           self.clean_value(current.Variables(2).Value()),
                    "wind_wave_height":      self.clean_value(current.Variables(3).Value()),
                    "wind_wave_direction":   self.clean_value(current.Variables(4).Value()),
                    "wind_wave_period":      self.clean_value(current.Variables(5).Value()),
                    "wind_wave_peak_period": self.clean_value(current.Variables(6).Value()),
                    "ocean_current_velocity":self.clean_value(current.Variables(7).Value()),
                    "ocean_current_direction":self.clean_value(current.Variables(8).Value()),
                }

                response_data = {
                    "weather_data": current_data,
                    "latitude": marine_data.Latitude(),
                    "longitude": marine_data.Longitude(),
                    "endpoint_used": "marine"
                }

            except Exception as marine_err:
                # 2) If Marine fails (e.g. landlocked => wave parse error), fallback
                logger.warning(
                    "Marine endpoint failed for lat=%s lon=%s. Error: %s",
                    latitude, longitude, marine_err,
                    exc_info=True  # logs stack trace
                )
                fallback_dict = self.fetch_fallback_data(lat_f, lon_f)

                # fallback_dict is a normal Python dict, e.g.:
                # {
                #   'latitude':  <float>,
                #   'longitude': <float>,
                #   'generationtime_ms': ...,
                #   'hourly': {...},
                #   'current_weather': {
                #       'temperature':  27.3,
                #       'windspeed':    5.4,
                #       'winddirection':80,
                #       'weathercode':  3,
                #       'time':         '2025-03-05T10:00'
                #   },
                #   ...
                # }
                cw = fallback_dict.get("current_weather", {})
                response_data = {
                    "weather_data": {
                        "temperature_2m": cw.get("temperature"),
                        "relativehumidity_2m": None,  # Could parse from fallback_dict["hourly"] if needed
                        "windspeed": cw.get("windspeed"),
                        "winddirection": cw.get("winddirection"),
                        "weathercode": cw.get("weathercode"),
                        "time": cw.get("time"),
                    },
                    "latitude": fallback_dict.get("latitude"),
                    "longitude": fallback_dict.get("longitude"),
                    "endpoint_used": "standard_forecast"
                }

            # Validate JSON and return
            return Response(
                self.validate_json(response_data),
                status=status.HTTP_200_OK,
            )

        except ValueError as ve:
            logger.exception("ValueError when processing lat/lon or data: %s", ve)
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as re:
            logger.exception("RuntimeError occurred: %s", re)
            return Response({"error": str(re)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
