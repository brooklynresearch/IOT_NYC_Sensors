import time
import paho.mqtt.publish as publish

#EX: "sensors/1/data"
topic = "sensors/1"
while True:
    publish.single(topic, "TIME", hostname="127.0.0.1")
    time.sleep(3)
