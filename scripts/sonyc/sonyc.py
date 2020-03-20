import tarfile
import pandas as pd
import numpy as np
import datetime
import sys
import os
import boto3
import json
import requests
import dateutil.parser
from dateutil.tz import tzutc

init_file = 'b827eb74a9e8_1547014589.94_data.tar'
latitude = 40.755334
longitude = -73.9933657
sitename = "sonyc-39th"
sensor_id = 39
get_url = 'http://127.0.0.1:8000/api/sound_data?count=1'
post_url = 'http://127.0.0.1:8000/api/sound_data'
# post_url = 'http://192.168.86.41:8000/api/sound_data'

REGION_NAME = 'us-east-1'
BUCKET_NAME = 'sonyc-39th'
base_prefix = 'spl/sonycnode-b827eb2a1bce.sonyc/'
tar_directory = 'temp_tar'
csv_directory = 'temp_csv'

def check_db(db_url):
    r = requests.get(db_url)
    last_timestamp = None
    try:
        last_timestamp_string = r.json()['readings'][0]['timestamp']
        # debug
        # last_timestamp_string = '2019-01-23T11:16:29.940Z'
        last_timestamp = dateutil.parser.parse(last_timestamp_string)

    except Exception as e:
        print("[!!] Exception in check_db")
        print(e)

    return last_timestamp

def perdelta(start, end, delta):
    curr = start
    while curr <= end:
        yield curr
        curr += delta

def check_bucket(last_check):

    client = boto3.client('s3', region_name=REGION_NAME)
    paginator = client.get_paginator('list_objects_v2')

    current_date = datetime.datetime.now().replace(tzinfo=tzutc())
    print("[+] Checking for new sound data at " + str(current_date))

    retrieval_list = []

    # create list of dates from last checked date to current date
    for search_date in perdelta(last_check.date(), current_date.date(), datetime.timedelta(days=1)):
        print("[+] Searching date: " + str(search_date))
        search_prefix = base_prefix + search_date.strftime('%Y-%m-%d')
        operation_parameters = {'Bucket': BUCKET_NAME, 'Prefix': search_prefix}

        print("[+] RETRIEVING OBJECTS: " + search_prefix)

        page_iterator = paginator.paginate(**operation_parameters)

        try:
            for page in page_iterator:
                if page['KeyCount'] > 0:
                    for entry in page['Contents']:
                        filename = entry['Key'].split('/')[-1]
                        unixtime = float(filename.split("_")[1].split("_")[0])
                        if unixtime > last_check.timestamp():
                            retrieval_list.append(entry['Key'])
        except Exception as e:
            print("[!!] Exception in check_bucket")
            print(e)
            pass

    return retrieval_list


def download_files(retrieval_list):
    s3 = boto3.resource('s3')

    for each in retrieval_list:
        try:
            print("[+] Downloading File: " + each)
            s3.Bucket(BUCKET_NAME).download_file(each, tar_directory + '/' + each.split('/')[-1])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("[!!] The object does not exist.")
            else:
                raise

def process_tar(tarfilename):

    filename = None

    try:
        tar = tarfile.open(tarfilename)
        files = tar.getmembers()

        for each in files:
            if "slow" in each.name:
                filename = each.name
                break

        tar.extract(filename, path=csv_directory)

    except Exception as e:
        print("[!!] Exception in process_tar")
        print(e)
        pass

    return filename

def get_time(filename):
    unixtime = float(filename.split("_")[1].split("_")[0])
    readable = datetime.datetime.fromtimestamp(unixtime).astimezone(tzutc()).isoformat()
    return readable

def process_csv(csv_file):
    values = None
    try:
        df = pd.read_csv(csv_directory + "/" + csv_file)
        saved_column = df['dBAS']
        values = {}
        values['davg'] = calculate_avg(saved_column)
        values['dmin'] = min(saved_column)
        values['dmax'] = max(saved_column)
        values['L10'] = calcbg(saved_column, 10)
        values['L50'] = calcbg(saved_column, 50)
        values['L90'] = calcbg(saved_column, 90)
    except Exception as e:
        print("[!!] Exception in process_csv")
        print(e)
        pass

    return values

def calculate_avg(dBAS):
    levels = np.asanyarray(dBAS)
    return 10.0 * np.log10((10.0**(levels/10.0)).mean(None))

def calcbg(data, percentile_value):
    stat_percentile = 100 - percentile_value
    return np.nanpercentile(data, stat_percentile)

def delete_file(filename, tarfilename):
    os.remove(filename)
    os.remove(tarfilename)

def main():
    last_timestamp = check_db(get_url)

    if last_timestamp is None:
        print("[!!] Unable to receive from database")

    else:

        retrieval_list = check_bucket(last_timestamp)
        download_files(retrieval_list)

        for each in retrieval_list:
            tarfilename = tar_directory + "/" + each.split('/')[-1]
            filename = process_tar(tarfilename)
            timestamp = get_time(filename)
            values = process_csv(filename)
            if values is None:
                print("No values!")
                pass
            else:
                values['sensor_id'] = sensor_id
                values['name'] = sitename
                values['timestamp'] = timestamp
                values['latitude'] = latitude
                values['longitude'] = longitude
                data = [values]
                # print(data)
                requests.post(post_url, json=data)
                delete_file(csv_directory + '/' + filename, tarfilename)


if __name__ == '__main__':
    # if len(sys.argv) > 1:
    # tarfilename = init_file
    # main(tarfilename)
    main()
    # else:
        # check_bucket()

