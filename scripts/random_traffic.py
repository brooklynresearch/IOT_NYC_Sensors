import json
import requests
import random
from datetime import datetime
from dateutil.tz import tzutc

#[latitude, longitude, name]
sensors = {}
sensors['1'] = {'lat': 40.6689742, 'long': -73.906674, 'name': 'Belmont & Mother Gaston'}
sensors['2'] = {'lat': 40.6692515, 'long':  -73.9047691, 'name': 'Belmont & Sackman St'}
sensors['3'] = {'lat': 40.6695376, 'long': -73.9029402, 'name': 'Belmont & Junius St'}

def post_data(sensor_id, timestamp):
    print("sensor {}: {}".format(sensor_id, sensors[sensor_id]['name']))

    data = {}
    data['sensor_id'] = sensor_id
    data['timestamp'] = timestamp
    data['latitude'] = sensors[sensor_id]['lat']
    data['longitude'] = sensors[sensor_id]['long']
    data['name'] = sensors[sensor_id]['name']

    #json_data = json.dumps([data])
    #print(json_data)
    requests.post('http://127.0.0.1:8000/api/motion_data', json=data)

    return

def main():
    r = random.randint(0,100)
    print("randint: " + str(r))
    if r <= 25: #25% chance of doing something
        print("Doing something")
        sensor_id = random.randint(1,3)
        t = datetime.now().astimezone(tzutc()).isoformat()
        post_data(str(sensor_id), t)

main()

