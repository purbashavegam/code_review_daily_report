
import paho.mqtt.client as mqtt
import time
import json
import threading
import logging
MQTT_TOPIC = [("testTopic1", 0), ("testTopic2", 0), ("testTopic3", 0)]
clients = [
    {"broker": "192.168.1.185", "port": 1883},
    {"broker": "192.168.1.218", "port": 1883},
    {"broker": "192.168.1.102", "port": 5353},
    {"broker": "176.9.144.238", "port": 1883}
]
nclients = len(clients)
message = "test message with new topic"

def multi_loop(nclients, flag=True):
    while flag:
        for i in range(nclients):
            client = clients[i]["client"]
            client.loop(1)

#########
def on_log(client, userdata, level, buf):
    print(buf)

def on_message(client, userdata, message):
    time.sleep(1)
    print("message received ", str(message.payload.decode("utf-8")), message.topic)
    # out_queue.append(msg)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True  # set flag
        for i in range(nclients):
            if clients[i]["client"] == client:
                break

def on_subscribe(client, userdata, mid, granted_qos):
    ## client.subscribe(MQTT_TOPIC)
  #print("subscription success")
  pass

def on_disconnect(client, userdata, rc):
    print("Bad connection Returned code=", rc)
    client.loop_stop()
    # client.unsubscribe(topic)
    print("client disconnected sucessfully")

def on_unsubscribe(client, userdata, mid):
    # client.unsubscribe(MQTT_TOPIC)
    #print("unsubscription success")
    pass

def on_publish(client, userdata, mid):
    time.sleep(1)
    print("In on_pub callback mid= ", mid)

def Create_connections():
    for i in range(nclients):
        cname = "client" + str(i)
        t = int(time.time())
        client_id = cname + str(t)  # create unique client_id
        client = mqtt.Client(client_id)  # create new instance
        clients[i]["client"] = client
        clients[i]["client_id"] = client_id
        clients[i]["cname"] = cname
        broker = clients[i]["broker"]
        port = clients[i]["port"]
        try:
            client.connect(broker, port)  # establish connection
            print("Connected sucessfully to broker ", broker,":",port)
            # client.subscribe(MQTT_TOPIC)
            client.subscribe(MQTT_TOPIC)
            print("Subscribed sucessfully to the Topics",MQTT_TOPIC)
        except:
            print("Connection Failed to broker", broker,":",port)
            client.unsubscribe(MQTT_TOPIC)
            print("Subscribed sucessfully to the Topics",MQTT_TOPIC)

            #client.unsubscribe(MQTT_TOPIC)
            continue
        # client.on_log=on_log #this gives getailed logging
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_disconnect = on_disconnect
        client.on_unsubscribe = on_unsubscribe
        # client.on_publish = on_publish
        client.on_message = on_message
        while not client.connected_flag:
            client.loop(1)  # check for messages
            time.sleep(1)

mqtt.Client.connected_flag = False  # create flag in class
no_threads = threading.active_count()
print("current threads =", no_threads)
print("Creating  Connections ", nclients, " clients")
Create_connections()
t = threading.Thread(target=multi_loop, args=(nclients, True))  # start multi loop
t.start()
print("All clients connected ")
time.sleep(5)
count = 0
no_threads = threading.active_count()
Run_Flag = True
try:
    while Run_Flag:
        i = 0
        for i in range(nclients):
            client = clients[i]["client"]
           
            if client.connected_flag:
                client.subscribe(MQTT_TOPIC)
            else:
                client.unsubscribe(MQTT_TOPIC)
               
                time.sleep(1)
                # print("publishing client " + str(i))
            i += 1
        time.sleep(1)
        count += 1
except KeyboardInterrupt:
    print("interrupted  by keyboard")
# client.loop_stop() #stop loop
for client in clients:
    client.disconnect()
multi_loop(flag=False)  # stop loop
# allow time for allthreads to stop before existing
time.sleep(1)
