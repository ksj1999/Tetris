import os
import requests
from datetime import datetime, timedelta
from db import get_db_connection
from flask import Blueprint


weather_bp = Blueprint('weather', __name__)


def fetch_weather_data(service_key, base_date, base_time, nx, ny):
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        'serviceKey': service_key,
        'numOfRows': '50',
        'pageNo': '1',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': nx,
        'ny': ny
    }
    response = requests.get(url, params=params)
    print(f"API response status code: {response.status_code}")
    print(f"API response headers: {response.headers}")
    print(f"API response text: {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        return None

def store_weather_data(items):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                for item in items:
                    if item['category'] in ['POP', 'PCP', 'REH', 'TMP', 'WSD']:
                        cursor.execute("""
                            INSERT INTO weather_forecast (
                                base_date, base_time, forecast_date, forecast_time, nx, ny,
                                precipitation_probability, hourly_precipitation, humidity,
                                hourly_temperature, wind_speed
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            item['baseDate'],
                            item['baseTime'],
                            item['fcstDate'],
                            item['fcstTime'],
                            item['nx'],
                            item['ny'],
                            item['fcstValue'] if item['category'] == 'POP' else None,
                            item['fcstValue'] if item['category'] == 'PCP' else None,
                            item['fcstValue'] if item['category'] == 'REH' else None,
                            item['fcstValue'] if item['category'] == 'TMP' else None,
                            item['fcstValue'] if item['category'] == 'WSD' else None
                        ))
                connection.commit()
        print("Weather data stored successfully")
    except Exception as e:
        print(f"Failed to store weather data: {e}")

def fetch_and_store_all_weather():
    service_key = os.getenv('WEATHER_API_KEY')
    base_times = ["0500", "1100", "1700", "2300"]  # Typical base times for forecasts
    locations = [
        {'nx': 97, 'ny': 75},
    ]

    for location in locations:
        for base_time in base_times:
            for days_ago in range(2):
                base_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
                weather_data = fetch_weather_data(service_key, base_date, base_time, location['nx'], location['ny'])
                if weather_data and 'response' in weather_data and 'body' in weather_data['response']:
                    items = weather_data['response']['body']['items']['item']
                    store_weather_data(items)
                else:
                    print(f"No data for location (nx: {location['nx']}, ny: {location['ny']}) on {base_date} at {base_time}")

if __name__ == '__main__':
    fetch_and_store_all_weather()
