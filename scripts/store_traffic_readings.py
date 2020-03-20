# NOTE: Motionloft API has coordinates tuple as longitude, latitude

import os
import json
import pprint
import requests
import datetime
from dateutil import parser
from dateutil import tz
from dateutil.tz import tzutc

GET_URL = "http://127.0.0.1:8000/api/traffic_data?count=1"
POST_URL = "http://127.0.0.1:8000/api/traffic_data"

API_KEY = os.environ.get('MOTIONLOFT_API_KEY')

API_BASE = "https://dashboard.motionloft.com/api/v1/location"

API_QUERY = "?resource_uid=1608904455254709982&begin=2019-07-29&end=2019-07-30&api_key=" + API_KEY

def check_db(db_url):
    r = requests.get(db_url)
    last_timestamp = None
    try:
        last_timestamp_string = r.json()['readings'][0]['timestamp']
        # debug
        # last_timestamp_string = '2019-01-23T11:16:29.940Z'
        last_timestamp = parser.parse(last_timestamp_string)

    except Exception as err:
        print("[!!] Exception in check_db")
        print(err)

    return last_timestamp

def parse_data(data):
    json_data = data.json()
    # print(len(json_data))
    print(json_data)

    coords = json_data['geometry']['coordinates']
    fixed_coords = [coords[1], coords[0]]
    name = json_data['properties']['name']
    sensor_id = json_data['properties']['id']
    data = json_data['properties']['timeseries']

    n_readings = len(data)
    readings = []
    # from motionloft API docs
    classifications = {1: "person", 2: "bicycle", 3: "car",\
            4: "motorcycle", 5: "bus", 6: "truck"}

    for i in range(n_readings):
        # print(sensor[sensor_id]['data'][i])
        r_time = data[i]['utc']
        count = data[i]['n']
        category = "person"
        if data[i].get("classification"):
            category = classifications[data[i]['classification']]
        reading = {'time': r_time, 'count': count, 'category': category}
        if check_date(r_time):
            readings.append(dict(reading))

    post_readings(sensor_id, name, fixed_coords, readings)

def check_date(date_string):
    check = True
    sp = date_string.split(' ')
    t = sp[0] + 'T' + sp[1] + '+00:00' #readings are utc already
    reading_date = parser.parse(t)
    reading_date = reading_date.replace(tzinfo=tzutc())
    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=tzutc())
    if reading_date > now or abs(now - reading_date) <= datetime.timedelta(hours=1):
        check = False
        print("Future Time! : " + str(reading_date))
    return check


def post_readings(sensor_id, name, coords, readings):
    #pprint.pprint(readings)
    requests.post(POST_URL, json={'id':sensor_id, 'name': name,\
            'coords': coords, 'readings': readings})


def main():
    last_timestamp = check_db(GET_URL)

    start_utc = ""

    if last_timestamp is None:
        print("[!!] No Readings")
        start_utc = (datetime.datetime.now() - datetime.timedelta(hours = 24)).isoformat(sep='T', timespec='seconds')\
            .replace(':', '-').split('T')[0]
    else:
        print("Last stored reading: " + str(last_timestamp))
        ny_zone = tz.gettz('America/New_York')
        local = last_timestamp.astimezone(ny_zone)
        print("LOCAL " + str(local))
        start_utc = local.isoformat(sep='T', timespec='seconds')\
            .split('+')[0].replace(':', '-').split('T')[0]


    print("start time: " + start_utc)
    current_utc = datetime.datetime.now().isoformat(sep='T', timespec='seconds')\
            .replace(':', '-').split('T')[0]

    api_query = F"?resource_uid=1608904455254709982&begin={start_utc}&end={current_utc}&api_key={API_KEY}"

    request_url = API_BASE + api_query

    print("Trying api_url " + request_url)

    data = requests.get(request_url)
    #pprint.pprint(data)

    parse_data(data)


if __name__ == "__main__":
    main()
