import os
import pandas as pd
import logging
import numpy as np
import threading
import time
import json
import requests as req
import nltk
from nltk import flatten
# import logers
import vanalytics_data as v_data
import vanalytics_api as v_api
import vanalytics_helper as v_helper 
import mqtt_con as m_con
from logging_manager import main_logger

# log = logers.customLogger(logging.DEBUG)

DIR = os.path.dirname(__file__)
if not DIR:
    FILE_PATH = "main_config.json"
else:
    FILE_PATH = DIR + "/main_config.json"

with open(FILE_PATH, 'r') as readfile:
    main_config = json.load(readfile)
    v_data.CommonFeatures.main_config = main_config

main_logger.info('starting vegam analytics app')


def host_vanalytics():
    try:
        x = threading.Thread(target=v_api.host_api, args=(), daemon=True)
        x.start()
    except Exception as ex:
        main_logger.critical('Exception occured while hosting the api', exc_info=True)
        print(f"Error in method: main.py - host_vanalytics, with Ex: {ex}")


def publish_data():
    while True:
        if len(v_helper.helper.data_to_publish) > 0:
            data = None
            try:
                data = v_helper.helper.data_to_publish.pop()
                pub_equipment_id = data[0]
                pub_sensor_id = data[1]
                pub_type = data[2]
                # pub_payload = json.dumps(data[3])
                pub_payload = data[3]
                broker = getBrokerDetails(pub_equipment_id)
                topic = getPublishTopics(
                    pub_equipment_id, pub_sensor_id, pub_type)
                if topic != "-1":                    
                    client = broker.MqttClient
                    if(pub_type == "FO"):
                        #topic = topic + "All"
                        topic = topic
                    client.publish_data(topic, pub_payload)
                    print(f"{topic} : {pub_payload}")
            except Exception as ex:
                main_logger.critical(
                    f"ERROR while publishing data {data}", exc_info=True)

        time.sleep(.05)

        

def getBrokerDetails(equipment_id): 
    try:
        brokerinfo = v_data.CommonFeatures.equipment_store[equipment_id]['E'].Brokers[0]
        output = brokerinfo.IpAddress + "_" + str(brokerinfo.PortNumber)
        broker = v_data.CommonFeatures.brokers_dict[output]
        return broker
    except Exception as ex:
        print(
            f"Error while getting broker details for equipment {equipment_id}, with error {ex}")
        main_logger.critical(
            f"Error while getting broker details for equipment {equipment_id}", exc_info=True)

def getPublishTopics(equipment_id, sensor_id, tagType):
    topic = "-1"
    try:
        if tagType.upper() == "H":
            tagType = "HEALTH"
        elif tagType.upper() == "O":
            tagType = "ONOFF"
        elif tagType.upper() == "R":
            tagType = "RPM"
        else:
            tagType = "FAULT"

        sensors = v_data.CommonFeatures.equipment_store[equipment_id]['E'].AttachedSensors
        sensor = next((x for x in sensors if x.SensorMacID == sensor_id), None)
        tags = sensor.Tags
        """
        if (sensor.AxisX=='HORIZONTAL_R') and (sensor.AxisY=='VERTICAL_R') and (sensor.AxisZ=='AXIAL') :
            print("data is mounted axially")
            dataaxis='axially'
        if (sensor.AxisX=='VERTICAL_R') and (sensor.AxisY=='HORIZONTAL_R') and (sensor.AxisZ=='AXIAL'):
            print("data is mounted horizontal") 
            dataaxis='horizontal'
        if (sensor.AxisX=='AXIAL') and (sensor.AxisY=='VERTICAL_R') and (sensor.AxisZ=='HORIZONTAL_R'):
            print("data is mounted vertically")  
            dataaxis='vertical'"""
        
        tag = next((x for x in tags if x.TopicRepresents == tagType), None)
        topic = tag.Topic
    except Exception as ex:
        print(f"Error in method: main.py - getPublishTopics, with ex: {ex}")
        #   write log here
    finally:
        return topic

queue_read_flag = True

host_vanalytics()

# handle startup here
def main_start():
    #   get the list of site id's
    v_data.CommonFeatures.site_ids = v_data.CommonFeatures.get_site_to_moniter()

    #   if site are there, get the list of equipments
    if v_data.CommonFeatures.site_ids is not None and len(v_data.CommonFeatures.site_ids) > 0:
        v_data.CommonFeatures.get_sites_equipments()
    else:
        v_data.CommonFeatures.site_ids = []
        main_logger.warning("vmaint api does not returned any sites to monitor")

    #   if metadata list has items, fetch them
    if len(v_data.CommonFeatures.metadata_lookup) > 0:
        v_data.CommonFeatures.get_metadata()

    #   check if brokers to connect
    broker_keys = list(v_data.CommonFeatures.brokers_dict.keys())
    if len(broker_keys) > 0:
        v_data.CommonFeatures.connect_subscribe_mqtt(broker_keys)

def time_based_data_processing():
    while True:
        try:
            keys = list(v_data.CommonFeatures.sensordata_lookup.keys())
            if len(keys) > 0:
                for key in keys:
                    vsens = v_data.CommonFeatures.sensordata_lookup[key]                    
                    if vsens.BeingProcessed == False:
                        can_process = vsens.check_conditions_for_algo_process(True)

                        if can_process:
                            stream_process_th = threading.Thread(target=vsens.process_burst, args=(), daemon=True)
                            stream_process_th.start()
        except Exception as ex:
            print(f"Error in method: main.py - time_based_data_processing, with ex: {ex}")
        finally:
            time.sleep(60)

def clear_objects():
    while True:
        try:
            v_data.CommonFeatures.delete_unusedobjects()
        except Exception as ex:
            print(f"Error in method: main.py - clear_objects, with ex: {ex}")
        finally:
            time.sleep(45)

main_start()

publish_thread = threading.Thread(target=publish_data, args=(), daemon=True)
publish_thread.start()

dp_thread = threading.Thread(target=time_based_data_processing, args=(), daemon=True)
dp_thread.start()

objclear_thread = threading.Thread(target=clear_objects, args=(), daemon=True)
objclear_thread.start()

while True:
    if v_helper.helper.data_queue.empty() == False:
        try:
            input_data = v_helper.helper.data_queue.get()
            if len(input_data) == 2:
                topic = input_data[0]
                raw_data = input_data[1]
                if topic == "se_poc/rpm":
                    if raw_data == "0":
                        v_data.CommonFeatures.simulator_rpm = 0
                    else:
                        v_data.CommonFeatures.simulator_rpm = float(raw_data)
                    continue

                topic_data = v_data.CommonFeatures.topics_lookup[topic]
                if topic_data is not None:
                    equipment_id = topic_data['E']
                    sensor_id = topic_data['S']
                    tag_type = topic_data['T']

                    vsens = None
                    if sensor_id in v_data.CommonFeatures.sensordata_lookup:                        
                        vsens = v_data.CommonFeatures.sensordata_lookup[sensor_id]

                    if vsens is None:
                        vsens = v_data.VsensStreamProcessor(sensor_id, equipment_id)
                        print(f"creating object for {sensor_id}")
                        if vsens.update_dataset() is None:
                            continue
                         
                        v_data.CommonFeatures.sensordata_lookup[sensor_id] = vsens

                    if vsens.TempStore is None:
                        vsens.axis_selection()
                    dataoutput=vsens.axisdetails(equipment_id,sensor_id)
                    vsens.store_data(tag_type, raw_data)

                    can_process = vsens.check_conditions_for_algo_process()

                    if can_process:
                        stream_process_th = threading.Thread(target=vsens.process_burst, args=(), daemon=True)
                        stream_process_th.start()                    
                else:
                    main_logger.error(
                        f"topic {topic} is not available in equipment store")
            else:
                main_logger.error(
                    f"Invalid data received {input_data}", exc_info=True)
        except Exception as ex:
            main_logger.error(
                f"Error while processing the data dequeue with error: {ex}", exc_info=True)
        #finally:
            #time.sleep(0.005)


# TODO handle the stoping of application
'''
def stop_processing():
    #   stop the hosted flask api
    #   kill all long running threads
    #   release all the resources
    #   kill main thread
    pass
'''

# hi this is purbasha again