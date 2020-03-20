from datetime import datetime, timedelta, timezone
from dateutil import parser
from dateutil.tz import tzutc
from django.shortcuts import render
from django.core import serializers
from django.db.models import F
from django.db import connection
import json
from django.http import JsonResponse

from .models import Sensor, AirQualityReading, PedCountReading, SoundReading, TrafficReading

def convert_to_utc(timestring, b_convert):
    t = parser.parse(timestring)

    if b_convert:
        t = t + timedelta(hours=5)

    t = t.replace(tzinfo=tzutc())

    return t

def save_air_data(data):
    count = 0
    for reading in data:

        utc_timestamp = convert_to_utc(reading['updateTime'], True)
        #is the sensor itself new?
        stored = Sensor.objects.filter(sensor_type="air", external_id=reading['siteID'])
        if len(stored) == 0:
            #save the sensor info first
            s = Sensor(external_id=reading['siteID'], name=reading['site'], sensor_type="air",\
                    latitude=reading['latitude'], longitude=reading['longitude'], latest_reading=utc_timestamp)
            s.save()
            stored = Sensor.objects.filter(external_id=reading['siteID'])

        #check if we've already saved this reading
        duplicates = AirQualityReading.objects.filter(site=reading['site'], timestamp=utc_timestamp)
        if len(duplicates) == 0:
            r = AirQualityReading(sensor=stored[0], timestamp=utc_timestamp, site=reading['site'], location=reading['location'],\
                    address=reading['address'], current_PM25=reading['current_PM25'], roll_PM25=reading['roll_PM25'], bldgarea_c=reading['bldgarea_c'],\
                    traffic_cl=reading['traffic_cl'])
            r.save()

            if utc_timestamp > stored[0].latest_reading:
                stored[0].latest_reading = utc_timestamp
                stored[0].save()
            count += 1

    print(str(count) + " air readings saved.")


def save_pedcount_data(data):
    print("got pedcount reading: " + str(data))

    utc_timestamp = convert_to_utc(data['timestamp'], False)
    #is the sensor itself new?
    stored = Sensor.objects.filter(sensor_type="pedcount", external_id=int(data['sensor_id']))
    if len(stored) == 0:
        #save the sensor info first
        s = Sensor(external_id=data['sensor_id'], name=data['name'], sensor_type="pedcount",\
                latitude=data['latitude'], longitude=data['longitude'], latest_reading=utc_timestamp)
        s.save()
        stored = Sensor.objects.filter(external_id=data['sensor_id'])

    r = PedCountReading(sensor=stored[0], timestamp=utc_timestamp, count=data['value'])
    r.save()
    if utc_timestamp > stored[0].latest_reading:
        stored[0].latest_reading = utc_timestamp
        stored[0].save()

    print("Saved PedCount reading for sensor: " + str(data['sensor_id']))

def save_sound_data(data):
    print("got sound data: " + str(data))
    count = 0
    readings = data['readings']
    for reading in readings:
        utc_timestamp = convert_to_utc(reading['timestamp'], False)

        #is the sensor itself new?
        stored = Sensor.objects.filter(sensor_type="sound", external_id=int(reading['sensor_id']))
        if len(stored) == 0:
            #save the sensor info first
            s = Sensor(external_id=reading['sensor_id'], name=reading['name'], sensor_type="sound",\
                    latitude=reading['latitude'], longitude=reading['longitude'], latest_reading=utc_timestamp)
            s.save()
            stored = Sensor.objects.filter(external_id=reading['sensor_id'])

        #check if we've already saved this reading
        duplicates = SoundReading.objects.filter(timestamp=utc_timestamp, sensor_id=stored[0].id)
        if len(duplicates) == 0:
            r = SoundReading(sensor=stored[0], timestamp=utc_timestamp, davg=reading['davg'], dmin=reading['dmin'],\
                    dmax=reading['dmax'], d_l10=reading['L10'], d_l50=reading['L50'], d_l90=reading['L90'])
            r.save()

            if utc_timestamp > stored[0].latest_reading:
                stored[0].latest_reading = utc_timestamp
                stored[0].save()
            count += 1

    print(str(count) + " sound readings saved.")

def save_traffic_data(data):
    print(data)
    sensor_id = data['id']
    sensor_name = data['name']
    sensor_coords = data['coords']
    readings = data['readings']
    cnt = 0
    for reading in readings:
        category = reading.get('category')
        plurals = {"person": "People", "bicycle" : "Bicycles",\
                "car" : "Cars", "bus": "Buses", "truck": "Trucks"}
        if category:
            sensor_name = data['name'] + ' ' + plurals[category]
            sensor_id = data['id'] + ord(category[0])
        sp = reading['time'].split(' ')
        t = sp[0] + 'T' + sp[1] + '+00:00' #readings are utc already
        utc_timestamp = convert_to_utc(t, False)
        print("[!!!] UTC " + str(utc_timestamp))
        #is the sensor itself new?
        stored = Sensor.objects.filter(sensor_type="traffic", external_id=sensor_id)
        if len(stored) == 0:
            #save the sensor info first
            s = Sensor(external_id=sensor_id, name=sensor_name, sensor_type="traffic",\
                    latitude=sensor_coords[0], longitude=sensor_coords[1], latest_reading=utc_timestamp)
            s.save()
            stored = Sensor.objects.filter(external_id=int(sensor_id))

        #check if we've already saved this reading
        duplicates = TrafficReading.objects.filter(timestamp=utc_timestamp)
        if len(duplicates) == 0:
            r = TrafficReading(sensor=stored[0], timestamp=utc_timestamp, count=reading['count'])
            r.save()

            if utc_timestamp > stored[0].latest_reading:
                stored[0].latest_reading = utc_timestamp
                stored[0].save()
            cnt += 1
        else: # Allow values to up updated if needed
            if not (duplicates[0].count == reading['count']):
                db_reading = duplicates[0]
                db_reading.count = reading['count']
                db_reading.save()

    print(str(cnt) + " sound readings saved.")

def getPedCountData(request):
    '''
    Needs special handler to group into 15 min intervals
    '''

    sensors = Sensor.objects.filter(sensor_type='pedcount')

    count = int(request.GET.get('count', 0))
    r_days = int(request.GET.get('days', 0))
    start = str(request.GET.get('start', ''))
    end = str(request.GET.get('end', ''))

    readings = []
    if r_days > 0:
        sensor_id = int(request.GET.get('sensor_id', 0))
        if sensor_id > 0:
            sensors = sensors.filter(id=sensor_id)
        for s in sensors:
            raw_query = "SELECT SUM(count) hr_count, sensor_id, to_timestamp(floor((extract('epoch' from timestamp) / 900 )) * 900)"+\
                    " at time zone 'UTC' as t_interval from api_pedcountreading where sensor_id = %s and timestamp > %s group by (t_interval, sensor_id)"+\
                    " order by t_interval desc;"

            sensor_id = s.id
            date_string = (s.latest_reading - timedelta(days=r_days)).isoformat()
            # readings += MotionReading.objects.raw(raw_query, [sensor_id, date_string])
            cursor = connection.cursor()
            try:
                cursor.execute(raw_query, [sensor_id, date_string])
                readings += cursor.fetchall()
            finally:
                cursor.close()

    elif start and end:
        start_date = parser.parse(start)
        end_date = parser.parse(end)
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()
        raw_query = "SELECT SUM(count) hr_count, sensor_id, to_timestamp(floor((extract('epoch' from timestamp) / 900 ))"+\
                    " * 900) at time zone 'UTC' as t_interval from api_pedcountreading where sensor_id = %s and timestamp >= %s and timestamp <= %s"+\
                    "group by (t_interval, sensor_id) order by t_interval desc;"

        for s in sensors:
            sensor_id = s.id

            cursor = connection.cursor()
            try:
                cursor.execute(raw_query, [sensor_id, start_iso, end_iso])
                readings += cursor.fetchall()
            finally:
                cursor.close()

    def format_time(t):
        return t.replace(tzinfo=tzutc()).isoformat()

    reading_list = [{'timestamp': format_time(r[2]), 'count': r[0], 'sensor_id': r[1]} for r in readings]
    return {'readings': reading_list, 'sensors': list(sensors.values())}


def getData(s_type, request):
    s_types = list(Sensor.objects.distinct('sensor_type').values('sensor_type'))
    type_list = [t['sensor_type'] for t in s_types]

    if s_type not in type_list:
        return {}

    sensors = Sensor.objects.filter(sensor_type=s_type)

    count = int(request.GET.get('count', 0))
    r_days = int(request.GET.get('days', 0))
    start = str(request.GET.get('start', ''))
    end = str(request.GET.get('end', ''))

    query_begin = s_type + '_readings'
    if count > 0:
        query_string = '.order_by("-timestamp").values()[:' + str(count) + ']'

    elif r_days > 0:
        sensor_id = int(request.GET.get('sensor_id', 0))
        if sensor_id > 0:
            sensors = sensors.filter(id=sensor_id)

        query_string = '.filter(timestamp__gt=s.latest_reading - timedelta(days='+ str(r_days) +\
                ')).order_by("-timestamp").values()'

    elif start and end:
        start_date = parser.parse(start)
        end_date = parser.parse(end)
        print("Query Date Range: " + str(start_date) + ' - ' + str(end_date))

        query_string = '.filter(timestamp__gte=start_date,timestamp__lte=end_date)'+\
                '.order_by("-timestamp").values()'


    readings = []
    for s in sensors:
        readings += eval('s.' + query_begin + query_string)

    # print("READINGS: " + str(readings))
    return {'readings': list(readings), 'sensors': list(sensors.values())}

def get_sensor_types():
    sensors = Sensor.objects.distinct('sensor_type').values('sensor_type')
    return {'sensor_types': [s['sensor_type'] for s in sensors]}


# Create your views here.
def sensor_types(request):
    if request.method == 'GET':
        db_data = get_sensor_types()
        return JsonResponse(db_data, safe=False)

def air_data(request):
    if request.method == 'POST':
        json_data = request.body
        data = json.loads(json_data)
        print("Received air quality readings: " + str(data[0]))
        save_air_data(data)
        return JsonResponse(['OK'], safe=False)

    elif request.method == 'GET':
        db_data = getData("air", request)
        return JsonResponse(db_data, safe=False)

def sound_data(request):
    if request.method == 'POST':
        json_data = request.body
        data = json.loads(json_data)
        print("Got sound data: " + str(data))
        save_sound_data(data)
        return JsonResponse(['OK'], safe=False)

    elif request.method == 'GET':
        db_data = getData("sound", request)
        return JsonResponse(db_data, safe=False)

def pedcount_data(request):
    if request.method == 'POST':
        json_data = request.body
        data = json.loads(json_data)
        save_pedcount_data(data)
        return JsonResponse(['OK'], safe=False)

    elif request.method == 'GET':
        db_data = getPedCountData(request)
        return JsonResponse(db_data, safe=False)

def traffic_data(request):
    if request.method == 'POST':
        json_data = request.body
        data = json.loads(json_data)
        save_traffic_data(data)
        return JsonResponse(['OK'], safe=False)

    elif request.method == 'GET':
        db_data = getData("traffic", request)
        return JsonResponse(db_data, safe=False)
