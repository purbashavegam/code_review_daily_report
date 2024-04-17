import enum
import time
import logging
import ssl
import paho.mqtt.client as mqtt
from Scripts.Trending.alert.MqttJsonHandler import AnalyticsJsonHandler
# from MqttJsonHandler import AnalyticsJsonHandler  # Make sure to import this correctly
import threading
# Define a logger for MQTT subscribe/publish
mqtt_subscribe_publish_logger = logging.getLogger("mqtt_subscribe_publish")

TLS_VERSION_TLSv1_2 = "tlsv1.2"

class TrendsMqtt:
    class TopicEnum(enum.Enum):
        log_details = "LogDetails"
        failure_msg = "FailureMessage"
        device_info = "DeviceInfoData"

    class LoggingLevels(enum.Enum):
        debug = "debug"
        info = "info"
        warning = "warning"
        error = "error"
        critical = "critical"

    def __init__(self, filename, subscribe_callback, connect_success_cb=None, service_name=None):
        try:

            self.json_handler_object = None
            self.filename = filename
            self.service_name = service_name
            self.load_mqtt_settings = self.readfile()
            # self.client = mqtt.Client() #og
            self.client = mqtt.Client(clean_session=True, transport='tcp') #pm checks
            self.extra_sub_topics = {}
            self.stop_multi_loop = False
            self.client.connected_flag = False
            self.trends_key = "Mqtt"
            self.broker_key = "broker_details"
            self.microservice_name = self.load_mqtt_settings[self.trends_key]['microservice_name']
            # print(self.microservice_name,self.service_name,"-------------purbasha prints-------------------")
            # Velo_fft_microservice
            # AnalyticsMQTT - ------------purbasha
            # prints - ------------------

            self.broker_cert_loc = "C:\\VELO_FFT_service\\cert_40"#"C:\\VELO_FFT_service\\cert"  # "cert"
            # self.broker_cert_loc = "/usr/local/ssl_certificates/"
            self.connect_success_cb = connect_success_cb
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.subscribe_cb = subscribe_callback
            self.connect_success_cb = connect_success_cb
            self.logging_dict = {self.LoggingLevels.debug.value: logging.debug,
                                 self.LoggingLevels.info.value: logging.info,
                                 self.LoggingLevels.warning.value: logging.warning,
                                 self.LoggingLevels.error.value: logging.error,
                                 self.LoggingLevels.critical.value: logging.critical}
            self.configure_ssl()
            self.connect_broker()
            self.start_thread()
        except Exception as e:
            logging.error(f"An error occurred during initialization in mqtt class: {str(e)}")

    def start_thread(self):
        try:

            """
            This method creates the multiloop thread.
            """
            self.thread = threading.Thread(
                target=self.multi_loop, name="MqttConnectionThread")  # start multi loop
            time.sleep(1)
            self.thread.start()
        except Exception as e:
            logging.error(f"An error occurred in start_thread: {str(e)}")

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload = message.payload.decode("utf-8")
            print(f"Received message on topic '{topic}': {payload}")
        except Exception as e:
            logging.error(f"An error occurred in on_message: {str(e)}")

    def readfile(self):
        try:
            self.json_handler_object = AnalyticsJsonHandler(self.filename) # how to pass "Mqtt" key dynamically need to check -> pm
            load_mqtt_settings = self.json_handler_object.read_json()
            print("Loaded JSON data:", load_mqtt_settings)  # Debugging line
            return load_mqtt_settings
        except ValueError as error:
            raise ValueError from error
        except Exception as e:
            logging.error(f"An error occurred in readfile: {str(e)}")

    def configure_ssl(self):
        try:
            if self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_enabled'] == 1:
                ca_cert = self.broker_cert_loc + "/" + self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_details'][
                    'ca_certificate']
                # print("ca_cert path:", ca_cert)

                client_cert = self.broker_cert_loc + "/" + self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_details'][
                    'client_certificate']
                client_key = self.broker_cert_loc + "/" + self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_details'][
                    'client_key_file']
                # print("client_cert path:", client_cert)
                # print("client_key path:", client_key)
                # --pm check---

                # self.client.tls_set(ca_certs=ca_cert, certfile=client_cert, keyfile=client_key,
                #                     tls_version=TLS_VERSION_TLSv1_2,
                #                     keyfile_password=self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_details'][
                #                         'keyfile_password'])

                tls_context = ssl.create_default_context()
                tls_context.load_verify_locations(cafile=ca_cert)
                tls_context.load_cert_chain(certfile=client_cert, keyfile=client_key)
                self.client.tls_set_context(tls_context)
                # --pm check---

                # self.client.tls_set(ca_certs=ca_cert, certfile=client_cert, keyfile=client_key,
                #                     tls_version=ssl.PROTOCOL_TLSv1_2,
                #                     keyfile_password=self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_details'][
                #                         'keyfile_password'])
                #
                # self.client.tls_insecure_set(True)

                payload_msg = "Configured ssl - [with new ssl code] for mqtt broker at %s" % (time.time())
                logging.info(payload_msg)
        except ValueError as error:
            err_msg = "Failed to configure ssl," \
                      "at %s, error: %s" % (
                          time.time(), error.args[0])
            logging.error(err_msg)
        except Exception as e:
            logging.error(f"An error occurred in configure_ssl: {str(e)}")

    def connect_broker(self):
        try:
            '''
            This function connects to the broker using the broker details
            Args:
                broker_username: Broker username
                broker_password: Broker password
                broker_ip: Broker ip address
                broker_port: Broker port number
            '''
            logging.info("Trying to connect broker")
            if (self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_username'] != "None" and
                    self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_password'] != "None"):
                self.client.username_pw_set(
                    username=self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_username'],
                    password=self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_password']
                )

            if (self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'] != "None" and
                    self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_port'] != "None"):
                try:
                    self.client.connect(self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'],
                                        self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_port'],keepalive=25)  # keepalive
                    logging.info("broker connected...")
                except Exception as err:
                    logging.error("Error Raised : Waiting for reconnection")
                    err_msg = "%s: Error Raised %s: Waiting for reconnection at %s" % \
                              (self.microservice_name, err, time.time())

                    logging.error(err_msg)
            else:
                raise ValueError("Invalid Details")
        except Exception as e:
            logging.error(f"An error occurred in connect_broker: {str(e)}")

    def on_connect(self, client, userdata, flags, result_code):
        try:
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
            # pylint: disable=unused-argument
            if result_code == 0:
                self.client.connected_flag = True
                payload_msg = "%s: MQTT broker Connected Successful to %s at %s" % (
                    self.microservice_name, self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'], time.time())
                logging.info(payload_msg)
                self.subscribe_extra_topics()
                if self.connect_success_cb is not None:
                    self.connect_success_cb()
            else:
                self.client.connected_flag = False
        except Exception as e:
            logging.error(f"An error occurred in on_connect: {str(e)}")

    def on_disconnect(self, client, userdata, result_code):
        try:
            '''
            Callback to check when the broker disconnects
            '''
            # pylint: disable=unused-argument
            # if result_code == 7:
            #     logging.info("rc is" + str(result_code))
            #     self.reconnect()  # pm add

            if result_code != 0:
                self.client.connected_flag = False
                payload_msg = "%s: MQTT broker %s was disconnected at %s" % (
                    self.service_name, self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'], time.time())
                logging.info(payload_msg)
                logging.info("rc is" + str(result_code))
                logging.info("reconnecting..")

                # Reconnect when disconnection occurs
                # self.reconnect()
                self.client.reconnect()  # pm add
                # self.reconnect_broker()
                logging.info("reconnection done..")
        except Exception as e:
            logging.error(f"An error occurred in on_disconnect: {str(e)}")

    def publish(self, topic, message, qos=2):
        try:  # prev qos = 0
            '''
            This function publish the data to the topic specified
            Args:
                topic: Topic on which data to be published
                message: contains the message to be published
                qos: Quality Of Service i.e it can be either 0,1 or 2
            '''
            return_value = False
            res = None
            if self.client.connected_flag is True:
                res = self.client.publish(payload=message, qos=qos, topic=topic)
                return_value = True
            return (return_value, res)
        except Exception as e:
            logging.error(f"An error occurred in publish: {str(e)}")

    def add_subscribe_data(self, topic, message_callback):
        try:
            if topic not in self.extra_sub_topics:
                # print("----------------------------------------------------")
                # print(topic,message_callback,"--------------------------------")
                # print("----------------------------------------------------")
                dict1 = {}
                dict1[topic] = message_callback
                self.extra_sub_topics.update(dict1)
                if self.client.connected_flag is True:
                    try:
                        self.client.message_callback_add(topic, message_callback)
                        self.client.subscribe(topic, qos=0)
                        payload_msg = "%s: Subscribed to topic: %s at %s" % (
                            self.service_name, topic, time.time())
                        logging.info(payload_msg)
                    except Exception as error:
                        payload_msg = "%s: Exception occurred, Error: %s at %s" % (
                            self.service_name, error, time.time())
                        logging.info(payload_msg)  # new add
            else:
                print("assert error")
                raise AssertionError(
                    "Topic already exists in extra_sub_topics,same topic can't be added again")  # new add
        except Exception as e:
            logging.error(f"An error occurred in add_subscribe_data: {str(e)}")

    def subscribe_extra_topics(self):
        try:

            for topic, callback in self.extra_sub_topics.items():
                try:
                    self.client.message_callback_add(topic, callback)
                    self.client.subscribe(topic, qos=0)
                    payload_msg = "%s: Subscribed to topic: %s at %s" % (
                        self.service_name, topic, time.time())
                    logging.info(payload_msg)
                except Exception as error:
                    payload_msg = "%s: Exception occurred in subscribe_extra_topics, Error: %s at %s" % (
                        self.service_name, error, time.time())
                    logging.info(payload_msg)
        except Exception as e:
            logging.error(f"An error occurred in subscribe_extra_topics: {str(e)}")

    def reconnect_broker(self):
        try:
            logging.info("let's reconnet..")
            self.load_mqtt_settings[self.trends_key] = self.readfile()
            self.connect_broker()
            # self.thread.start() #pm add #required?
            logging.info("reconnect done...")
        except Exception as e:
            logging.error(f"An error occurred in reconnect_broker: {str(e)}")


    def multi_loop(self, flag=True):

        # This function helps to run the client in loop
        # Args:
        #     flag
        while flag:
            # print("inside true")
            try:
                # print(self.microservice_name)
                self.client.loop_forever(retry_first_connection=True)
                if self.client.connected_flag is False:
                    self.connect_broker()
                    logging.warning("Reconnecting to MQTT broker %s",
                                    self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'])
                    time.sleep(0.5)
                if self.stop_multi_loop is True:
                    break
            except Exception as error:
                payload_msg = "%s: Exception occured in multi loop, Error:%s at %s" % (
                    self.microservice_name, error, time.time())
                logging.error(payload_msg)
                self.reconnect_broker()
        # try:
        #     while flag:
        #         self.client.loop()
        #         if self.client.is_connected() is False:
        #             self.connect_broker()
        #             logging.warning("Reconnecting to MQTT broker %s",
        #                             self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'])
        #             # time.sleep(2)
        #         if self.stop_multi_loop is True:
        #             break
        # except Exception as e:
        #     logging.error(f"An error occurred in multi_loop: {str(e)}")



    # def multi_loop(self, flag=True):
    #     while flag:
    #         # print("inside true")
    #         if self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_enabled'] == 1:
    #             logging.info("ssl is enabled , this is inside multi loop")
    #             try:
    #
    #                 # print(self.microservice_name)
    #                 self.client.loop_forever(retry_first_connection=True)
    #                 if self.client.connected_flag is False:
    #                     self.connect_broker()
    #                     logging.warning("Reconnecting to MQTT broker %s",
    #                                     self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'])
    #                     # time.sleep(2)
    #                 if self.stop_multi_loop is True:
    #                     break
    #             except Exception as error:
    #                 payload_msg = "%s: Exception occured in multi loop, Error:%s at %s" % (
    #                     self.microservice_name, error, time.time())
    #                 logging.error(payload_msg)
    #                 self.reconnect_broker()
    #         elif self.load_mqtt_settings[self.trends_key][self.broker_key]['ssl_auth_enabled'] == 0:
    #             logging.info("ssl is not enabled , this is inside multi loop")
    #             try:
    #                 while flag:
    #                     self.client.loop()
    #                     if self.client.is_connected() is False:
    #                         self.connect_broker()
    #                         logging.warning("Reconnecting to MQTT broker %s",
    #                                         self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'])
    #                         # time.sleep(2)
    #                     if self.stop_multi_loop is True:
    #                         break
    #             except Exception as e:
    #                 logging.error(f"An error occurred in multi_loop: {str(e)}")


    def set_multi_loop_flag(self, boolean):
        try:
            self.stop_multi_loop = boolean
            logging.info("self.stop_multi_loop   :", self.stop_multi_loop)
        except Exception as e:
            logging.error(f"An error occurred in set_multi_loop_flag: {str(e)}")

    def disconnect(self):
        try:
            self.client.disconnect()
        except Exception as e:
            logging.error(f"An error occurred in disconnect: {str(e)}")


#----------
    #
    # def multi_loop(self, flag=True):
    #     '''
    #     This function helps to run the client in loop
    #     Args:
    #         flag
    #     '''
    #     while flag:
    #         # print("inside true")
    #         try:
    #             # print(self.microservice_name)
    #             self.client.loop_forever(retry_first_connection=True)
    #             if self.client.connected_flag is False:
    #                 self.connect_broker()
    #                 logging.warning("Reconnecting to MQTT broker %s",
    #                                 self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'])
    #                 # time.sleep(2)
    #             if self.stop_multi_loop is True:
    #                 break
    #         except Exception as error:
    #             payload_msg = "%s: Exception occured in multi loop, Error:%s at %s" % (
    #                 self.microservice_name, error, time.time())
    #             logging.error(payload_msg)
    #             self.reconnect_broker()
    #     # try:
    #     #     while flag:
    #     #         self.client.loop()
    #     #         if self.client.is_connected() is False:
    #     #             self.connect_broker()
    #     #             logging.warning("Reconnecting to MQTT broker %s",
    #     #                             self.load_mqtt_settings[self.trends_key][self.broker_key]['broker_ip'])
    #     #             # time.sleep(2)
    #     #         if self.stop_multi_loop is True:
    #     #             break
    #     # except Exception as e:
    #     #     logging.error(f"An error occurred in multi_loop: {str(e)}")
