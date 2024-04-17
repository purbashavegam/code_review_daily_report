import paho.mqtt.client as mqtt
import time
import logging
import threading
# import logers
import numpy as np
import vanalytics_helper as v_helper
import vanalytics_data as v_data
from logging_manager import mqtt_logger

class MqttClient(object):
    # log = logers.customLogger(logging.DEBUG)

    def __init__(self, ipAddress, portNumber, username=None, password=None, brokerName=None):
        self.IpAddress = ipAddress
        self.PortNumber = int(portNumber)
        self.Username = username
        self.Password = password
        self.BrokerName = brokerName
        self.Keepalive = 1000
        self.Client = None
        self.isConnected = 0

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            # set flag
            client.connected_flag = True
            self.isConnected = 1
            print("connected OK Returned code=", rc)
        else:
            print("Bad connection Returned code=", rc)

    def on_disconnect(self, client, userdata, rc):
        try:
            mqtt_logger.info("Client disconnected=%s", rc)
            self.isConnected = 0
            client.loop_stop()
            broker_keys = [self.IpAddress + "_" + str(self.PortNumber)]
            v_data.CommonFeatures.connect_subscribe_mqtt(broker_keys)
        except:
            mqtt_logger.error(
                "Exception occurred while disconnecting the broker,Returned code= %s", rc, exc_info=True)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        try:
            pass
        except:
            mqtt_logger.critical(
                "Exception occurred while subscribing the topics", exc_info=True)

    def on_unsubscribe(self, client, userdata, mid):
        try:
            pass
        except:
            mqtt_logger.critical(
                "Exception occurred while unsubscribing the topics", exc_info=True)

    def on_message(self, client, userdata, message):
        try:
            data = [message.topic, message.payload.decode("utf-8")]
            
            v_helper.helper.data_queue.put(data)
        except:
            mqtt_logger.error("Exception occurred while receving message %s", str(
                message.topic), exc_info=True)

    def connect_broker(self):
        clientid = "vegam_analytics_" + str(time.time_ns())
        self.Client = mqtt.Client(clientid, False)

        if self.Username is not None and self.Password is not None:
            self.Username = self.Username.strip()
            self.Password = self.Password.strip()

            if len(self.Username) > 0 and len(self.Password):
                self.Client.username_pw_set(self.Username, self.Password)

        mqtt_logger.info("Connecting to broker at %s:%s",
                      self.IpAddress, self.PortNumber)
        try:
            self.Client.connect(
                self.IpAddress, self.PortNumber, self.Keepalive)
            mqtt_logger.info("Connected")
        except Exception as ex:
            mqtt_logger.error('Failed with error: %s', ex, exc_info=True)

        self.Client.on_connect = self.on_connect
        self.Client.on_subscribe = self.on_subscribe
        self.Client.on_disconnect = self.on_disconnect
        self.Client.on_unsubscribe = self.on_unsubscribe
        self.Client.on_message = self.on_message

        self.Client.loop_start()

    def disconnect_broker(self):
        self.Client.loop_stop()
        # TODO: unsubscribe from here

    def subscribe_topic(self, topics, qos=2):
        for topic in topics:
            self.Client.subscribe(topic, qos)

    def publish_data(self, topic, message, qos=2):
        self.Client.publish(topic, message, qos)
