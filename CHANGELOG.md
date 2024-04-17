# CHANGELOG

## [v1.0.0] - 2023-11-08
### Added
- Data Processing: The release includes the ability to receive sensor raw data (accelerometer data) via MQTT, process the data, and calculate key metrics such as velocity FFT, accelerometer FFT, and velocity RMS and publish the same in MQTT.

- Continuous checking on MQTT connection, if it gets disconnected, reconnecting to the broker again.
- Bad/improper formatted input data is being dropped before processing.
- For synchronization and coordination between threads,`threading.condition` is added. 
  wait(), notify() are added to avoid race conditions when working with shared resources or critical sections. 
  ####Enhancement
   - SSL Enhancement: MQTT connections have been strengthened with SSL, using python package ssl , not paho-mqtt ssl to create ssl layer over MQTT client .
   - If length of raw data is greater than window size then make sub packets and process and do average as result

### Fixed
- Bug Fix: This SSL EOF error has been identified and resolved.[high load test is done] 
  >error:<span style="color:red;"> EOF occurred in violation of protocol (_ssl.c:2483)</span>
- Race condition in multi threads: Issue has been resolved by adding thread condition in codebase
  >error:<span style="color:red;"> Same result data was getting published 6-7 times in a topic in MQTT while it should be only one times publish per topic</span>
### Acknowledgments
- xxxxx

[1.0.0]: https://github.com/repo/need to add /releases/tag/1.0.0

