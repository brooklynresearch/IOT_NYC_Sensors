import json
import pprint
import requests
import datetime
import dateutil.parser
from dateutil.tz import tzutc

# SENSOR_ID = "b827eb0fedda" # Wrong one. For Testing
SENSOR_ID = "b827eb252949" # closest one
SENSOR_ID_39 = "b827eb74a9e8"
ID_NUMS = {SENSOR_ID: 827, SENSOR_ID_39: 888} # needs number for id

get_url = 'http://127.0.0.1:8000/api/sound_data?count=1'
post_url = 'http://127.0.0.1:8000/api/sound_data'

api_url = "http://citsci-sonyc.engineering.nyu.edu:5000/"

def check_db(db_url):
    r = requests.get(db_url)
    last_timestamp = None
    try:
        readings = r.json()['readings']
        for reading in readings:
            date = dateutil.parser.parse(reading['timestamp'])
            if last_timestamp == None or date < last_timestamp:
                last_timestamp = date

    except Exception as err:
        print("[!!] Exception in check_db")
        print(err)

    return last_timestamp

def parse_data(data):
    # json_data = data.json()
    # print(len(json_data))
    pprint.pprint(data)
    sensor_id = list(data)[0]
    coords = [data['lat'], data['lon']]
    # for sensor in json_data:
    n_readings = len(data[sensor_id]['index'])
    readings = []
    for i in range(n_readings):
        # print(sensor[sensor_id]['data'][i])
        r_time = data[sensor_id]['index'][i]
        values = data[sensor_id]['data'][i]
        reading = {'timestamp': r_time, 'sensor_id': ID_NUMS[sensor_id], 'name': sensor_id,\
                'latitude': coords[0], 'longitude': coords[1], 'L10': values[0],\
                'L5': values[1], 'L50': values[2], 'L90': values[3], 'davg': values[4],\
                'dmax': values[5], 'dmin': values[6]}
        readings.append(dict(reading))

    post_readings(sensor_id, readings)

def post_readings(sensor_id, readings):
    requests.post(post_url, json={'readings': readings})


def main():
    last_timestamp = check_db(get_url)

    if last_timestamp is None:
        print("[!!] No readings in database")
        last_timestamp = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    else:
        print("Last stored reading: " + str(last_timestamp))

    start_utc = last_timestamp.isoformat(sep='T', timespec='seconds')\
            .split('+')[0].replace(':', '-')
    current_utc = datetime.datetime.utcnow().isoformat(sep='T', timespec='seconds')\
            .replace(':', '-')

    api_query = F"sonycdata?range={start_utc}:{current_utc}&sensors={SENSOR_ID},{SENSOR_ID_39}&granularity=hour"

    request_url = api_url + api_query

    print("Trying api_url " + request_url)

    data = requests.get(request_url)
    # print(data)

    json_data = data.json()
    for sensor in json_data:
        parse_data(sensor)
        print('\n\n')


if __name__ == "__main__":
    main()
