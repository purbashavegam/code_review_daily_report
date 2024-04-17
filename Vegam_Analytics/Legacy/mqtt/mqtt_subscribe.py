# import paho.mqtt.client as mqtt
# import re
# import os
# import json
# import time
#
# def extract_parameters(userdata):
#     try:
#         userdata_dict = eval(userdata)  # Convert userdata string to dictionary  #eval???
#         sampling_frequency = userdata_dict.get("s")
#         window_size = userdata_dict.get("w")
#         time_stamp = userdata_dict.get("t")
#         data = userdata_dict.get("d")
#
#         if sampling_frequency is not None and window_size is not None and time_stamp is not None and data is not None:
#             return sampling_frequency, window_size, time_stamp, data
#         else:
#             print("Incomplete or missing parameters in userdata")
#             return None, None, None, None
#     except Exception as e:
#         print("Error while extracting parameters:", str(e))
#         return None, None, None, None

#
# # to raise exception
# class InvalidUserDataError(Exception):
#     pass
#
# def extract_parameters(userdata):
#     try:
#         print("hi in try")
#         userdata_dict = json.loads(userdata)  # eval should not be used
#         print("tt=ype:", type(userdata_dict))
#         if not isinstance(userdata_dict, dict):
#             raise InvalidUserDataError("User data is not a dictionary")
#         else:
#             sampling_frequency = userdata_dict.get("s")
#             window_size = userdata_dict.get("w")
#             time_stamp = userdata_dict.get("t")
#             data = userdata_dict.get("d")
#
#         if sampling_frequency is not None and window_size is not None and time_stamp is not None and data is not None:
#             print(sampling_frequency, window_size, time_stamp, data, "<--44444444-")
#             return sampling_frequency, window_size, time_stamp, data
#         else:
#             # print(sampling_frequency, window_size, time_stamp, data, "<--else44444444-")
#             print("Incomplete or missing parameters in userdata")
#             return None, None, None, None
#     except InvalidUserDataError as e:
#         print("Error while extracting parameters:", str(e))
#         return None, None, None, None
#     except Exception as e:
#         print("An unexpected error occurred:", str(e))
#         return None, None, None, None
# #
# extract_parameters("InvalidUserData")
# exit()

import paho.mqtt.client as mqtt
import re
import os
import json
import time


# # to raise exception
# class InvalidUserDataError(Exception):
#     pass


class MqttClient:
    def __init__(self, config_file_path):
        self.data_que = []
        self.config_file_path = config_file_path
        self.load_config()

        self.publish_client = mqtt.Client()
        self.publish_client.username_pw_set(username=self.username, password=self.password)
        self.publish_client.connect(self.broker_ip, self.broker_port)

        self.subscribe_client = mqtt.Client()
        self.subscribe_client.username_pw_set(username=self.username, password=self.password)
        self.subscribe_client.on_connect = self.on_connect_subscriber
        self.subscribe_client.on_message = self.on_message

    def connect_to_broker(self, client):
        client.connect(self.broker_ip, self.broker_port)
        client.loop_start()

    def load_config(self):
        DIR = os.path.dirname(__file__)
        if not DIR:
            FILE_PATH = "Vegam_MQTT.json"
        else:
            FILE_PATH = os.path.join(DIR, "Vegam_MQTT.json")

        with open(FILE_PATH, 'r') as readfile:
            main_config = json.load(readfile)
            self.broker_ip = main_config["broker_details"]["broker_ip"]
            self.username = main_config["broker_details"]["broker_username"]
            self.password = main_config["broker_details"]["broker_password"]
            self.broker_port = main_config['broker_details']['broker_port']

    def on_connect_subscriber(self, client, userdata, flags, rc):
        if rc == 0:
            print("Subscribing Client: Connected to the broker")
            client.subscribe("+/SensorData/AccelerometerX")
        else:
            print("Subscribing Client: Connection failed")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        self.data_que.append(str(msg.payload.decode("utf-8")))

        sensor_mac_id = self.extract_sensor_mac_id(topic)
        sampling_frequency, window_size, time_stamp, data = self.extract_parameters(str(msg.payload.decode("utf-8")))

        if sampling_frequency is not None and window_size is not None and time_stamp is not None and data is not None:
            print("Sensor MAC ID:", sensor_mac_id)
            print("Sampling Frequency:", sampling_frequency)
            print("Window Size:", window_size)
            print("Timestamp:", time_stamp)
            print("Data:", data)

    def extract_sensor_mac_id(self, topic):
        sensor_name_match = re.search(r'(.*?)/SensorData/AccelerometerX', topic)
        if sensor_name_match:
            return sensor_name_match.group(1)
        else:
            print(f"Failed to extract Sensor MAC ID from topic: {topic}")
            return None

    def extract_parameters(self, userdata):
        try:
            # userdata_dict = eval(userdata)  # Convert userdata string to dictionary  # eval == vulnerabilities, please check
            userdata_dict = json.loads(userdata)
            sampling_frequency = userdata_dict.get("s")
            window_size = userdata_dict.get("w")
            time_stamp = userdata_dict.get("t")
            data = userdata_dict.get("d")

            if sampling_frequency is not None and window_size is not None and time_stamp is not None and data is not None:
                return sampling_frequency, window_size, time_stamp, data
            else:
                print("Incomplete or missing parameters in userdata")
                return None, None, None, None
        except Exception as e:
            print("Error while extracting parameters:", str(e))
            return None, None, None, None

    def run(self):
        try:
            self.connect_to_broker(self.publish_client)
            self.connect_to_broker(self.subscribe_client)
            while True:
                time.sleep(2)  # Adjust the delay time as needed
        except KeyboardInterrupt:
            print("Subscribing Client: Stopped")
            self.subscribe_client.disconnect()
            self.publish_client.disconnect()


if __name__ == "__main__":
    config_file_path = "Vegam_MQTT.json"
    mqtt_client = MqttClient(config_file_path)
    mqtt_client.run()












#     # def get_connection_status(self):
#     #     return self.subscribe_client._state
#
