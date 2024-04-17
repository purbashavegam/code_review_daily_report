
import mqtt_client as mqttc

Test_Topic = ['testTopic1', 'testTopic2', 'testTopic3', 'testTopic4']

Broker_Info = [
    {"broker": "192.168.1.185", "port": 1883},
    {"broker": "192.168.1.218", "port": 1883},
    {"broker": "192.168.1.102", "port": 5353},
    {"broker": "176.9.144.238", "port": 1883}]

Test = mqttc.MQTT_Connection(Broker_Info, Test_Topic) ## mqtt connection class is called
# Test = MQTT_Connection(Broker_Info, Test_Topic)

#Check_Connection = Test.connect_broker()

#subscribing = Test.on_connect()

