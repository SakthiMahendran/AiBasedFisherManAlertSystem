import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test coordinates (should be an oceanic location)
TEST_LAT = 36.96   # Near California coast
TEST_LON = -122.02

def fetch_marine_data(lat, lon):
    """
    Fetch Marine data from Open-Meteo API.
    """
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

    for i in range(3):  # Retry up to 3 times
        try:
            logger.info(f"Sending request to Marine API (Attempt {i+1})...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()  # Raises error for non-200 responses
            logger.info("✅ API request successful!")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Marine API request failed (Attempt {i+1}): {e}")
            time.sleep(2 ** i)  # Exponential backoff

    raise RuntimeError("❌ Failed to fetch marine data after 3 retries")


if __name__ == "__main__":
    try:
        result = fetch_marine_data(TEST_LAT, TEST_LON)
        print("\n🌊 Marine API Response:")
        print(result)  # Print full JSON response
    except Exception as e:
        logger.error(f"🚨 Test failed: {e}")
