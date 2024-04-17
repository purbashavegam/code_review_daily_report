

import json

Test_Mqtt_Config = {
    "broker_address":"176.9.144.238",
    "broker_port":"1883",
    "ConfigureSensors":["A434F17EE90B","A434F17EE90B","A434F17EE90B"],
    "Sensor_topic": ["AccelerometerX","AccelerometerY","AccelerometerZ", 
                      "VelocityX","VelocityY","VelocityZ",
                      "FFTX","FFTY","FFTZ"]
}

with open('Test_Mqtt_Config.json', 'w') as json_file:
    json.dump(Test_Mqtt_Config, json_file)
    

