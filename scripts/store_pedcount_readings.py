import requests
import datetime
import paho.mqtt.subscribe as subscribe

sensors = {}
sensors['1'] = [40.668738, -73.908694, 'Pole #1']
sensors['2'] = [40.668640, -73.909362, 'Pole #2']
sensors['3'] = [40.668587, -73.909032, 'Pole #3']
sensors['4'] = [40.668827, -73.908103, 'Pole #4']
sensors['5'] = [40.668778, -73.907747, 'Pole #5']

def print_msg(message):
    print("%s : %s" % (message.topic, message.payload))

def save_data(message):
    msg = str(message.payload, 'utf-8')
    print("Got pir: %s" % (msg))

    split = msg.split(" ")
    print("sensor {}: {}".format(split[1], split[3]))
    data = {}
    sensor_id = split[1]
    timestamp = split[3]
    data['sensor_id'] = sensor_id
    data['timestamp'] = timestamp
    data['latitude'] = sensors[sensor_id][0]
    data['longitude'] = sensors[sensor_id][1]
    data['value'] = 1
    data['name'] = sensors[sensor_id][2]
    print("DATA:" + str(data))
    response = requests.post('http://127.0.0.1:8000/api/pedcount_data', json=data)
    print(response)

def save_pulse(message):
    msg = str(message.payload, 'utf-8')
    print("Got pulse: " + msg)
    split = msg.split(" ")
    sensor_id = split[1]
    data = {}
    data['sensor_id'] = sensor_id
    data['timestamp'] = datetime.datetime.now().isoformat()
    data['latitude'] = sensors[sensor_id][0]
    data['longitude'] = sensors[sensor_id][1]
    data['value'] = 0
    data['name'] = sensors[sensor_id][2]
    print("DATA:" + str(data))
    response = requests.post('http://127.0.0.1:8000/api/pedcount_data', json=data)
    print(response)

def parse_msg(client, userdata, message):
    try:
        print("%s : %s" % (message.topic, message.payload))
        topic = str(message.topic)
        if topic == 'nightlight/pir':
            save_data(message)
        elif topic == "nightlight/pulse":
            save_pulse(message)
    except Exception as e:
        print("Exception: " + str(e))
    finally:
        print("\n")

def main():
    topic = "nightlight/#"
    print("Subscribing to nightlight/#")
    # subscribe.callback(parse_msg, topic, hostname="18.220.143.195")
    subscribe.callback(parse_msg, topic, hostname="127.0.0.1")

if __name__ == "__main__":
    main()
