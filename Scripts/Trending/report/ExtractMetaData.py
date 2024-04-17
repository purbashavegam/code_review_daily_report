import json
from functools import wraps
import requests
import logging
import time

# with open('ReportGenerator.json') as json_file:
#     ReportGeneratorConfig = json.load(json_file)


def retry(num_retry, sleep_sec):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """A wrapper function"""
            for retry_num in range(1, num_retry+1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print("Number of retry ", retry_num)
                    logging.error(f'Attempting retry -----{retry_num}----for Extract Meta Data -------exception{str(e)}')
                    time.sleep(sleep_sec)
            return {}

        return wrapper

    return decorator

class ExtractMetaData:
    def __init__(self, vmaint_api_url,cache,area_checking_key):
        self.vmaint_api_url = vmaint_api_url
        self.input_data = []
        self.vmaint_api_json = self.input_data if len(self.input_data)>0 else [] # can be removed later this line for report
        # why calling api at first , call when needed
        self.desired_represents = ["V_RMSX", "V_RMSY", "V_RMSZ"]
        self.extracted_topics = []  # Add this line to initialize extracted_topics

        # self.input_data = self.vmaint_api_json
        # self.result_list = []
        # self.result_list_str = []
        self.check_key =area_checking_key #"CHP - 1200 MW"                  # ReportGeneratorConfig["area_check"] #as it is for alert

        self.cache_duration = cache
        # 180  # 3 minutes in seconds #get 24 hours from json or alert generator class.
        self.cached_data = None
        self.last_fetch_time = 0



    @retry(5, 30)
    def get_metadata_from_api(self, json_data=None):
        try:
            # Check if the data is still valid in the cache
            current_time = time.time()
            if self.cached_data and (current_time - self.last_fetch_time) < self.cache_duration:
                # print("Using cached data")
                logging.info("getting cached data for vmaint api..")
                return self.cached_data

            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.vmaint_api_url, json=json_data, headers=headers)
            print(response)

            if response.status_code == 200:
                result_json = response.json()
                # print("vmaint data came..yoooo hooooo", len(result_json))

                # Update the cache
                self.cached_data = result_json
                self.last_fetch_time = current_time

                print(result_json)
                return result_json
            else:
                print(f"Failed to make vmaint API call. Status code: {response.status_code}")
                print(response.text)
                raise
        except requests.exceptions.RequestException as e:
            print(f"Error fetching metadata from API: {e}")
            logging.error(f"Error fetching metadata from API: {e}")
            raise e

    def extract_topic_in_order(self, node, desired_represents, extracted_topics):
        try:
            if isinstance(node, list):
                for item in node:
                    self.extract_topic_in_order(item, desired_represents, extracted_topics)
            elif isinstance(node, dict):
                tags = node.get('Tags', [])
                for topic_represents in desired_represents:
                    for tag in tags:
                        try:
                            topic_represent = tag.get('TopicRepresents', '')
                            if topic_represent == topic_represents:
                                extracted_topics.append(tag['Topic'])
                        except Exception as e:
                            # Handle the exception, e.g., log the error or print a message
                            print(f"Error processing tag: {e}")

                # Recursively explore nested structures
                for key, value in node.items():
                    if isinstance(value, (list, dict)):
                        self.extract_topic_in_order(value, desired_represents, extracted_topics)
        except Exception as e:
            # Handle the exception, e.g., log the error or print a message
            print(f"Error in extract_topic_in_order: {e}")

    def extract_all_data(self):
        all_data = {
            'AllTopics': self.extract_all_topics(),
            'EquipmentDetails': self.vmaint_api_json.get('EquipmentDetails', {}),
            'AxisInfo': self.vmaint_api_json.get('AxisInfo', {}),
            'SensorMACIDs': self.vmaint_api_json.get('SensorMACIDS', {}),
            'AreaHierarchy': self.vmaint_api_json.get('AreaHierarchy', {}),
        }
        return all_data

    def extract_all_topics_recursive(self, structure):
        try:
            topics = []
            if isinstance(structure, list):
                for item in structure:
                    topics.extend(self.extract_all_topics_recursive(item))
            elif isinstance(structure, dict):
                for key, value in structure.items():
                    if key == 'Topic':
                        topic_data = {'Topic': value, 'TopicRepresents': structure.get('TopicRepresents', '')}
                        if any(topic_data.values()):
                            topics.append(topic_data)
                    elif isinstance(value, (list, dict)):
                        topics.extend(self.extract_all_topics_recursive(value))
            return topics
        except Exception as e:
            print(f"Error in extract_all_topics_recursive: {e}")
            logging.error(f"Error in extract_all_topics_recursive: {e}")
            return []


    def extract_all_topics(self):
        try:
            topics = []
            for key, value in self.vmaint_api_json.items():
                if key == 'Topic':
                    topic_data = {'Topic': value, 'TopicRepresents': self.vmaint_api_json.get('TopicRepresents', '')}
                    if any(topic_data.values()):
                        topics.append(topic_data)
                elif isinstance(value, (list, dict)):
                    topics.extend(self.extract_all_topics_recursive(value))
            return topics
        except Exception as e:
            logging.error(f"An error occurred in extract_all_topics: {str(e)}")
            return []

    def extract_topics_in_order(self, desired_represents):
        try:
            extracted_topics = []
            self.extract_topic_in_order(self.vmaint_api_json, self.desired_represents, extracted_topics)
            return extracted_topics
        except Exception as e:
            logging.error(f"An error occurred in extract_topics_in_order: {str(e)}")
            return []



    def extract_sensor_mac_ids(self):
        try:
            """
            Extract Sensor MAC IDs from the fetched metadata JSON.
            Returns:
            - list: A list of Sensor MAC IDs.
            """
            # Look for Sensor MAC IDs under 'attachedSensors' first
            attached_sensors = self.vmaint_api_json.get('attachedSensors', [])
            sensor_mac_ids = []
            for sensor in attached_sensors:
                mac_id = sensor.get('SensorMacID', '')
                if mac_id:
                    sensor_mac_ids.append(mac_id)
            # If not found under 'attachedSensors', check the entire JSON
            if not sensor_mac_ids:
                sensor_mac_ids = self._recursive_extract_sensor_mac_ids(self.vmaint_api_json)
            return sensor_mac_ids
        except Exception as e:
            logging.error(f"An error occurred in extract_sensor_mac_ids: {str(e)}")
            return []

    def _recursive_extract_sensor_mac_ids(self, node):
        try:
            """
            A helper method for recursive extraction of Sensor MAC IDs.
            """
            sensor_mac_ids = []
            if isinstance(node, list):
                for item in node:
                    sensor_mac_ids.extend(self._recursive_extract_sensor_mac_ids(item))
            elif isinstance(node, dict):
                for key, value in node.items():
                    if key == 'SensorMacID':
                        sensor_mac_ids.append(value)
                    elif isinstance(value, (list, dict)):
                        sensor_mac_ids.extend(self._recursive_extract_sensor_mac_ids(value))
        except Exception as e:
            logging.error(f"Error in _recursive_extract_sensor_mac_ids: {str(e)}")
            print('error in _recursive_extract_sensor_mac_ids')
        return sensor_mac_ids

    def find_equipment_info(self,data, check_key, result_list):
        try:
            if isinstance(data, dict):
                # Check if the current dictionary has the check_key in the 'Areas' value
                if 'Areas' in data and data['Areas'] is not None:
                    for area in data['Areas']:
                        # print(area['LocationName'])
                        if area[
                            'LocationName'] == check_key:  # this is not working, for report-- but working for alert-> taking all mac ids
                            # print("hi")
                            # If the check_key is found in 'Areas', collect equipment info
                            self.collect_equipment_info(area, result_list)
                        # Recursively check in the nested 'Areas'
                        self.find_equipment_info(area, check_key, result_list)
                # Check if the current dictionary has the 'Equipments' value
                if 'Equipments' in data and data['Equipments'] is not None:
                    self.collect_equipment_info(data, result_list)
                # Recursively check in other key-value pairs
                for value in data.values():
                    self.find_equipment_info(value, check_key, result_list)
        except Exception as e:
            # Handle the exception (e.g., log the error)
            logging.error(f"Error in find_equipment_info:{str(e)}")
            print(f"Error in find_equipment_info: {str(e)}")

    def collect_equipment_info(self,area_data, result_list):
        try:
            if 'Equipments' in area_data and area_data['Equipments'] is not None:
                for equipment in area_data['Equipments']:
                    if 'AttachedSensors' in equipment and equipment['AttachedSensors'] is not None:
                        for sensor in equipment['AttachedSensors']:
                            temp_dict = {}
                            # temp_list =[]
                            #pm patch moving avg axis wise code
                            temp_dict["AxisX"] = sensor["AxisX"]
                            temp_dict["AxisY"] = sensor["AxisY"]
                            temp_dict["AxisZ"] = sensor["AxisZ"]
                            # print(sensor)
                            # print(temp_dict)
                            temp_list = sensor["Tags"]
                            # print(temp_list)
                            temp_list.append(temp_dict)


                            mac_id_with_tags = {sensor['SensorMacID']: temp_list} # pm checking
                            # "AxisX": "HORIZONTAL_R",
                            # "AxisY": "VERTICAL_R",
                            # "AxisZ": "AXIAL"
                            #pm patch
                            # mac_id_with_tags = {sensor['SensorMacID']: sensor["Tags"]} #pm - og
                            result_list.append(mac_id_with_tags)
        except Exception as e:
            # Handle the exception here, e.g., print an error message or log it
            print(f"Error in collect_equipment_info: {str(e)}")
            logging.error(f"Error in collect_equipment_info: {str(e)}")

    def get_mac_ids_tags_for_alret(self):
        try:
            hc_list = [
                {
                    "EE0C38A63F6A": [
                        {
                            "Topic": "818",
                            "TopicRepresents": "V_RMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "823",
                            "TopicRepresents": "V_RMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "828",
                            "TopicRepresents": "V_RMSZ",
                            "TopicType": "S"
                        }
                    ]
                },
                {
                    "DC89C06D84ED": [
                        {
                            "Topic": "846",
                            "TopicRepresents": "V_RMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "851",
                            "TopicRepresents": "V_RMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "856",
                            "TopicRepresents": "V_RMSZ",
                            "TopicType": "S"
                        }
                    ]
                },
                {
                    "C887A1859188": [
                        {
                            "Topic": "877",
                            "TopicRepresents": "V_RMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "882",
                            "TopicRepresents": "V_RMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "887",
                            "TopicRepresents": "V_RMSZ",
                            "TopicType": "S"
                        }
                    ]
                }
            ]  # pm test
            hc_list_5 = [
                {
                    "CB80735DCC28": [
                        {
                            "Topic": "1172",
                            "TopicRepresents": "VRMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1177",
                            "TopicRepresents": "VRMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1182",
                            "TopicRepresents": "VRMSZ",
                            "TopicType": "S"
                        }
                    ]
                },
                {
                    "E58BB96F1BDD": [
                        {
                            "Topic": "1203",
                            "TopicRepresents": "VRMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1208",
                            "TopicRepresents": "VRMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1213",
                            "TopicRepresents": "VRMSZ",
                            "TopicType": "S"
                        }
                    ]
                },
                {
                    "E5ABAD392F1A": [
                        {
                            "Topic": "1234",
                            "TopicRepresents": "VRMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1239",
                            "TopicRepresents": "VRMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1244",
                            "TopicRepresents": "VRMSZ",
                            "TopicType": "S"
                        }
                    ]
                },
                {
                    "F29EF6342CEE": [
                        {
                            "Topic": "1265",
                            "TopicRepresents": "VRMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1270",
                            "TopicRepresents": "VRMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1275",
                            "TopicRepresents": "VRMSZ",
                            "TopicType": "S"
                        }
                    ]
                },
                {
                    "C93DCD037BE0": [
                        {
                            "Topic": "1296",
                            "TopicRepresents": "VRMSX",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1301",
                            "TopicRepresents": "VRMSY",
                            "TopicType": "S"
                        },
                        {
                            "Topic": "1306",
                            "TopicRepresents": "VRMSZ",
                            "TopicType": "S"
                        }
                    ]
                }
            ]
            hc_list_10 = [
    {
        "CB80735DCC28": [
            {
                "Topic": "1172",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1177",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1182",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E58BB96F1BDD": [
            {
                "Topic": "1203",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1208",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1213",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E5ABAD392F1A": [
            {
                "Topic": "1234",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1239",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1244",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F29EF6342CEE": [
            {
                "Topic": "1265",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1270",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1275",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C93DCD037BE0": [
            {
                "Topic": "1296",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1301",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1306",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D5CC7ABE0B80": [
            {
                "Topic": "1327",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1332",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1337",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D93BEB1BB907": [
            {
                "Topic": "1362",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1367",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1372",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F56A571956E8": [
            {
                "Topic": "1389",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1394",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1399",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F0313FB8BDCE": [
            {
                "Topic": "1420",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1425",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1430",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E36AC193831D": [
            {
                "Topic": "1451",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1456",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1461",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    }
]
            hc_list_20 = [
    {
        "CB80735DCC28": [
            {
                "Topic": "1172",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1177",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1182",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E58BB96F1BDD": [
            {
                "Topic": "1203",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1208",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1213",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E5ABAD392F1A": [
            {
                "Topic": "1234",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1239",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1244",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F29EF6342CEE": [
            {
                "Topic": "1265",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1270",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1275",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C93DCD037BE0": [
            {
                "Topic": "1296",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1301",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1306",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D5CC7ABE0B80": [
            {
                "Topic": "1327",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1332",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1337",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D93BEB1BB907": [
            {
                "Topic": "1362",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1367",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1372",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F56A571956E8": [
            {
                "Topic": "1389",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1394",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1399",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F0313FB8BDCE": [
            {
                "Topic": "1420",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1425",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1430",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E36AC193831D": [
            {
                "Topic": "1451",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1456",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1461",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F8221B8C9DBE": [
            {
                "Topic": "1947",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1952",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1957",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "FF70BADC4288": [
            {
                "Topic": "1978",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1983",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1988",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F96D0C475001": [
            {
                "Topic": "2009",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2014",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2019",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "EC3051C00B06": [
            {
                "Topic": "2040",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2045",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2050",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "FBAE64DF745C": [
            {
                "Topic": "2071",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2076",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2081",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F1F55737FD75": [
            {
                "Topic": "2412",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2417",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2422",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C162A83CE125": [
            {
                "Topic": "2443",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2448",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2453",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F5C0D5432743": [
            {
                "Topic": "2474",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2479",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2484",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D11DB7433F79": [
            {
                "Topic": "2505",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2510",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2515",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "EE9BE3F7DF79": [
            {
                "Topic": "2536",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2541",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2546",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    }
]
            hc_list_39 = [
    {
        "CB80735DCC28": [
            {
                "Topic": "1172",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1177",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1182",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E58BB96F1BDD": [
            {
                "Topic": "1203",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1208",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1213",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E5ABAD392F1A": [
            {
                "Topic": "1234",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1239",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1244",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F29EF6342CEE": [
            {
                "Topic": "1265",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1270",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1275",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C93DCD037BE0": [
            {
                "Topic": "1296",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1301",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1306",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D5CC7ABE0B80": [
            {
                "Topic": "1327",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1332",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1337",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D93BEB1BB907": [
            {
                "Topic": "1362",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1367",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1372",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F56A571956E8": [
            {
                "Topic": "1389",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1394",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1399",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F0313FB8BDCE": [
            {
                "Topic": "1420",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1425",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1430",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E36AC193831D": [
            {
                "Topic": "1451",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1456",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1461",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F8221B8C9DBE": [
            {
                "Topic": "1947",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1952",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1957",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "FF70BADC4288": [
            {
                "Topic": "1978",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "1983",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "1988",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F96D0C475001": [
            {
                "Topic": "2009",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2014",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2019",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "EC3051C00B06": [
            {
                "Topic": "2040",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2045",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2050",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "FBAE64DF745C": [
            {
                "Topic": "2071",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2076",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2081",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F1F55737FD75": [
            {
                "Topic": "2412",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2417",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2422",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C162A83CE125": [
            {
                "Topic": "2443",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2448",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2453",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F5C0D5432743": [
            {
                "Topic": "2474",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2479",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2484",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D11DB7433F79": [
            {
                "Topic": "2505",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2510",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2515",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "EE9BE3F7DF79": [
            {
                "Topic": "2536",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2541",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2546",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "DB5F7165C858": [
            {
                "Topic": "2567",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2572",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2577",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E88F6EE924C7": [
            {
                "Topic": "2598",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2603",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2608",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C99B9AF8A39D": [
            {
                "Topic": "2629",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2634",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2639",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D10A4AE14B58": [
            {
                "Topic": "2660",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2665",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2670",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C92E6D8523A8": [
            {
                "Topic": "2691",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2696",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2701",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "CC451EAE9CEC": [
            {
                "Topic": "2722",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2727",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2732",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C7982C8EC99C": [
            {
                "Topic": "2753",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2758",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2763",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "CD0D2702CDB2": [
            {
                "Topic": "2784",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2789",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2794",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C93A8F0E33EB": [
            {
                "Topic": "2815",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2820",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2825",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "CFADFA33AD2C": [
            {
                "Topic": "2846",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2851",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2856",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C9DA4D4F9BE8": [
            {
                "Topic": "2877",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2882",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2887",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "D1091ADD53FD": [
            {
                "Topic": "2908",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2913",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2918",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "FF51940BE967": [
            {
                "Topic": "2939",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2944",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2949",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C6F6638E148F": [
            {
                "Topic": "2970",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "2975",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "2980",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "CF0E80807A93": [
            {
                "Topic": "3001",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "3006",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "3011",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F5318ED9F3F3": [
            {
                "Topic": "3718",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "3723",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "3728",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "C1B18D10A999": [
            {
                "Topic": "3746",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "3751",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "3756",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "E56F4DB384C1": [
            {
                "Topic": "3777",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "3782",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "3787",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    },
    {
        "F8CD30F158AD": [
            {
                "Topic": "3805",
                "TopicRepresents": "VRMSX",
                "TopicType": "S"
            },
            {
                "Topic": "3810",
                "TopicRepresents": "VRMSY",
                "TopicType": "S"
            },
            {
                "Topic": "3815",
                "TopicRepresents": "VRMSZ",
                "TopicType": "S"
            }
        ]
    }
]

            temp_check_key = "none"
            if self.check_key != temp_check_key:
                self.check_key = temp_check_key
                logging.info("changed the check key to none,as it is not none from json")
            else:
                logging.info("nothing to change in check key, it is none from json itself")
                pass

            # print("it came here...")
            self.result_list = []
            self.result_list_str = []
            self.input_data = self.get_metadata_from_api()
            # print("or not came..")
            if len(self.input_data ) >0:
                self.find_equipment_info(self.input_data, self.check_key, self.result_list)
                # print(self.result_list)
                print(len(self.result_list))
                for item in self.result_list:
                    # print(item)
                    key = next(iter(item.keys()))
                    value = item[key]
                    # print(key)
                    # print(value)
                    updated_value_with_vrms = [item for item in value if 'V_RMS' in item.get('TopicRepresents', '')]
                    item[key] = updated_value_with_vrms
                    # print(item)
                # print(self.result_list)
                # print(len(self.result_list))
                return self.result_list #pm
                # return hc_list_39 #pm test
            else:
                # print("vmaint api is giving empty data")
                logging.info("vmaint api is giving empty data, can't proceed..")
                # return hc_list_39 #pm test
        except Exception as exception:
            # print('Exception in mac id with tags wala method: ' + str(exception))
            logging.error('Exception in mac id with tags wala method:: ' + str(exception))

    def find_sensor_location_info(self, data):
        try:
            sensor_info_list = []

            # Iterate through areas to find SensorMacID, EquipmentID, and EquipmentName
            self.recursive_search_and_collect(data, sensor_info_list)

            return sensor_info_list
        except Exception as e:
            logging.error(f"An error occurred in find_sensor_location_info: {str(e)}")
            return []

    def recursive_search_and_collect(self, data, sensor_info_list):
        try:
            if 'Areas' in data and data['Areas']:
                for sub_area in data['Areas']:
                    self.recursive_search_and_collect(sub_area, sensor_info_list)

            # Once you find an area with null, extract SensorMacID, EquipmentID, and EquipmentName
            if 'Equipments' in data and data['Equipments']:
                for equipment in data['Equipments']:
                    if 'AttachedSensors' in equipment and equipment['AttachedSensors']:
                        for sensor in equipment['AttachedSensors']:
                            sensor_info = {
                                'SensorMacID': sensor.get('SensorMacID', ''),
                                'EquipmentID': equipment.get('EquipmentID', ''),
                                'EquipmentName': equipment.get('EquipmentName', ''),

                            }
                            sensor_info_list.append(sensor_info)
        except Exception as e:
            # Log an error message along with the exception information
            logging.error(f"An error occurred in recursive_search_and_collect: {str(e)}")
            # Return an empty list in case of an error
            return []
        return sensor_info_list


    def extract_area_hierarchy(self,sensor_mac_id, areas, site_name):
        try:
            for area in areas:
                hierarchy = self.find_sensor_in_area(sensor_mac_id, area, [], site_name)
                if hierarchy:
                    return hierarchy
        except Exception as e:
            # Log an error message along with the exception information
            logging.error(f"An error occurred in extract_area_hierarchy: {str(e)}")
            # Return an empty list in case of an error
            return []

    def find_sensor_in_area(self,sensor_mac_id, area, parent_names, site_name):
        try:
            current_name = area.get("LocationName")
            if current_name:
                current_hierarchy = [current_name] + parent_names
            else:
                current_hierarchy = parent_names

            if area["Equipments"]:
                for equipment in area["Equipments"]:
                    for sensor in equipment["AttachedSensors"]:
                        if sensor["SensorMacID"] == sensor_mac_id:
                            return current_hierarchy

            if area["Areas"]:
                for sub_area in area["Areas"]:
                    hierarchy = self.find_sensor_in_area(sensor_mac_id, sub_area, current_hierarchy, site_name)
                    if hierarchy:
                        return hierarchy
        except Exception as e:
            # Log an error message along with the exception information
            logging.error(f"An error occurred in find_sensor_in_area: {str(e)}")
            # Return None or handle the exception if needed
            return None

        return None

    def get_hierarchy_level_with_equipment_details_from_metadata(self):
        try:
            sensor_info_list = []
            sensor_information = []
            sensor_information_for_selected_area=[]
            vmaint_api_url = self.vmaint_api_url

            # metadata = ExtractMetaData(vmaint_api_url, 1)

            # #for local work
            # file_path = r'D:\vegam_projects\GIT_works\Vegam_Analytics\Scripts\Trending\report\metadata.json' #pm local
            # # file_path = r'D:\ExeWorks_sp\Scripts\Trending\report\metadata.json' # sp local
            # with open(file_path, 'r') as file:
            #     vmaint_api_json = json.load(file)
            #
            # # for local work


            vmaint_api_json = self.get_metadata_from_api() # pm # can be optimized?? check it please --> pm

            site_name = vmaint_api_json.get("SiteName", "")

            result_list = self.recursive_search_and_collect(vmaint_api_json, sensor_info_list)

            for sensor_mac_id_to_extract in result_list:
                sensor_mac_id = sensor_mac_id_to_extract.get('SensorMacID', '')
                EquipmentID = sensor_mac_id_to_extract.get('EquipmentID', '')
                EquipmentName = sensor_mac_id_to_extract.get('EquipmentName', '')

                area_hierarchy = self.extract_area_hierarchy(sensor_mac_id, vmaint_api_json["Areas"], site_name)

                if area_hierarchy:
                    result = f"{site_name}_{'_'.join(reversed(area_hierarchy))}"
                else:
                    result = f"{site_name}"
                    print(f"Sensor with MAC ID {sensor_mac_id} not found.")

                sensor_info = {
                    'SensorMacID': sensor_mac_id,
                    'EquipmentID': EquipmentID,
                    'EquipmentName': EquipmentName,
                    'Area_Hierarchy': result,
                }
                if self.check_key is None or self.check_key.lower().strip() in ["none", "", " "]:
                    sensor_information.append(sensor_info)
                elif self.check_key in result:
                    sensor_information_for_selected_area.append(sensor_info)

            if self.check_key and self.check_key.strip() not in ["", " "] and (self.check_key != "none" or self.check_key in result):
                return sensor_information_for_selected_area
            else:
                return sensor_information



        except Exception as e:
            print("error")
            logging.error(
            f"An error occurred in get_hierarchy_level_with_equipment_details_from_metadata: {str(e)}")
        return []

    def get_mac_ids_tags_for_report_with_temp(self):
        try:
            self.result_list = []
            self.result_list_str = []
            self.input_data = self.get_metadata_from_api() #this is full meta data json
            # print("or not came..")
            if len(self.input_data) > 0:
                self.find_equipment_info(self.input_data, self.check_key, self.result_list)
                # print(self.result_list)
                # print(len(self.result_list))
                for item in self.result_list:
                    # print(item)
                    key = next(iter(item.keys()))
                    value = item[key]
                    updated_value_with_vrms_or_temp = [item for item in value if 'V_RMS' in item.get('TopicRepresents', '')]


                    # Find and add the Axis information from self.result_list for report
                    axis_info = next((item for item in value if 'AxisX' in item), None)
                    if axis_info:
                        updated_value_with_vrms_or_temp.append(axis_info)
                    # print(updated_value_with_vrms_or_temp,'++++++')

                    updated_value_with_vrms = [item for item in updated_value_with_vrms_or_temp if 'Topic' in item]
                    # print(updated_value_with_vrms,'updated_value_with_vrms')
                    item[key] = updated_value_with_vrms
                    # print(item)
                # print(self.result_list)

                #HACK: removing duplicate keys.. happened in chp_common. why happened , not sure.
                # review: this part needs to be reviewed later.
                seen_keys = set()
                result = []

                for item in self.result_list:
                    key = next(iter(item))
                    if key in seen_keys:
                        logging.critical("this is duplicate key, so not sending ")
                        logging.info(f"duplicate key is: {key}")
                    else:
                        # print("iooo")
                        seen_keys.add(key)
                        result.append(item)

                # print(result)


                # print(len(result))
                return result  # pm
                # return self.result_list[:3]  # pm test
                # return hc_list_39 #pm test
            else:
                # print("vmaint api is giving empty data")
                logging.info("vmaint api is giving empty data, can't proceed..")
                # return hc_list_39 #pm test
        except Exception as exception:
            # print('Exception in mac id with tags wala method: ' + str(exception))
            logging.error('Exception in mac id with tags wala method:: ' + str(exception))

    def get_axis_information(self):
        try:
            self.result_list = []
            self.result_list_str = []
            self.input_data = self.get_metadata_from_api()  # this is full meta data json

            if len(self.input_data) > 0:
                self.find_equipment_info(self.input_data, self.check_key, self.result_list)

                for item in self.result_list:
                    key = next(iter(item.keys()))
                    value = item[key]
                    updated_value_with_vrms_or_temp = [item for item in value if
                                                       'V_RMS' in item.get('TopicRepresents', '')]

                    # Find and add the Axis information from self.result_list for report
                    axis_info = next((item for item in value if 'AxisX' in item), None)
                    if axis_info:
                        updated_value_with_vrms_or_temp.append(axis_info)

                    updated_value_with_vrms = [item for item in updated_value_with_vrms_or_temp if 'Topic' in item]

                    # Update the item with the filtered values
                    item[key] = updated_value_with_vrms_or_temp

                    # Add 'macid' dictionary to the filtered values
                    mac_dict = {'macid': key}
                    updated_value_with_vrms_or_temp.append(mac_dict)
                # print(self.result_list,'fhjkl')

                return self.result_list

        except Exception as exception:
            logging.error('Exception in get_axis_information method: ' + str(exception))



# a = ExtractMetaData("https://apps.vegam.co/Vegam_MaintenanceService/MaintenanceAnalyticsService.svc/DeployedSensors?siteID=26",
#                     1,"Cooling Tower Area")
# a.get_metadata_from_api()