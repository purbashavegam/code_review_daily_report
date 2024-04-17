# -*- coding: utf-8 -*-
import json
from mqtt_json_handler import MqttJsonHandler
import  os
import paho.mqtt.client as mqtt
import threading
import time
import logging
# import sys

__file__ = "F:/Vegam_Office/Code/Test_Mqtt_Config.py"

DIR = os.path.dirname(__file__)

if not DIR:
    FILE_PATH = "Test_Mqtt_Config.json"
else:
    FILE_PATH = DIR + "/Test_Mqtt_Config.json"

with open(FILE_PATH, 'r') as readfile:
    json_dict = json.load(readfile)


class mqtt_connection:
    
    def __init__(self, filepath):#, subscribe_callback):
        
        self.filename = filepath
        self.json_handler_object = None
        self.load_mqtt_settings = self.readfile()
        self.client = mqtt.Client()
        self.client.connected_flag = False
        self.stop_multi_loop = False
        self.broker_address = 'broker_address'
        self.broker_port = 'broker_port'
        self.logger = ""
        self.sensor_dictionary = dict()
        # self.extra_sub_topics = {}
        self.ConfigureSensors =  []
        self.topics = []
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        # self.subscribe_cb = subscribe_callback
        self.start_thread()

    def readfile(self):
        '''
        This function reads the data from the json file
        '''
        try:
            self.json_handler_object = MqttJsonHandler(self.filename)
            self.load_mqtt_settings = self.json_handler_object.read_json()
            return self.load_mqtt_settings
        except ValueError as error:
            raise ValueError from error
    
    def start_thread(self):
        """
        This method creates the multiloop thread.
        """
        self.thread = threading.Thread(
            target=self.multi_loop)  # start multi loop
        time.sleep(1)
        self.thread.start()
    
    def on_connect(self, client, userdata, flags, result_code):
        '''
        Callback to check whether the broker is connected.
        Args:
            client: client name while creating the client
            flags: Tis flag define about the clean session i.e either 0 or 1
            rc: The value of rc determines success or not:
                0: Connection successful
                1: Connection refused - incorrect protocol version
                2: Connection refused - invalid client identifier
                3: Connection refused - server unavailable
                4: Connection refused - bad username or password
                5: Connection refused - not authorised
                6-255: Currently unused.
        '''
        if result_code == 0:
            self.client.connected_flag = True
            self.client.connect(self.broker_address, self.broker_port)
            logging.info("MQTT broker Connected Successful to %s",
                         self.broker_address)
            self.subscribe_topics(self.topics)
        else:
            self.client.connected_flag = False
    
    def on_disconnect(self, client, userdata, result_code):
        '''
        Callback to check when the broker disconnects
        '''
        #pylint: disable=unused-argument
        if result_code != 0:
            self.client.connected_flag = False
            logging.info("MQTT broker %s was disconnected",self.broker_address)
            
    def on_message(self, client, userdata, message):
        self.topics = message.self.topics
        self.message = str(self.message.payload.decode("utf-8"))
        self.message = "Message Recieved" + self.message
        logging.info(self.message)
        
    def subscribe_topics(self):
        '''
        This function subscribes to the topic specified
        Args:
            qos: Quality Of Service i.e it can be either 0,1 or 2
        '''
        subscribe_topics = self.topics
        self.client.on_message = self.subscribe_cb

        for topic in subscribe_topics:
            subscribe_topic = self.ConfigureSensors + '/'+ topic + '#'
            self.client.subscribe(subscribe_topic, qos=0)
            logging.info("Subscribed to topic: %s", subscribe_topic)
    
    

    def reconnect_broker(self):
        """
        Reconnect to the broker when broker details
        are updated
        """
        self.load_mqtt_settings = self.readfile()
        self.on_connect()
    
    def multi_loop(self, flag=True):
        '''
        This function helps to run the client in loop
        Args:
            flag
        '''
        while flag:
            self.client.loop()
            if self.client.connected_flag is False:
                self.on_connect()
                time.sleep(2)
                logging.warning("Reconnecting to MQTT broker %s",
                                self.broker_address)
            if self.stop_multi_loop is True:
                break

    def set_multi_loop_flag(self, boolean):
        '''
        This function is to set the flag for
        multi_loop function
        '''
        self.stop_multi_loop = boolean
    
    def disconnect(self):
        '''
        This function disconnects from client.
        '''
        self.client.disconnect()
      
































