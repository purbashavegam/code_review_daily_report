from Scripts.Trending.report.ExtractMetaData import ExtractMetaData
from Scripts.Trending.report.ExtractSensorData import ExtractSensorData
from Scripts.Trending.report.AverageCalculator import TrendGenerator
from Scripts.Trending.alert.MQTT import TrendsMqtt
from logging.handlers import RotatingFileHandler
import pytz
VERSION = '1.0'
import errno
import os
import threading
import logging
import time
import json
import datetime
from numpy import nan
from datetime import datetime, timezone, timedelta
import psutil
import sched
# trends_json = "C:\\Trends_services\\Trends.json"
# # trends_json = "C:/Trends_services/Trends.json"

# with open('Alert.json') as json_file:   C:\Users\Public
#     Alert_Config = json.load(json_file)

# config_filename = "Vegam_MQTT.json"  # Replace with your JSON file path
# with open(config_filename, 'r') as readfile:
#     main_config = json.load(readfile)


log_folder_path = 'logs'
if not os.path.exists(log_folder_path):
    try:
        os.makedirs(log_folder_path)
        print(f'Created "{log_folder_path}" folder.')
    except Exception as e:
        print(f'Error creating "{log_folder_path}" folder: {str(e)}')

logger = logging.getLogger()
log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s -' \
             ' %(message)s'
logging.basicConfig(
    format=log_format,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

file_handler = RotatingFileHandler(
    'logs/trends_alert.log', maxBytes=200 * 1024 * 1024, backupCount=10, mode='a'
)
file_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(file_handler)



class AlertGeneratorTrend:
    # config_file_path = r'../report/TrendGenerator_Config.json'
    FIRST_EXECUTION_LOCK = threading.Lock()  # Lock for thread-safe access to first_execution
    # INIT_LOCK = threading.Lock()
    FIRST_EXECUTION = True
    RAW_DATA_WILDCARD_TOPIC = '+/MA/#'
    def __init__(self,config_json):
        try:
            self.filepath = config_json#config_filename


            with open(self.filepath,'r') as json_file:
                self.Trends_Config = json.load(json_file)

            self.cache_time = int(self.Trends_Config["trends"]["data_window_startup_hr"]*3600)# 180  # get from json , time in seconds
            print(self.cache_time)

            self.service_initiated = True
            self.mac_id = None
            self.area_check = self.Trends_Config["trends"]["area_check"]
            self.metadata_extractor =ExtractMetaData(self.Trends_Config["trends"]["vmaint_api"],self.cache_time,self.area_check)# ExtractMetaData(Alert_Config["vmaint_api"])
            self.sensor_data_extract = ExtractSensorData(self.Trends_Config["trends"]["vegam_view_prod_api"])#ExtractSensorData(Alert_Config["api_url"],self.metadata_extractor)
            # self.sensor_data_extract = ExtractSensorData(self.Trends_Config["trends"]["api_url"],self.metadata_extractor)
            self.list_of_tags_macids = []
            self.first_execution = True  #flag to track the first execution
            self.first_execution_schedule = True
            self.previous_end_time = None

            self.mqtt_object_trend = TrendsMqtt(self.filepath, self.on_mqtt_connected,service_name="TrendsMQTT") #add mac id
            self.micro_service_name = self.mqtt_object_trend.json_handler_object.get_property(
                "microservice_name")
            self.mqtt_object_trend.add_subscribe_data(self.RAW_DATA_WILDCARD_TOPIC,self.on_moving_avg_received)

            # self.config_file_path = r'../report/TrendGenerator_Config.json' #for trend algos
            # for now not using this. but need to add this as json later -->19th dec getting ps actual code

            # schedule_thread = threading.Thread(target=self.start_tasks, name="Trends Alerts")  # Start the scheduled tasks in a separate thread
            # schedule_thread.start()

            logger.info("Initialization complete...")
        except Exception as e:
            logging.error(f"An error occurred during initialization in AlertGeneratorTrend: {str(e)}")

    def get_metadata_from_vamint_api_for_alert(self):
        # print("start of meta data getting method in thread..",datetime.now())
        logger.info(f"start of meta data getting method in thread..----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            # self.metadata_extractor.get_metadata_from_api()
            # print("okkkk...")
            list_of_tags_with_macids =self.metadata_extractor.get_mac_ids_tags_for_alret()
            self.list_of_tags_macids = list_of_tags_with_macids
            # print("Yes, it happened.")
            logger.info("list_of_tags_with_macids is being returned, len of the list_of_tags_with_macids is"+str(len(list_of_tags_with_macids)))
            # print(list_of_tags_with_macids)
            return list_of_tags_with_macids

        except Exception as e:
            print(f"Error in get_metadata_from_vamint_api_for_alert: {e}")

    def get_save_vrms_data_trend_process_mqtt_publish(self):
        try:
        # global current_time #pm test
            cycle_start_time = int(time.time())
            # Get initial memory usage
            initial_memory = psutil.virtual_memory().percent
            initial_memory_usage = psutil.virtual_memory().used

            global end_time
            input_data = self.list_of_tags_macids
            # logger.info("this is input data....."+str(input_data))

            current_time_before_process = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(
                f"START of the CYCLE - getting vrms data and processing sensors: current time is : {current_time_before_process}")

            current_time = int(time.time() * 1000)  # pm
            end_time = current_time  # pm

            if self.FIRST_EXECUTION:
                # first execution on startup
                logger.info("this is first time execution.....")
                start_time = current_time - self.Trends_Config["trends"][
                    "data_window_startup_hr"] * 60 * 60 * 1000  # One day before the current time #pm test
                self.FIRST_EXECUTION = False  # for subsequent executions,making the flag to False

            else:
                logger.info("this is next time execution.....")
                # Subsequent hourly executions
                # start_time = self.previous_end_time
                start_time = current_time - self.Trends_Config["trends"]["data_window_in_scheduler_hr"] * 60 * 60 * 1000

            for sensor_details in input_data: # what if input data is empty --????? have if else -- pm
                # print(sensor_details)
                key = next(iter(sensor_details.keys()))
                mac_id = key  # "F44F92D7B58C"# key
                # print(key)

                topic_values = [item['Topic'] for item in sensor_details[key]]
                # print(topic_values)

                logger.info(str(start_time)+str(end_time)+"----this is start time , end time in unix milli seconds")
                payload = {
                    "historyDataParamter": [
                        {"signalIds": topic_values, "fromTime": start_time, "toTime": end_time}
                    ]
                }
                # logger.info("Start getting data for sensor mac id:"+str(mac_id))
                logger.info(payload)
                logger.info(
                    f"start of getting sensor data for  {mac_id} :----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                sensor_data_start_time = int(time.time())
                vrms_temp_data = self.sensor_data_extract.fetch_vrms_temp_data(payload)
                logger.info(f"Fetched VRMS Data for Signal IDs {topic_values}:")
                sensor_data_end_time = int(time.time())
                fetch_time = sensor_data_end_time - sensor_data_start_time
                logger.info(f'Data fetching time for {mac_id} is {fetch_time} seconds')


                # Extract v and t data
                logger.info("len of vrms data from vegam view: "+str(len(vrms_temp_data)))
                if len(vrms_temp_data) > 0:

                    extracted_data = self.sensor_data_extract.extract_v_and_t_from_api_data(vrms_temp_data)

                    sheet_name_prefix = f'Sheet'
                    # output_file_prefix = f'C:/Trends_services/outputs/vrms_data'  #saving in output folder
                    output_file_prefix = f'C:/Vegam/Trends_alert/outputs/vrms_data'  #saving in output folder
                    # output_folder = 'outputs'
                    # vrms_data_folder = 'temp_vrms_data'
                    # desired_path = os.path.join(output_folder, vrms_data_folder)
                    self.make_sure_path_exists(output_file_prefix)
                    self.sensor_data_extract.save_data_to_excel_for_alert(extracted_data, output_file_prefix, sheet_name_prefix,mac_id)

                    # ps code...

                    trends_obj = TrendGenerator(start_time, end_time, mac_id,self.Trends_Config["trends"]["data_window_in_scheduler_hr"],self.Trends_Config["trends"]["data_window_startup_hr"])

                    # sp code...


                    self.mqtt_publish_alert(trends_obj)
                    logger.info(f"End of processing and publishing for   {mac_id}----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    self.previous_end_time = end_time  # save the end_time for the next execution
                    # print(f"All separated values saved successfully.")
                    logger.info("All separated values saved successfully.")

                else:
                    logger.info(
                        f"VEGAM VIEW API is returing empty result for sensor: {mac_id}, payload is:{payload} and current time is:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                # current_time_after_process =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"END of the CYCLE.. process meta data getting method in thread....----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            cycle_end_time = int(time.time())
            time_taken = cycle_end_time - cycle_start_time
            # Measure percentage_memory_change usage after the computation
            percentage_memory_change = psutil.virtual_memory().percent - initial_memory
            final_memory_usage = psutil.virtual_memory().used
            # Measure CPU usage after the computation
            cpu_usage = psutil.cpu_percent(interval=0.1)
            # Calculate memory consumption during function execution
            memory_consumption_change = final_memory_usage - initial_memory_usage
            # percentage_memory_consumption_change = (memory_consumption_change / initial_memory_usage) * 100
            # # Output metrics
            # print(f"Time taken for one cycle: {time_taken:.2f} seconds")
            # print(f"Start Time: {cycle_start_time}")
            # print(f"End Time: {cycle_end_time}")
            # print(f"Maximum CPU Utilization: {cpu_usage}%")
            # print(f"percentage_memory_change: {percentage_memory_change:.2f}%")
            # print("Memory Consumption change in mb: {:.2f} MB".format(memory_consumption_change / (1024 * 1024)))
            logging.info(f"Time taken for one cycle: {time_taken:.2f} seconds")
            logging.info(f"Start Time: {cycle_start_time}")
            logging.info(f"End Time: {cycle_end_time}")
            logging.info(f"Maximum CPU Utilization: {cpu_usage}%")
            logging.info(f"percentage_memory_change: {percentage_memory_change:.2f}%")
            logging.info("Memory Consumption change in mb: {:.2f} MB".format(memory_consumption_change / (1024 * 1024)))
            logger.info(f"Start Time for this cycle: {self.epoch_utc_to_ist_human_read_time(cycle_start_time)}")
            logger.info(f"End Time for this cycle : {self.epoch_utc_to_ist_human_read_time(cycle_end_time)}")







        #     #cycle = current_time_before_process-current_time_after_process
        #     #print(cycle,'CYCLE DURATION')
        #     cycle_end_time = int(time.time())
        #     time_taken = cycle_end_time - cycle_start_time
        #
        #     # Measure memory usage after the computation
        #     memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # Convert bytes to MB
        #
        #     # Measure peak memory usage after the computation
        #     peak_memory = psutil.virtual_memory().percent - initial_memory
        #     final_memory_usage = psutil.virtual_memory().used
        #
        #     # Measure CPU usage after the computation
        #     cpu_usage = psutil.cpu_percent()
        #
        #     # Calculate memory consumption during function execution
        #     memory_consumption = final_memory_usage - initial_memory_usage
        #
        # # # Output metrics
        # #     print(f"Time taken for one cycle: {time_taken:.2f} seconds")
        # #     print(f"Start Time: {cycle_start_time}")
        # #     print(f"End Time: {cycle_end_time}")
        # #     print(f"Maximum CPU Utilization: {cpu_usage:.2f}%")
        # #     print(f"Maximum Memory Consumption: {memory_usage:.2f} MB")
        # #     print(f"Maximum Memory Consumption Peak: {peak_memory:.2f}%")
        # #     print("Memory Consumption: {:.2f} MB".format(memory_consumption / (1024 * 1024)))
        #     logger.info(f"Time taken for one cycle: {time_taken:.2f} seconds")
        #     logger.info(f"Start Time epoch utc: {cycle_start_time}")
        #     logger.info(f"End Time epoch utc: {cycle_end_time}")
        #     logger.info(f"Start Time for this cycle: {self.epoch_utc_to_ist_human_read_time(cycle_start_time)}")
        #     logger.info(f"End Time for this cycle : {self.epoch_utc_to_ist_human_read_time(cycle_end_time)}")
        #     logger.info(f"Maximum CPU Utilization: {cpu_usage:.2f}%")
        #     logger.info(f"Maximum Memory Consumption: {memory_usage:.2f} MB")
        #     logger.info(f"Maximum Memory Consumption Peak: {peak_memory:.2f}%")
        #     logger.info("Memory Consumption: {:.2f} MB".format(memory_consumption / (1024 * 1024)))



        except Exception as e:
            print(f"Error in get_save_vrms_data_trend_process_mqtt_publish: {e}")
            logger.error(f"Error in get_save_vrms_data_trend_process_mqtt_publish: {e}")

    def get_save_vrms_data_trend_process_mqtt_publish_old_data(self):
        try:
            global current_time , payload, mac_id ##pm test
            # print("start of getting vrms data in thread____________________________________________________________________")
            # print("current time is", datetime.now())

            # need to add new code for time what chethan has asked for.. nested for loop??

            # current_time = int(time.time() * 1000)#pm

            print("this is self.first_execution:",self.FIRST_EXECUTION)

            if self.FIRST_EXECUTION:
                #first execution on startup
                print("first time done..") #Dec 27 2023 05:23:32
                current_time =1703738630000# int(datetime.strptime("14th December 2023 11:00 AM", "%dth %B %Y %I:%M %p").timestamp() * 1000)  # pm test

                # start_time = current_time - 24 * 60 * 60 * 1000  #One day before the current time #pm
                # start_time = current_time - 12 * 60 * 60 * 1000  #One day before the current time #pm test
                start_time = current_time - self.Trends_Config["trends"]["data_window_startup_hr"] * 60 * 60 * 1000  #One day before the current time #pm test
                end_time = current_time# pm test
                self.FIRST_EXECUTION = False  #for subsequent executions,making the flag to False

            else:
                print("second time done..")
                start_time = self.previous_end_time
                end_time = start_time + self.Trends_Config["trends"]["data_window_in_scheduler_hr"] * 60 * 60 * 1000

            input_data = self.list_of_tags_macids
            print("this is input data.....",input_data)
            for sensor_details in input_data:

                # have time here ...

                print(sensor_details)
                key = next(iter(sensor_details.keys()))
                # print(key)
                topic_values = [item['Topic'] for item in sensor_details[key]]
                print(topic_values)
                # topic_values_hc = ['17115', '17120', '17125']
                mac_id =key# "F44F92D7B58C"# key

                payload = {
                    "historyDataParamter": [
                        {"signalIds": topic_values, "fromTime": start_time, "toTime": end_time}
                    ]
                }

                vrms_temp_data = self.sensor_data_extract.fetch_vrms_temp_data(payload)
                print(f"Fetched VRMS Data for Signal IDs {topic_values}:")

                # Extract v and t data
                logger.info(f"start of getting sensor data---{mac_id}:..----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(len(vrms_temp_data),"99999999999999999999999999999")
                if len(vrms_temp_data)>0:
                    extracted_data = self.sensor_data_extract.extract_v_and_t_from_api_data(vrms_temp_data)

                    sheet_name_prefix = f'Sheet'
                    # output_file_prefix = f'C:/Trends_services/outputs/vrms_data'  #saving in output folder
                    output_file_prefix = f'C:/Vegam/Trends_alert/outputs/vrms_data'  #saving in output folder
                    # output_folder = 'outputs'
                    # vrms_data_folder = 'temp_vrms_data'
                    # desired_path = os.path.join(output_folder, vrms_data_folder)
                    self.make_sure_path_exists(output_file_prefix)
                    self.sensor_data_extract.save_data_to_excel_for_alert(extracted_data, output_file_prefix, sheet_name_prefix,mac_id)

                    # ps code...

                    trends_obj = TrendGenerator(start_time, end_time, mac_id,self.Trends_Config["trends"]["data_window_in_scheduler_hr"],self.Trends_Config["trends"]["data_window_startup_hr"])
                    # sp code...
                    self.mqtt_publish_alert(trends_obj)
                    logger.info(f"end of publishing sensor data---{mac_id}: ..----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"All separated values saved successfully.")
                    logger.info("All separated values saved successfully.")
                else:
                    logger.info(
                        f"VEGAM VIEW API is returing empty result for sensor: {mac_id}, payload is:{payload} and current time is:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                self.previous_end_time = end_time #save the end_time for the next execution
                # print(f"All separated values saved successfully.")
                logger.info(
                    f"END of the CYCLE.. process meta data getting method in thread....----   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"Error in get_save_vrms_data_trend_process_mqtt_publish_old_data: {e}")
            logger.error(f"Error in get_save_vrms_data_trend_process_mqtt_publish_old_data: {e}")




    def epoch_utc_to_ist_human_read_time(self,time_epoch):
        try:
            # UTC timestamp int --> datetime object
            datetime_utc = datetime.utcfromtimestamp(time_epoch)
            # india time zone
            desired_timezone = pytz.timezone('Asia/Kolkata')

            #UTC datetime -> ist zone
            datetime_desired_timezone = datetime_utc.replace(tzinfo=pytz.utc).astimezone(desired_timezone)
            #datetime as a string
            human_readable_time = datetime_desired_timezone.strftime('%Y-%m-%d %H:%M:%S %Z')
            return  human_readable_time

        except Exception as e:
            logging.error(f"An error occurred in epoch_utc_to_ist_human_read_time: {str(e)}")
    # def on_moving_avg_received(self, client, userdata,message=0):
    def on_moving_avg_received(self, client, userdata, message):
        try:
            # topic="test/SensorData/AccelerometerX",payload='{"s": 100, "w": 10, "t": "timestamp", "d": [1, 2, 3]}'

            # {'X_Axis': 0.4741287866665474, 'Y_Axis': 0.5800497308752203, 'Z_Axis': 0.547458284784535,
            #  'Sensor MacID': 'EE0C38A63F6A', 'EndTime': '1702531800000'}

            # print("on_moving_avg_received message--------------------->",message)
            payload = message.payload

            # Extract topic
            topic = message.topic

            # Print or use the extracted information
            print(f"Received message on topic {topic}: {payload}")
        except Exception as e:
            logger.error("Error while on_moving_avg_received:" + str(e))

    def on_mqtt_connected(self):
        try:
            if self.service_initiated:
                msg = '%s v%s service is initialized at: %s' % (
                    self.mqtt_object_trend.microservice_name, VERSION, datetime.datetime.now())
                logging.info(msg)
            msg = '%s local MQTT connected successfully at: %s' % (
                self.mqtt_object_trend.microservice_name, datetime.datetime.now())
            logging.debug(msg)
        except Exception as e:
            logger.error(f"An error occurred during on_mqtt_connected in vel fft class: {str(e)}")


    def mqtt_publish_alert(self,trends_obj):
        output_from_trend_generator_dict = trends_obj.process_excel_data()
        # print(output_from_trend_generator_dict,"++++++++++++++++++RESULT FROM TREND GENERSTOR++++++++++++++++++++++++++++++++++")
        logger.info(str(output_from_trend_generator_dict)+":RESULT FROM TREND GENERATOR++++++++++++++++++++++++++++++++++")


        try:
            if len(output_from_trend_generator_dict) > 0 and output_from_trend_generator_dict is not None:
                # list_of_keys_of_output = []
                axes_messages = {}
                list_of_keys_of_output = list(output_from_trend_generator_dict.keys())
                for key in list_of_keys_of_output:
                    if key == "X_Axis" and output_from_trend_generator_dict["X_Axis"] != nan:
                        axes_messages[
                            "X"] = f"{output_from_trend_generator_dict.get('X_Axis')}$T${output_from_trend_generator_dict.get('EndTime', '')}"
                    if key == "Y_Axis" and output_from_trend_generator_dict["Y_Axis"] != nan:
                        axes_messages[
                            'Y'] = f"{output_from_trend_generator_dict.get('Y_Axis')}$T${output_from_trend_generator_dict.get('EndTime', '')}"
                    if key == "Z_Axis" and output_from_trend_generator_dict["Z_Axis"] != nan:
                        axes_messages[
                            'Z'] = f"{output_from_trend_generator_dict.get('Z_Axis')}$T${output_from_trend_generator_dict.get('EndTime', '')}"

                # axes_messages = {
                #     'X': f"{output_from_trend_generator_dict.get('X_Axis', None)}$T${output_from_trend_generator_dict.get('EndTime', '')}",
                #     'Y': f"{output_from_trend_generator_dict.get('Y_Axis', None)}$T${output_from_trend_generator_dict.get('EndTime', '')}",
                #     'Z': f"{output_from_trend_generator_dict.get('Z_Axis', None)}$T${output_from_trend_generator_dict.get('EndTime', '')}"
                # }
                # # axes_messages = {
                # #     'X': f"{output_from_trend_generator_dict.get('X_Axis', None)}$T${str(int(time.time() * 1000))}",
                # #     'Y': f"{output_from_trend_generator_dict.get('Y_Axis', None)}$T${str(int(time.time() * 1000))}",
                # #     'Z': f"{output_from_trend_generator_dict.get('Z_Axis', None)}$T${str(int(time.time() * 1000))}"
                # # }
                # for axis, message in axes_messages.items():
                #     topic_to_publish = f"{output_from_trend_generator_dict.get('Sensor MacID')}/MA/VRMS{axis}"  # Use 'Sensor MacID' dynamically in the topic
                #     self.mqtt_object_trend.publish(topic_to_publish, message, 2)


                # Publish messages to each axis topic with dynamic 'Sensor MacID'
                if len(axes_messages)>0:
                    for axis, message in axes_messages.items():
                        topic_to_publish = f"{output_from_trend_generator_dict.get('Sensor MacID')}/MA/VRMS{axis}"  # Use 'Sensor MacID' dynamically in the topic
                        if "nan" not in message:
                            self.mqtt_object_trend.publish(topic_to_publish, message,2)
                            logger.info(topic_to_publish + "----->" + message)
                        else:
                            logger.info(topic_to_publish+"---->nan present in data as no data present in db, so not publishing")
                            pass
                else:
                    logger.error(f"nothing to publish for mac id{output_from_trend_generator_dict.get('Sensor MacID')}")
            else:
                logger.error("output from trend generator is not correct.")
                # print("output from trend generator is not correct.")



        except Exception as ex:
            logger.error("error came in mqtt_publish_alert "+str(ex))

    def start_tasks(self):
        try:
            with self.FIRST_EXECUTION_LOCK:
                start_time = datetime.now()
                if hasattr(self, 'first_execution') and self.first_execution:
                    self.get_metadata_from_vamint_api_for_alert()
                    # self.get_save_vrms_data_trend_process_mqtt_publish_old_data()# pm test hystorical
                    self.get_save_vrms_data_trend_process_mqtt_publish()
                    self.first_execution = False
                else:
                    self.get_metadata_from_vamint_api_for_alert()
                    # self.get_save_vrms_data_trend_process_mqtt_publish_old_data()# pm test hystorical
                    self.get_save_vrms_data_trend_process_mqtt_publish()

                current_time = datetime.now()
                time_difference = (current_time - start_time).total_seconds()
                interval_time = self.Trends_Config["trends"]["data_window_in_scheduler_hr"]*3600


                delay = max(0, int(interval_time - (time_difference % interval_time))) #vm test/ prod test
                # delay = max(0, int(600 - (time_difference % 600)))# pm test hystorical

            # Schedule the tasks to run periodically every 10 minutes or 1 hr  by threding timer
            threading.Timer(delay, self.start_tasks).start()
            # threading.Timer(delay, self.start_tasks, args=("Trends Tasks",)).start() # how to rename new temp threads --> yet to explore

            # # using sched module --> yet to test properly
            # scheduler = sched.scheduler(time.time, time.sleep)
            # scheduler.enter(delay, 1, self.start_tasks, ())
            # scheduler.run()
        except Exception as e:
            logger.error(f"An unexpected error occurred in start_tasks method : {str(e)}")

    def run(self):
        try:
            tasks_thread = threading.Thread(target=self.start_tasks, name="Trends Tasks")
            tasks_thread.start()
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")

    """the start_tasks method is scheduled to run periodically using threading.Timer. 
    The start_tasks method itself creates a new thread each time it is scheduled. Therefore,
    a new thread will be created each time start_tasks is executed.
    
    
    When a threading.Timer expires, it creates a new thread to execute the specified function (in this case, start_tasks).
     The old thread is not automatically killed; instead, it completes the execution of the function and then terminates. 
     This means that multiple threads with the same function can exist concurrently.

    In current case, when the timer expires, a new thread is created to execute start_tasks. If the old thread from the 
    previous timer is still running, they will coexist briefly until the old thread completes its execution.
     Once the old thread completes, it will terminate.
    
    It's important to note that Python threads are managed by the Python Global Interpreter Lock (GIL), 
    which ensures that only one thread executes Python bytecode at a time. This can impact the effectiveness of using multiple 
    threads for parallelism, especially in CPU-bound tasks. If you are dealing with I/O-bound tasks, threads can still be beneficial. 
    If you need true parallelism for CPU-bound tasks, you might consider using multiprocessing or other concurrency approaches.
    #improvement#
    
    """





    @staticmethod
    def make_sure_path_exists(path):
        try:
            os.makedirs(path, exist_ok=True)
            # os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise




'''do we need to call vmaimt api call in every one hr ? or not --> sensor number won't get change anyway frequently.
so in every 24 hr for now -> check with chethan'''


if __name__ == "__main__":

    # trends_json = "C:\\Trends_services\\Trends.json" C:\Vegam\Trends_alert
    trends_json = "C:\\Vegam\\Trends_alert\\Trends.json"
    try:
        '''Check if the file exists'''
        if not os.path.isfile(trends_json):
            raise FileNotFoundError(f"File '{trends_json}' does not exist.")

        '''Check if the file is empty'''
        if os.path.getsize(trends_json) == 0:
            raise ValueError(f"File '{trends_json}' is empty.")

        AlertGeneratorTrendObj = AlertGeneratorTrend(config_json=trends_json)
        # Run the main method
        AlertGeneratorTrendObj.run()

    except FileNotFoundError as e:
        logger.error(str(e))
    except ValueError as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

