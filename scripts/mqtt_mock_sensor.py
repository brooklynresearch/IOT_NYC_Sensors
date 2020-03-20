import time
import datetime
import paho.mqtt.publish as publish

topic = "nightlight/pir"
now = datetime.datetime.now()
message = "node 1 utc " + now.isoformat()
#publish.single(topic, now.isoformat(), hostname="18.220.143.195")
publish.single(topic, message, hostname="127.0.0.1")
