import sys
from numpy import array,testing,allclose
sys.path.append("D:/vegam_projects/GIT_works/Vegam_Analytics")
import os
import json
import pytest
from Software.src.AnalyticsVelFFT import AnalyticsVelFFT,logger
# from Software.src.AnalyticsMqtt import AnalyticsMqtt
import threading
from unittest.mock import Mock, patch, MagicMock
from unittest import mock

filepath = "C:\\VELO_FFT_service\\Vegam_MQTT.json"




@pytest.fixture
def analytics_object():
    return AnalyticsVelFFT(filepath)


# extract_sensor_mac_id method
def test_extract_sensor_mac_id():
    analytics_object = AnalyticsVelFFT(filepath)  # instance

    assert analytics_object.extract_sensor_mac_id("test/SensorData/AccelerometerX") == "test"
    assert analytics_object.extract_sensor_mac_id("another/SensorData/AccelerometerY") == "another"
    assert analytics_object.extract_sensor_mac_id("invalid/topic") is None


# extract_parameters method
def test_extract_parameters():
    analytics_object = AnalyticsVelFFT(filepath)  # instance

    payload = '{"s": 100, "w": 10, "t": "125626371", "d": [1, 2, 3]}'
    assert analytics_object.extract_parameters(payload) == (100, 10, "125626371", [1, 2, 3])

    payload = '{"s": null, "w": 10, "t": "timestamp", "d": [1, 2, 3]}'
    assert analytics_object.extract_parameters(payload) == (None, None, None, None)

    payload = '{"s": 100, "w": 10}'
    assert analytics_object.extract_parameters(payload) == (None, None, None, None)


def test_extract_axis():
    analytics_object = AnalyticsVelFFT(filepath)
    assert analytics_object.extract_axis("test/SensorData/AccelerometerX") == "X"
    assert analytics_object.extract_axis("another/SensorData/AccelerometerY") == "Y"
    assert analytics_object.extract_axis("invalid/topic") == None


# on_raw_data_received method
def test_on_raw_data_received():
    analytics_object = AnalyticsVelFFT(filepath)  # instance
    # Mock message object for testing
    class MockMessage:
        def __init__(self, topic, payload):
            self.topic = topic
            self.payload = payload

    '''import the mqtt.MQTTMessage class from the paho.mqtt.client library to create real MQTT message objects with payloads.
     This should resolve the decoding issue I was facing with the MockMessage object.'''
    message = MockMessage(topic="test/SensorData/AccelerometerX",payload=b'{"s": 100, "w": 10, "t": "45764", "d": [1, 2, 3]}')


    analytics_object.on_raw_data_received(client=None, userdata=None, message=message)
    assert analytics_object.sensor_raw_data_queue.qsize() == 1
    added_payload = analytics_object.sensor_raw_data_queue.get()
    assert added_payload["sensor_mac_id"] == "test"
    assert added_payload["axis"] == "X"
    assert added_payload["sampling_frequency"] == 100

    invalid_message = MockMessage(
        topic="invalid/topic",
        payload=b'{"s": 200, "w": 5, "t": "timestamp", "d": [4, 5, 6]}'
    )
    analytics_object.on_raw_data_received(client=None, userdata=None, message=invalid_message)
    assert analytics_object.sensor_raw_data_queue.qsize() == 0

    try:
        analytics_object.on_raw_data_received(client=None, userdata=None, message=message)
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")


def test_add_payload_to_queue():

    analytics_object = AnalyticsVelFFT(filepath)
    #sample payload dictionary
    sample_payload = {
        "sensor_mac_id": "test",
        "axis": "X",
        "sampling_frequency": 100,
        "window_size": 10,
        "time_stamp": "timestamp",
        "data": [1, 2, 3]
    }

    initial_queue_size = analytics_object.sensor_raw_data_queue.qsize()

    analytics_object.add_payload_to_queue(sample_payload)

    assert analytics_object.sensor_raw_data_queue.qsize() == initial_queue_size + 1

'''
#  add_payload_to_queue method
def test_add_payload_to_queue():

    analytics_object = AnalyticsVelFFT(filepath)
    payload_dict = {
        "sensor_mac_id": "test",
        "axis": "X",
        "sampling_frequency": 100,
        "window_size": 10,
        "time_stamp": "timestamp",
        "data": [1, 2, 3]
    }    #sample payload dictionary

    analytics_object.add_payload_to_queue(payload_dict)
'''








# sample data as a dictionary for testing avg_calc_of_sub_acc_fft_velo_fft_vrms
# {"acc_fft_1":[1,2,34,5,12,55],"vfft_1":[2,858,7474,39,45,54],"vrms_1":0.1234521,"acc_fft_2":[1,2,3,2,34,5],"vfft_2":[2,858,7474,122,234,39],"vrms_2":5.1234521}  now write code

sample_data = {
    "acc_fft_1": array([1, 2, 34, 5, 12, 55]),
    "vfft_1":array([2, 858, 7474, 39, 45, 54]),
    "vrms_1": 0.1234521,
    "acc_fft_2": array([1, 2, 3, 2, 34, 5]),
    "vfft_2": array([2, 858, 7474, 122, 234, 39]),
    "vrms_2": 5.1234521
}

# pytest function to test avg_calc_of_sub_acc_fft_velo_fft_vrms method
def test_avg_calc_of_sub_acc_fft_velo_fft_vrms():

    analytics_object = AnalyticsVelFFT(filepath)
    result = analytics_object.avg_calc_of_sub_acc_fft_velo_fft_vrms(sample_data)

    expected_result = {
        "acc_fft_avg": [1.0, 2.0, 18.5, 3.5, 23.0, 30.0],
        "vfft_avg": [2.0, 858.0, 7474.0, 80.5, 139.5, 46.5],
        "vrms_avg": 2.6234520999999997 #2.6239021
    }

    assert result == expected_result


def test_wrapper_acc_fft_velo_fft_vrms():

    analytics_object = AnalyticsVelFFT(filepath)

    # test inputs
    sensor_id = "purbasha"
    acc_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 6, 5, 4, 32, 27, 78, 54, 32, 2, 332, 23]
    sampling_frequency = 10
    windowsize = 4

    acc_fft_avg, vfft_avg, vrms_avg = analytics_object.wrapper_acc_fft_velo_fft_vrms(sensor_id, acc_data,
                                                                                     sampling_frequency, windowsize)

    expected_acc_fft_avg = [0.0, 26.698023574962956, 45.28]
    expected_vfft_avg = [0.0, 0.0, 0.0]
    expected_vrms_avg = 0.0

    # assert acc_fft_avg == expected_acc_fft_avg
    # assert vfft_avg == expected_vfft_avg
    # assert expected_vrms_avg == vrms_avg


    testing.assert_allclose(acc_fft_avg, expected_acc_fft_avg, rtol=1e-5)
    testing.assert_allclose(vfft_avg, expected_vfft_avg, rtol=1e-5)  # tolerance as needed how to use this?
    testing.assert_allclose(vrms_avg, expected_vrms_avg, rtol=1e-5)
    assert vrms_avg == expected_vrms_avg

def test_processed_data_condition_exists(analytics_object):
    assert hasattr(analytics_object, 'processed_data_condition')

def test_notify_exists(analytics_object):
    assert hasattr(analytics_object.processed_data_condition, 'notify')






#---------------------



# def test_processed_data_notification(analytics_object):
#     def notify_thread():
#         with analytics_object.processed_data_condition:
#             print("Waiting for condition...")
#             analytics_object.processed_data_condition.wait()
#             print("Notifying condition...")
#             analytics_object.processed_data_condition.notify()  # Notify the condition
#             print("Notified condition.")
#
#     notify_thread = threading.Thread(target=notify_thread)
#     notify_thread.start()
#
#     analytics_object.start_raw_data_processing_thread()
#     payload = {'sensor_mac_id': '12345', 'axis': 'X', 'sampling_frequency': 100, 'window_size': 10, 'time_stamp': '298836', 'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 6, 5, 4, 32, 27, 78, 54, 32, 2, 332, 23]}
#     analytics_object.add_payload_to_queue(payload)
#
#     notify_thread.join()
#
#     assert analytics_object.process_data_to_publish.qsize() == 1


#-------------------


#----

# def test_condition_wait_behavior(analytics_object):
#     def wait_thread():
#         with analytics_object.processed_data_condition:
#             while analytics_object.process_data_to_publish.empty():
#                 analytics_object.processed_data_condition.wait()
#             analytics_object.process_data_to_publish.get()
#
#     wait_thread = threading.Thread(target=wait_thread)
#     wait_thread.start()
#
#     # Simulate adding data to the queue
#     payload = {'sensor_mac_id': '12345', 'axis': 'X', 'sampling_frequency': 100, 'window_size': 10, 'time_stamp': 'timestamp', 'data': [1, 2, 3]}
#     analytics_object.add_payload_to_queue(payload)
#
#     wait_thread.join()
#
#     # Assert that the thread correctly waited and dequeued the data
#     assert analytics_object.process_data_to_publish.empty()














# #-----------------------------------------------------------------------------
# @pytest.mark.parametrize("payload, expected_processed_data_count", [
#     ({'sensor_mac_id': '12345', 'axis': 'X', 'sampling_frequency': 100, 'window_size': 10, 'time_stamp': '4539876', 'data': [1, 2, 3,1,3,5,6,78,4,32,21,34,53,24,5,4]}, 1),
#     ({'sensor_mac_id': '56789', 'axis': 'Y', 'sampling_frequency': 200, 'window_size': 5, 'time_stamp': '999999999', 'data': [4, 5, 6,7,8,5,4,3,2,5,6,54,33,2.3,95,432,11,2,3]}, 1)
# ])
# # @pytest.mark.parametrize("payload, expected_processed_data_count", [
# #     ({"s": 100, "w": 10, "t": "45764", "d": [1, 2, 3,1,3,5,6,78,4,32,21,34,53,24,5,4]}, 1),
# #     ({"s": 100, "w": 10, "t": "45764", "d": [4, 5, 6,7,8,5,4,3,2,5,6,54,33,2.3,95,432,11,2,3]}, 1)
# # ])
# def test_processed_data_notification(analytics_object, payload, expected_processed_data_count):
#     analytics_object.add_payload_to_queue(payload)
#     analytics_object.start_raw_data_processing_thread()
#
#     analytics_object.sensor_raw_data_processing_thread.join()
#     assert analytics_object.process_data_to_publish.qsize() == expected_processed_data_count
#
# def test_processed_data_empty(analytics_object):
#     assert analytics_object.process_data_to_publish.empty()
#
# def test_processed_data_wait(analytics_object):
#     def wait_thread():
#         with analytics_object.processed_data_condition:
#             analytics_object.processed_data_condition.wait()
#
#     wait_thread = threading.Thread(target=wait_thread)
#     wait_thread.start()
#     import time
#     time.sleep(1)
#     payload = {'sensor_mac_id': '12345', 'axis': 'X', 'sampling_frequency': 100, 'window_size': 10, 'time_stamp': 'timestamp', 'data': [1, 2, 3]}
#     analytics_object.add_payload_to_queue(payload)
#     wait_thread.join()
#     assert analytics_object.process_data_to_publish.qsize() == 1
#
# #-----------------------------------------------------------------
















#----------------------------------------------------------------------------
# def test_processed_data_notification(analytics_object):
#     payload_dict = {
#         'sensor_mac_id': '12345',
#         'axis': 'X',
#         'sampling_frequency': 100,
#         'window_size': 10,
#         'time_stamp': '123465',
#         'data': [1, 2, 3]
#     }
#
#     # Start the processing thread
#     analytics_object.start_raw_data_processing_thread()
#     # Add payload to the queue
#     analytics_object.add_payload_to_queue(payload_dict)
#     # Wait for the processing thread to complete
#     print("yooo")
#     analytics_object.sensor_raw_data_processing_thread.join()
#     print("huhahaha")
#     # Assert that the processed data has been published
#     assert analytics_object.process_data_to_publish.qsize() > 0
#
# def test_processed_data_empty(analytics_object):
#
#     assert analytics_object.process_data_to_publish.empty()
#
# def test_processed_data_wait(analytics_object):
#
#     def wait_thread():
#         with analytics_object.processed_data_condition:
#             analytics_object.processed_data_condition.wait()
#
#
#     wait_thread = threading.Thread(target=wait_thread)
#     wait_thread.start()
#
#
#     import time
#     time.sleep(1)
#
#
#     payload_dict = {
#         'sensor_mac_id': '12345',
#         'axis': 'X',
#         'sampling_frequency': 100,
#         'window_size': 10,
#         'time_stamp': 'timestamp',
#         'data': [1, 2, 3]
#     }
#     analytics_object.add_payload_to_queue(payload_dict)
#
#
#     wait_thread.join()
#
#
#     assert analytics_object.process_data_to_publish.qsize() > 0
#
#
# ---------------------------------------------------------------------------
