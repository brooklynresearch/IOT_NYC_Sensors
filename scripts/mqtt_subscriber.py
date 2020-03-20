import paho.mqtt.subscribe as subscribe

def print_msg(client, userdata, message):
    print("%s : %s" % (message.topic, message.payload))

#topic = "$SYS/#"
topic = "nightlight/pir"
subscribe.callback(print_msg, topic, hostname="18.220.143.195")

