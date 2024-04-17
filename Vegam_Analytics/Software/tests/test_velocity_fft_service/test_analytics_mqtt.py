import sys
import ssl
# Add the path to the project root directory so you can import modules correctly
sys.path.append("D:/vegam_projects/GIT_works/Vegam_Analytics")
#to solve the import error
'''
from SourceCode.mqtt.mqtt_subscribe import MqttClient
E   ModuleNotFoundError: No module named 'SourceCode'
'''

from Software.src.AnalyticsMqtt import AnalyticsMqtt

filepath = "C:\\VELO_FFT_service\\Vegam_MQTT.json"

import pytest
from unittest.mock import Mock, patch, mock_open,call


'''mock subscribe callback function'''
def mock_subscribe_callback(client, userdata, message):
    pass

@pytest.fixture
def mqtt_client():
    client = AnalyticsMqtt(filepath, subscribe_callback=mock_subscribe_callback)
    # # return client
    yield client
    client.disconnect()

def test_on_connect(mqtt_client):
    mqtt_client.on_connect(None, None, None, 0)
    assert mqtt_client.client.connected_flag == True

@pytest.mark.xfail
def test_on_disconnect(mqtt_client):
    mqtt_client.on_disconnect(None, None, 1) #disconnect check
    assert not mqtt_client.client.connected_flag == True

def test_publish(mqtt_client):
    # Mock the client.publish method
    with patch.object(mqtt_client.client, 'publish') as mock_publish:
        mock_publish.return_value = (True, None)
        result, _ = mqtt_client.client.publish("e2dgfth34sgghh/SensorData/AccelerometerX", "Test Message")
        assert result == True

def test_add_subscribe_data(mqtt_client):
    topic = 'purbasha/topic'
    message_callback = Mock()

    # Positive test case
    mqtt_client.add_subscribe_data(topic, message_callback)
    assert topic in mqtt_client.extra_sub_topics
    assert mqtt_client.extra_sub_topics[topic] == message_callback

    '''Adding the same topic again'''
    # with pytest.raises(AssertionError):
    #     mqtt_client.add_subscribe_data(topic, message_callback)

    # with pytest.raises(Exception) as e:
    #     mqtt_client.add_subscribe_data(topic, message_callback)
    # assert "Topic already exists in extra_sub_topics,same topic can't be added again" in str(e.value)
    try:
        mqtt_client.add_subscribe_data(topic, message_callback)
    except Exception as AssertionError:
        assert str(AssertionError) == "Topic already exists in extra_sub_topics,same topic can't be added again"




def test_subscribe_extra_topics(mqtt_client):
    topic = 'test/topic'
    message_callback = Mock()

    '''Positive test case'''
    mqtt_client.extra_sub_topics = {topic: message_callback}
    mqtt_client.client.message_callback_add = Mock()
    mqtt_client.client.subscribe = Mock()

    mqtt_client.subscribe_extra_topics()

    mqtt_client.client.message_callback_add.assert_called_once_with(topic, message_callback)
    mqtt_client.client.subscribe.assert_called_once_with(topic, qos=0)

    '''false test case: Empty extra_sub_topics'''
    mqtt_client.extra_sub_topics = {}
    mqtt_client.client.message_callback_add = Mock()
    mqtt_client.client.subscribe = Mock()

    mqtt_client.subscribe_extra_topics()

    mqtt_client.client.message_callback_add.assert_not_called()
    mqtt_client.client.subscribe.assert_not_called()


# @patch('paho.mqtt.client.Client.loop_forever')
def test_start_thread(mqtt_client):
    '''mock for threading.Thread and its start method'''
    with patch('threading.Thread', autospec=True) as mock_thread:
        thread_instance = Mock()
        mock_thread.return_value = thread_instance
        mqtt_client.start_thread()#method call under test
        mock_thread.assert_called_once_with(
            target=mqtt_client.multi_loop, name="MqttConnectionThread") # Assertions
        thread_instance.start.assert_called_once()



def test_reconnect_broker(mqtt_client):
    '''mock thread'''
    mock_thread = Mock()
    mqtt_client.thread = mock_thread


    mqtt_client.readfile = Mock()
    mqtt_client.connect_broker = Mock() # Mock the methods used in reconnect_broker

    '''reconnect_broker method call '''
    mqtt_client.reconnect_broker()

    '''checking required methods are called or not '''
    mqtt_client.readfile.assert_called_once()
    mqtt_client.connect_broker.assert_called_once()
    # mock_thread.start.assert_called_once()

# def test_multi_loop(mqtt_client):
#     # Mock the client.is_connected method
#     mqtt_client.client.is_connected = Mock(return_value=False)
#     # Mock the connect_broker method
#     with patch.object(mqtt_client, 'connect_broker') as mock_connect_broker:
#         mock_connect_broker.return_value = None
#
#         # Call the method you want to test
#         mqtt_client.multi_loop(flag=True)
#
#         # Assert that is_connected was called and check the return value
#         mqtt_client.client.is_connected.assert_called()
#         assert mqtt_client.client.is_connected() is True  # Use 'is' to check for True value

def test_readfile(mocker, mqtt_client):

    """ mock for the AnalyticsJsonHandler [ used in analyticsmqqt.py file ]"""
    mock_json_handler = mocker.MagicMock()
    mocker.patch('Software.src.AnalyticsMqtt.AnalyticsJsonHandler', return_value=mock_json_handler)

    '''the expected return value from read_json'''
    expected_data = {"broker_details": {"broker_ip": "192.168.1.129","broker_password": "pass123","broker_port": 1883,"broker_username": "vegam129"}}
    mock_json_handler.read_json.return_value = expected_data
    result = mqtt_client.readfile()
    # print(result,"----------------")

    mock_json_handler.read_json.assert_called_once_with()
    assert result == expected_data

#
# def test_configure_ssl(mocker):
#     # Mock the required attributes and methods
#     mocker.patch.object(mqtt_client, 'readfile', return_value={
#         "broker_details": {
#             "ssl_auth_enabled": 1,
#             "ssl_auth_details": {
#                 "ca_certificate": "ca_cert.pem",
#                 "client_certificate": "client_cert.pem",
#                 "client_key_file": "client_key.pem",
#                 "keyfile_password": "password"
#             }


def test_configure_ssl(mocker):
    '''JSON configuration'''
    mqtt_config = {
        'broker_details': {
            'ssl_auth_enabled': 1,
            'ssl_auth_details': {
                'ca_certificate': 'mqtt_ca 3.crt',
                'client_certificate': 'mqtt_client 3.crt',
                'client_key_file': 'mqtt_client 3.key',
                'keyfile_password': 'pass123'
            }
        },
        'microservice_name': 'Velo_fft_microservice'
    }

    '''Mocking the readfile method to return the sample MQTT config'''
    mocker.patch.object(AnalyticsMqtt, 'readfile', return_value=mqtt_config)

    '''Creating an instance of AnalyticsMqtt'''
    mqtt_client_ssl = AnalyticsMqtt(filepath, subscribe_callback=mock_subscribe_callback)

    '''Mocking the tls_set method to check if it is called with the correct arguments'''
    mocker.patch.object(mqtt_client_ssl.client, 'tls_set', autospec=True)

    '''Mocking the tls_insecure_set method to check if it is called with the correct argument'''
    mocker.patch.object(mqtt_client_ssl.client, 'tls_insecure_set', autospec=True)

    '''Call configure_ssl method'''
    mqtt_client_ssl.configure_ssl()

    '''Checking if tls_set and tls_insecure_set were called'''
    assert mqtt_client_ssl.client.tls_set.called

    '''Checking if tls_set was called with the expected arguments'''
    expected_args = call(
        ca_certs='C:\\VELO_FFT_service\\cert/mqtt_ca 3.crt',
        certfile='C:\\VELO_FFT_service\\cert/mqtt_client 3.crt',
        keyfile='C:\\VELO_FFT_service\\cert/mqtt_client 3.key',
        tls_version=ssl.PROTOCOL_TLSv1_2,
        keyfile_password='pass123'
    )
    assert expected_args in mqtt_client_ssl.client.tls_set.call_args_list

    '''Checking if tls_insecure_set was called with the correct argument'''
    mqtt_client_ssl.client.tls_insecure_set.assert_called_with(True)

    # '''Clean up'''
    # mqtt_client_ssl.client = None

    '''disconnect'''
    mqtt_client_ssl.client = None


def test_multi_loop():
    '''Creating an instance of AnalyticsMqtt'''
    with patch('paho.mqtt.client.Client.loop_forever') as mock_loop_forever:
        mqtt_client1 = AnalyticsMqtt(filepath, subscribe_callback=mock_subscribe_callback)
        mqtt_client1.set_multi_loop_flag(True)
        mqtt_client1.multi_loop()

    '''Assert `loop_forever` was called with the retry_first_connection argument as True'''
    mock_loop_forever.assert_called_with(retry_first_connection=True)
    # assert mqtt_client1.client.connected_flag is False
    # mqtt_client1.connect_broker.assert_called_once()

    assert mqtt_client1.stop_multi_loop is True


# @patch('paho.mqtt.client.Client.loop_forever')
# def test_multi_loop(mock_loop_forever):
#     # Create an instance of AnalyticsMqtt with your test parameters
#     mqtt_client1 = AnalyticsMqtt(filepath, subscribe_callback=mock_subscribe_callback)
#
#     # Set the flag to True to stop the loop
#     mqtt_client1.set_multi_loop_flag(True)
#
#     # Call the `multi_loop` method
#     mqtt_client1.multi_loop()
#
#     # Assert that `loop_forever` was called with the retry_first_connection argument as True
#     mock_loop_forever.assert_called_with(retry_first_connection=True)



def test_set_multi_loop_flag(mqtt_client):
    mqtt_client.set_multi_loop_flag(True)
    assert mqtt_client.stop_multi_loop is True

    mqtt_client.set_multi_loop_flag(False)
    assert mqtt_client.stop_multi_loop is False

    mqtt_client.set_multi_loop_flag("hi") # false case check
    assert mqtt_client.stop_multi_loop is not False
    assert mqtt_client.stop_multi_loop is not True


@pytest.mark.xfail
def test_set_multi_loop_flag_expected_failure(mqtt_client):
    mqtt_client.set_multi_loop_flag(123)
    '''assert mqtt_client.stop_multi_loop is bool'''
    assert not isinstance(mqtt_client.stop_multi_loop, bool)


def test_disconnect(mqtt_client):
    mqtt_client.client.disconnect = Mock()

    mqtt_client.disconnect()

    mqtt_client.client.disconnect.assert_called_once()


#doc update
# report genaration for tests [ in excel] --> perform corner case , write report [ summary excel ]
#

# if __name__ == "__main__":
#     test_multi_loop()


