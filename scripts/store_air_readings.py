import os
import json
import sqlite3
import requests

api_url = "http://a816-dohmeta.nyc.gov/MetadataLite/api/AirQuality/GetData?type=json"

response = requests.get(api_url)
readings = json.loads(response.content.decode('utf-8'))

requests.post('http://127.0.0.1:8000/api/air_data', json=readings)

