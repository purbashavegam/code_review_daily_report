#Version 1.0.0 - Release Notes


This is the initial release of the project. 
It introduces several key features and improvements, and has undergone rigorous testing to ensure reliability and performance.

###**_Key Highlights:_**
- **_Data Processing:_** The release includes the ability to receive sensor raw data (accelerometer data) via MQTT, process the data, and calculate key metrics such as velocity FFT, accelerometer FFT, and velocity RMS and publish the same in MQTT.

- **_Scalability:_** The codebase has successfully passed a high-load test with simulated dummy data arriving every 15 minutes for 50 sensors. 

- **_Long-Term Stability:_** The release has undergone extensive long-term testing, demonstrating its stability and reliability over extended periods.

- **_End-to-End Integration:_** The project has been seamlessly integrated with an IoT platform to receive real sensor data, process it, and publish results to specific topics.

- **_SSL Enhancement:_** MQTT connections have been strengthened with SSL, providing enhanced security for data transmission.

- **_Bug Fix:_** An SSL EOF error has been identified and resolved, ensuring a more robust and error-free operation of the system.


For more detailed information about the release, please refer to the project's documentation[ not yet done].

