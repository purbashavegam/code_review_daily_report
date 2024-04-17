

import paho.mqtt.client as mqtt
import time
import json
import threading
import logging
#### this class connects and disconnects multiple brokers, also once connected it subscribes and unsubscribes to multiple topics,messages are stored in a queue
class MQTT_Connection:
    
    def __init__(self, Broker_Info, Test_Topic):
        self.client = mqtt.Client()
        self.broker_info = Broker_Info
        self.sensor_topics = Test_Topic
        self.stop_multi_loop = False
        self.client.connected_flag = False
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.subscribe = self.subscribe
        self.client.unsubscribe = self.unsubscribe
        self.connect_broker()
        self.start_thread()
    
    def start_thread(self):
        """
        This method creates the multiloop thread.
        """
        self.thread = threading.Thread(
            target=self.multi_loop)  # start multi loop
        time.sleep(1)
        self.thread.start()
        logging.info("Thread Started")
        
    def connect_broker(self):
        '''
        This function connects to the broker using the broker details
        Args:
            broker: Broker ip address
            port: Broker port number
        '''
        for self.bkr in range(len(self.broker_info)):
            if (self.broker_info[self.bkr]['broker'] != "None" and
                self.broker_info[self.bkr]['port'] != "None"):
                try:
                    self.client.connect(self.broker_info[self.bkr]['broker'],
                                        self.broker_info[self.bkr]['port'])
                except OSError:
                    logging.info("Error Raised : Waiting for reconnection")
            else:
                raise ValueError("Invalid Details")
    
    def on_connect(self, client, userdata, flags, rc):
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
        if rc == 0:
            self.client.connected_flag = True
            
            logging.info("MQTT broker Connected Successful to %s",
                         self.broker_info[self.bkr]['broker'])
            # self.subscribe_data()
        else:
            self.client.connected_flag = False
            logging.info("MQTT broker is not Connected to %s",
                         self.broker_info[self.bkr]['broker'])
            
    def on_disconnect(self, client, userdata, rc):
        '''
        Callback to check when the broker disconnects
        '''
        #pylint: disable=unused-argument
        if rc != 0:
            self.client.connected_flag = False
            logging.info("MQTT broker %s was disconnected",
                         self.broker_info[self.bkr]['broker'])
            
    def publish(self, topic, message, qos=0):
        '''
        This function publish the data to the topic specified
        Args:
            topic: Topic on which data to be published
            message: contains the message to be published
            qos: Quality Of Service i.e it can be either 0,1 or 2
        '''
        if self.client.connected_flag is True:
            self.client.publish(payload=message, qos=qos, topic=topic)
            return True
        return False
    
    def publish_raw_data(self, sensor_id, data_type, raw_data, qos=0):
        '''
        This function publish the data to the topic specified
        Args:
            data_type: Type of raw data that has to be published
            raw_data: contains the raw_data to be published
            qos: Quality Of Service i.e it can be either 0,1 or 2
        '''
        if self.client.connected_flag is True:
            topic = self.sensor_topic
            publish_message = json.dumps(raw_data)
            self.client.publish(payload=publish_message, qos=qos, topic=topic)
            return True
        return False
        
    def subscribe(self, client, userdata, mid, granted_qos):
        '''
        This function subscribe to the topic specified
        '''
        subscribe_topics = self.sensor_topics
        try:
            for topic in subscribe_topics:
                self.sensor_topic = topic
                self.client.subscribe(self.sensor_topic, qos=0)
        except:
            logging.info("Subscribed to topic: %s", self.sensor_topic)
        ## client.subscribe(MQTT_TOPIC)
        #print("subscription success")
        # pass
    def on_message(self, client, obj, msg):
        '''
        This function subscribe to the topic specified
        '''
        try:
            self.client.on_message = self.on_message
            self.queue.append(tuple((msg.topic,msg.payload.decode("utf-8")))) ##contains the total data coming from topics
        except:
            logging.info(msg.self.sensor_topic+" "+str(msg.qos)+" "+str(msg.payload))
        
    def unsubscribe(self, client, userdata, mid):
        '''
        This function Unsubscribe to the topic specified
        '''
        try:
            self.client.unsubscribe(self.sensor_topic)
        except:            
            logging.info("Unsubscribed to topic: %s", self.sensor_topic)
        #print("unsubscription success")
        # pass
    
    def multi_loop(self, flag=True):
        '''
        This function helps to run the client in loop
        Args:
            flag
        '''
        while flag:
            self.client.loop()
            if self.client.connected_flag is False:
                self.connect_broker()
                time.sleep(2)
                logging.warning("Reconnecting to MQTT broker %s",
                                self.broker_info[self.bkr]['broker'])
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
            
    
        
        
        
        
        
        
        
