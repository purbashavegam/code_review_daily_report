import time
import math
import numpy as np
import scipy.signal as sg
import logging
from AnalyticsMqtt import AnalyticsMqtt
# from AnalyticsMqtt import AnalyticsMqtt
from logging.handlers import RotatingFileHandler
import os

import sys
import json
import re
from datetime import datetime
from queue import Queue
from threading import Thread
import threading


VERSION = '1.0'

'''
backup of the json which is running for testing :

{
    "broker_details": {
        "broker_username": "",
        "broker_password": "",
        "broker_ip": "176.9.144.238",
        "broker_port": 1883,
        "ssl_auth_enabled": 0,  
        "ssl_auth_details": {
            "ca_certificate": "",
            "client_certificate":"",
            "client_key_file": "",
            "keyfile_password": ""
        }
    },

   "microservice_name" : "Velo_fft_microservice"
}

'''
#log_folder_path = 'logs'
log_folder_path = 'logs_40'

# Check if the "logs" folder exists, if not, create it
if not os.path.exists(log_folder_path):
    try:
        os.makedirs(log_folder_path)
        print(f'Created "{log_folder_path}" folder.')
    except Exception as e:
        print(f'Error creating "{log_folder_path}" folder: {str(e)}')

logger = logging.getLogger()
# log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s\n%(message)s'
# '%(asctime)s %(levelname)-8s [%(pathname)s:%(lineno)d in function %(funcName)s] %(message)s',
log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s -' \
             ' %(message)s'
logging.basicConfig(
    format=log_format,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

file_handler = RotatingFileHandler(
    'logs_40/AnalyticsVelFFT_ssl.log', maxBytes=200 * 1024 * 1024, backupCount=10, mode='a'
)
# file_handler = RotatingFileHandler(
#     'logs/AnalyticsVelFFT_ssl.log', maxBytes=200 * 1024 * 1024, backupCount=10, mode='a'
# )
# stream_handler = logging.StreamHandler()  # logging to console
file_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(file_handler)


class AnalyticsVelFFT:
    RAW_DATA_WILDCARD_TOPIC = '+/SensorData/#'

    VEL_RMS_MUL_CONST = (1.41) / (2 * 3.141)
    G_CONST = 9.81
    constant = 1000
    ZERO = 0
    ONE = 1
    TWO = 2

    def __init__(self, filepath):
        try:
            self.service_initiated = True
            self.filepath = filepath
            timestamp_for_log = time.time()
            datetime_obj = datetime.fromtimestamp(timestamp_for_log)  # Unix timestamp -> datetime object
            human_readable_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

            logger.debug("Analytics VEL FFT service is started at %s", human_readable_time)
            self.sensor_raw_data_queue = Queue()  # Initialize the Queue for sensor raw data #q1
            self.sensor_raw_data_processing_thread = Thread(
                target=self.process_sensor_raw_data, name="SensorRawDataThread")  # Initialize the processing thread
            self.sensor_raw_data_processing_thread.daemon = True  # Set the thread as daemon to exit when the main program exits

            self.analytics_vel_fft_object = AnalyticsMqtt(
                filepath, self.on_raw_data_received, self.on_mqtt_connected,
                service_name="AnalyticsMQTT")
            self.micro_service_name = self.analytics_vel_fft_object.json_handler_object.get_property(
                "microservice_name")
            self.sub_topic_dict = {}
            self.analytics_vel_fft_object.add_subscribe_data(self.RAW_DATA_WILDCARD_TOPIC, self.on_raw_data_received)
            # self.assign_sub_topic_dict()
            self.processed_data_condition = threading.Condition()  # pm add new
            self.process_data_to_publish = Queue()  # q2
            self.publish_thread_obj = Thread(target=self.publish_processed_data, name="PublishThread")
            self.publish_thread_obj.daemon = True
            self.st = self.et = None

            self.start_raw_data_processing_thread()  # Start the processing thread
            self.publish_thread()  # Start the publish thread
            logger.info("Service initialized and threads started..")
            logger.info(f'q2 size: {str(self.process_data_to_publish.qsize())}')

        except Exception as e:
            logging.error(f"An error occurred during initialization in AnalyticsVelFFT: {str(e)}")

    def start_raw_data_processing_thread(self):  # Start the processing thread
        try:
            self.sensor_raw_data_processing_thread.start()
        except Exception as e:
            logging.error(f"An error occurred during start_raw_data_processing_thread: {str(e)}")

    def publish_thread(self):  # Start the publish thread
        try:
            self.publish_thread_obj.start()
        except Exception as e:
            logging.error(f"An error occurred during publish_thread method: {str(e)}")

    def on_mqtt_connected(self):
        try:
            if self.service_initiated:
                msg = '%s v%s service is initialized at: %s' % (
                    self.analytics_vel_fft_object.microservice_name, VERSION, time.time())
                logging.info(msg)
            msg = '%s local MQTT connected successfully at: %s' % (
                self.analytics_vel_fft_object.microservice_name, time.time())
            logging.debug(msg)
        except Exception as e:
            logger.error(f"An error occurred during on_mqtt_connected in vel fft class: {str(e)}")

    def extract_sensor_mac_id(self, topic):
        try:
            sensor_name_match = re.search(r'(.*?)/SensorData/Accelerometer([XYZ])', topic)
            if sensor_name_match:
                logger.info(f"This topic's data came as input to the service: {topic}")
                self.st = time.time()  # for supriya time duration check. start time end time should be instance variable
                # start_time = time.time()
                print(self.st, "-------------this is st")  # for supriya time duration check.
                return sensor_name_match.group(1)
            else:
                logger.error(f"Failed to extract Sensor MAC ID from topic: {topic}")
                return None
        except Exception as e:
            logger.error(f"An error occurred during extract_sensor_mac_id: {str(e)}")

    def extract_parameters(self, payload):
        try:
            payload_dict = json.loads(payload)
            sampling_frequency = payload_dict.get("s")
            window_size = payload_dict.get("w")
            time_stamp = payload_dict.get("t")
            data = payload_dict.get("d")

            if all([sampling_frequency, window_size, time_stamp, data]):
                return sampling_frequency, window_size, time_stamp, data
            else:
                missing_parameters = []
                if not sampling_frequency:
                    missing_parameters.append("sampling_frequency")
                if not window_size:
                    missing_parameters.append("window_size")
                if not time_stamp:
                    missing_parameters.append("time_stamp")
                if not data:
                    missing_parameters.append("data")

                logger.error("Packet is dropped as incomplete or missing parameters in payload: %s",
                             ", ".join(missing_parameters))
                return None, None, None, None

        except Exception as e:
            logger.error("Error while extracting parameters:" + str(e))
            return None, None, None, None

    def extract_axis(self, topic):
        try:
            if topic:
                if topic[-1] == "X" or topic[-1] == "Y" or topic[-1] == "Z":  # new change
                    return topic[-1]
            else:
                return None
        except Exception as e:
            logger.error("Error while extract_axis:" + str(e))

    def on_raw_data_received(self, client, userdata, message):
        try:
            # topic="test/SensorData/AccelerometerX",payload='{"s": 100, "w": 10, "t": "timestamp", "d": [1, 2, 3]}'
            topic = message.topic

            payload = message.payload.decode("utf-8")
            sensor_mac_id = self.extract_sensor_mac_id(topic)
            axis = self.extract_axis(topic)
            sampling_frequency, window_size, time_stamp, data = self.extract_parameters(payload)

            if all([sensor_mac_id, axis, sampling_frequency, window_size, time_stamp, data]):
                payload_dict = {
                    "sensor_mac_id": sensor_mac_id,
                    "axis": axis,
                    "sampling_frequency": sampling_frequency,
                    "window_size": window_size,
                    "time_stamp": time_stamp,
                    "data": data
                }
                self.add_payload_to_queue(payload_dict)
        except Exception as e:
            logger.error("Error while on_raw_data_received:" + str(e))

    def add_payload_to_queue(self, payload_dict):  # q1
        try:
            self.sensor_raw_data_queue.put(payload_dict)
            logger.info(
                str(self.sensor_raw_data_queue.qsize()) + "<--one burst data came and stored in queue(q1)")
        except Exception as e:
            logger.error("Error while add_payload_to_queue:" + str(e))

    def publish_processed_data(self):
        while True:
            try:
                with self.processed_data_condition:  # new code add, pm
                    while self.process_data_to_publish.empty():
                        self.processed_data_condition.wait()

                    processed_data_from_queue_to_publish = self.process_data_to_publish.get()  # Get q2 data
                    if processed_data_from_queue_to_publish:
                        ''' Publish the processed data using the MQTT client '''

                        sampling_freqn = processed_data_from_queue_to_publish["sampling_frequency"]
                        timestamp = processed_data_from_queue_to_publish["time_stamp"]
                        vfft_res = processed_data_from_queue_to_publish["velocityfft"]  # <class 'numpy.ndarray'>
                        acc_fft_res = processed_data_from_queue_to_publish["acc_fft"]  # <class 'numpy.ndarray'>
                        vrms_res = processed_data_from_queue_to_publish["vrms"]  # <class 'float'>

                        vfft_topic_to_publish = processed_data_from_queue_to_publish["sensor_mac_id"] + "/VelocityFFT" + \
                                                processed_data_from_queue_to_publish["axis"]
                        acc_fft_topic_to_publish = processed_data_from_queue_to_publish["sensor_mac_id"] + "/FFT" + \
                                                   processed_data_from_queue_to_publish["axis"]
                        vrms_topic_to_publish = processed_data_from_queue_to_publish["sensor_mac_id"] + "/VelocityRMS" + \
                                                processed_data_from_queue_to_publish["axis"]
                        logger.info(
                            "topics which will publish:" + vfft_topic_to_publish + acc_fft_topic_to_publish + vrms_topic_to_publish)

                        vftt_payload_sub = {"n": sampling_freqn, "f": vfft_res}
                        acc_ftt_payload_sub = {"n": sampling_freqn, "f": acc_fft_res}

                        vftt_payload = json.dumps(vftt_payload_sub) + "$T$" + timestamp
                        acc_ftt_payload = json.dumps(acc_ftt_payload_sub) + "$T$" + timestamp
                        vrms_payload = str(vrms_res) + "$T$" + timestamp
                        qos = 2  # Quality of Service ->QoS level , needed as 2 here.
                        # print(self.process_data_to_publish.qsize(), "omg")
                        # if self.process_data_to_publish.qsize() > 0:  # new add purbasha
                        self.analytics_vel_fft_object.publish(vfft_topic_to_publish, vftt_payload, qos)
                        self.analytics_vel_fft_object.publish(acc_fft_topic_to_publish, acc_ftt_payload, qos)
                        self.analytics_vel_fft_object.publish(vrms_topic_to_publish, vrms_payload, qos)
                        # else:
                        #     pass

                        current_time_after_publish = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        logger.info(
                            f'Time after ACC and v fft and vrms data publishing is: {current_time_after_publish} and after publishing q2 size: {str(self.process_data_to_publish.qsize())}')

                    else:
                        logger.info("Payload data not present. Check queue 1 status.")
                    time.sleep(0.5)
                    logger.info("less time sleep.. line 266")
            except Exception as e:
                logger.critical('Exception occurred while publishing procesded sensor raw data', exc_info=True)

    def get_acc_fft_velo_fft_vrms(self, acc_data, sampling_frequency):
        try:
            if acc_data is not None and sampling_frequency is not None:

                acc_data = np.array(acc_data)
                window_size_vel = number_of_samples_vel = len(acc_data)
                detrended_signal = sg.detrend(acc_data)
                # fft calculation
                fft_1 = np.fft.rfft(detrended_signal)
                fft_abs_w_nm = np.absolute(fft_1)
                fft_abs_w_nm[0] = self.ZERO

                acc_fft_bins = fft_abs_w_nm[:(window_size_vel // self.TWO + self.ONE)]

                acc_fft_abs_nm = acc_fft_bins * self.TWO / len(acc_data)

                xf = np.fft.rfftfreq(len(acc_data), d=1. / sampling_frequency)

                # calculate velocity fft from acc data
                velocity_fft = fft_abs_w_nm * self.G_CONST * self.constant / (1j * self.TWO * np.pi * xf)
                velo_fft_abs_w_nm = np.absolute(velocity_fft)
                velo_fft_abs_w_nm[:5] = self.ZERO
                # NORMALIZATION OF DATA
                velo_fft_abs_nm = velo_fft_abs_w_nm * self.TWO / len(acc_data)
                fft_sample_number = self.ZERO
                xf_vel_summation = self.ZERO
                frequency = self.ZERO
                fft_scale = sampling_frequency / number_of_samples_vel  # ch
                fft_output_len = number_of_samples_vel / self.TWO  # ch

                while frequency < 1.0:
                    frequency = fft_scale * fft_sample_number * 1.0
                    fft_sample_number += self.ONE

                while fft_sample_number < fft_output_len:
                    if acc_fft_bins[fft_sample_number] != self.ZERO:
                        freq = fft_scale * fft_sample_number * 1.0
                        rms_i = (acc_fft_bins[fft_sample_number] / freq)
                        sqar_rms_i = rms_i * rms_i
                        xf_vel_summation += sqar_rms_i
                    fft_sample_number += self.ONE

                # vrms calc
                vrms = math.sqrt(xf_vel_summation)
                vrms /= number_of_samples_vel
                vrms *= (self.G_CONST * self.constant) * self.VEL_RMS_MUL_CONST

                return acc_fft_abs_nm, velo_fft_abs_nm, vrms
            else:
                raise ValueError("data_improer")
        except Exception as e:
            logger.error(
                "error in get_acc_fft_velo_fft_vrms method" + str(e))  # , exc_info=True --> this alos can be done

    def avg_calc_of_sub_acc_fft_velo_fft_vrms(self, dictionary_contains_splited_calculated_stuff):
        try:
            dict_avg_values = {}
            acc_fft_sum = vfft_sum = None
            acc_fft_count = vfft_count = vrms_count = 0
            vrms_sum = 0.0

            for key, value in dictionary_contains_splited_calculated_stuff.items():
                if "acc_fft" in key:
                    if isinstance(value, np.ndarray):
                        acc_fft_count += 1
                        if acc_fft_sum is None:
                            acc_fft_sum = value
                        else:
                            acc_fft_sum = [acc_fft_sum[i] + value[i] for i in range(len(value))]

                elif "vfft" in key:
                    if isinstance(value, np.ndarray):
                        vfft_count += 1
                        if vfft_sum is None:
                            vfft_sum = value
                        else:
                            vfft_sum = [vfft_sum[i] + value[i] for i in range(len(value))]

                elif "vrms" in key:
                    if isinstance(value, (int, float)):
                        vrms_count += 1
                        vrms_sum += value

            if acc_fft_sum is not None and acc_fft_count > 0:  # Calc --> the average of the acc_fft lists element-wise
                acc_fft_avg = [acc_fft_sum[i] / acc_fft_count for i in range(len(acc_fft_sum))]
            else:
                acc_fft_avg = None

            if vfft_sum is not None and vfft_count > 0:
                vfft_avg = [vfft_sum[i] / vfft_count for i in range(len(vfft_sum))]
            else:
                vfft_avg = None

            if vrms_count > 0:
                vrms_avg = vrms_sum / vrms_count
            else:
                vrms_avg = None

            dict_avg_values["acc_fft_avg"] = acc_fft_avg

            dict_avg_values["vfft_avg"] = vfft_avg

            dict_avg_values["vrms_avg"] = vrms_avg
            logger.info("coming back from avg_calc_of_sub_acc_fft_velo_fft_vrms method to wrapper.")

            return dict_avg_values
        except Exception as e:
            logger.error(
                "error in avg_calc_of_sub_acc_fft_velo_fft_vrms method" + str(
                    e))

    def wrapper_acc_fft_velo_fft_vrms(self, sensor_id, acc_data, sampling_frequency, windowsize):
        try:
            result_store = {}
            if acc_data is not None and sampling_frequency is not None and windowsize is not None:
                logger.info("sensor id :" + str(sensor_id))

                logger.info("len of raw acc_data,type of raw acc_data,window size inside wrapper method:" + str(
                    len(acc_data)) + str(
                    type(acc_data)) + str(windowsize))
                no_of_sub_window_size = int(len(acc_data) / windowsize)
                no_of_sample_will_not_get_processed = len(acc_data) - (windowsize * no_of_sub_window_size)
                '''corner test case'''
                if no_of_sample_will_not_get_processed > 0:
                    logger.info("No of samples is getting dropped as window size is higher:" + str(
                        no_of_sample_will_not_get_processed))
                logger.info("number of sub windows:" + str(no_of_sub_window_size))

                for iteration_times in range(1, no_of_sub_window_size + 1):
                    start_index = (iteration_times - 1) * windowsize
                    end_index = iteration_times * windowsize
                    acc_sub_data_list = acc_data[start_index:end_index]

                    result_store["acc_fft_" + str(iteration_times)], result_store["vfft_" + str(iteration_times)], \
                    result_store["vrms_" + str(iteration_times)] = self.get_acc_fft_velo_fft_vrms(acc_sub_data_list,
                                                                                                  sampling_frequency)

                get_avg_value = self.avg_calc_of_sub_acc_fft_velo_fft_vrms(result_store)

                acc_fft_avg = get_avg_value["acc_fft_avg"]

                vfft_avg = get_avg_value["vfft_avg"]

                vrms_avg = get_avg_value["vrms_avg"]
                logger.info("wrapper method gave values from avg method....")

                return acc_fft_avg, vfft_avg, vrms_avg
            else:
                raise ValueError("data_improper")
        except Exception as e:
            logger.error(
                "error in wrapper_acc_fft_velo_fft_vrms method" + str(e))  # , exc_info=True --> this alos can be done

    '''main processing loop running in the sensor_raw_data_processing_thread.
    It continuously checks for data in the queue and processes it.'''

    def process_sensor_raw_data(self):  # q2 add
        while True:
            mandatory_key_list = ['sensor_mac_id', 'axis', 'sampling_frequency', 'window_size', 'time_stamp', 'data']
            try:
                payload_dict = self.sensor_raw_data_queue.get()  # this is getting data from q1
                if payload_dict:
                    '''Check if any of the required variables is None, missing, not in right format - corner case 
                    test 1-7 '''

                    payload_keys = list(payload_dict.keys())
                    missing_keys = [key for key in mandatory_key_list if key not in payload_keys]
                    '''missing or not check'''
                    if missing_keys:
                        logger.error("Packet dropped as the following element(s) are not present in payload_dict:")
                        for key in missing_keys:
                            logger.error(str(key) + "\n")
                    else:
                        logger.info("All mandatory keys are present in payload_dict as input.")
                        sensor_mac_id = payload_dict['sensor_mac_id']
                        axis = payload_dict['axis']
                        sampling_frequency = payload_dict['sampling_frequency']
                        window_size = payload_dict['window_size']
                        time_stamp = payload_dict['time_stamp']
                        raw_acc_data = payload_dict['data']
                        logger.info(f"Sensor mac id is      : {sensor_mac_id}")
                        logger.info(f"Axis is               : {axis}")
                        logger.info(f"Sampling frequency is : {sampling_frequency}")
                        logger.info(f"Window size is        : {window_size}")
                        logger.info(f"Time stamp is         : {time_stamp}")
                        logger.info(f"Len of raw_acc_data is: {len(raw_acc_data)}")

                        '''type check s, w, t --> s, w should be int , t will be str always, otherwise packet drop'''  # log add
                        wrong_type_variables = []
                        if type(sampling_frequency) != int:
                            wrong_type_variables.append('sampling_frequency')
                        if type(window_size) != int:
                            wrong_type_variables.append('window_size')
                        if type(time_stamp) != str:
                            wrong_type_variables.append('time_stamp')
                        if type(raw_acc_data) != list:
                            wrong_type_variables.append('raw_acc_data')

                        '''value none or not'''
                        missing_variables = []

                        if sensor_mac_id is None or sensor_mac_id == "" or sensor_mac_id == " ":
                            missing_variables.append('sensor_mac_id')
                        if axis is None or axis == "" or axis == " ":
                            missing_variables.append('axis')
                        if sampling_frequency is None or sampling_frequency == "" or sampling_frequency == " ":
                            missing_variables.append('sampling_frequency')
                        if window_size is None or window_size == "" or window_size == " ":
                            missing_variables.append('window_size')
                        if time_stamp is None or time_stamp == "" or time_stamp == " ":
                            missing_variables.append('time_stamp')
                        if raw_acc_data is None or type(raw_acc_data) != list:
                            missing_variables.append('raw_acc_data')

                        if missing_variables:
                            error_message = f"One or more required variables are missing or None: {', '.join(missing_variables)}. Data prossecing is not possible, packet is dropped"
                            logger.error(error_message)
                        elif wrong_type_variables:
                            error_message = f"One or more required variables type is wrong: {', '.join(wrong_type_variables)}. Data prossecing is not possible, packet is dropped"
                            logger.error(error_message)
                        elif len(raw_acc_data) < window_size:
                            logger.error("Raw data is lesser than windowsize, packet dropped.")
                        else:
                            dict_to_save_processed_data = {}

                            logger.info("processing is starting...")
                            acc_fft, velocityfft, vrms = self.wrapper_acc_fft_velo_fft_vrms(sensor_mac_id, raw_acc_data,
                                                                                            sampling_frequency,
                                                                                            window_size)
                            dict_to_save_processed_data['sensor_mac_id'] = sensor_mac_id
                            dict_to_save_processed_data['axis'] = axis
                            dict_to_save_processed_data['sampling_frequency'] = sampling_frequency
                            dict_to_save_processed_data['window_size'] = window_size
                            dict_to_save_processed_data['time_stamp'] = time_stamp
                            dict_to_save_processed_data['acc_fft'] = velocityfft
                            dict_to_save_processed_data['velocityfft'] = velocityfft
                            dict_to_save_processed_data['vrms'] = vrms

                            epoch_timestamp = int(
                                time_stamp) / 1000  # milliseconds --> seconds
                            human_readable_epoch_time_from_packet = datetime.fromtimestamp(epoch_timestamp).strftime(
                                '%Y-%m-%d %H:%M:%S')

                            logger.info("Epoch time we got from raw data---:" + str(time_stamp) + "-->" + str(
                                human_readable_epoch_time_from_packet))

                            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            logger.info(f'Current time is before publishing {current_time}')

                            self.process_data_to_publish.put(dict_to_save_processed_data)
                            logger.info(
                                str(self.process_data_to_publish.qsize()) + "<-------------size of q2 after processing")
                            logger.info(
                                str(self.sensor_raw_data_queue.qsize()) + "<----size of q1 after processing, it is end of the work")
                            self.et = time.time()  # for supriya time duration check. start time end time should be instance variable
                            time_dur = self.et - self.st
                            logger.info("time duration to complete one process [ one sensor one axis] will come...")
                            logger.info(time_dur)
                            logger.info("duration came")
                            with self.processed_data_condition:
                                self.processed_data_condition.notify()  # Notify the publishing thread that new data is available #new pm add

                            logger.info(
                                "raw data processing is done for this burst and published result in mqtt successfully.. line 510")



                else:
                    logger.info("payload not present.. please check q1 status")



            except Exception as e:
                logging.critical('Exception occurred while processing sensor raw data', exc_info=True)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("mqtt_subscribe_publish")

    config_filename = "C:\\VELO_FFT_service\\Vegam_MQTT.json" #"C:\\VELO_FFT_service\\Vegam_MQTT_40.json"#"C:\\VELO_FFT_service\\Vegam_MQTT.json"

    try:
        '''Check if the file exists'''
        if not os.path.isfile(config_filename):
            raise FileNotFoundError(f"File '{config_filename}' does not exist.")

        '''Check if the file is empty'''
        if os.path.getsize(config_filename) == 0:
            raise ValueError(f"File '{config_filename}' is empty.")

        Analytics = AnalyticsVelFFT(filepath=config_filename)


    except FileNotFoundError as e:
        logger.error(str(e))
    except ValueError as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")




