## _Release Highlights:_


    - Enhanced data processing for accelerometer data via MQTT, calculating key metrics and ensuring accurate publishing.

    - Implemented continuous monitoring and automatic reconnection for MQTT connections.

    - Improved data validation by dropping improperly formatted input before processing.

    - Introduced threading.Condition for effective synchronization between threads.

    - Strengthened MQTT connections with Secure Sockets Layer.

    - Optimized processing for scenarios with raw data exceeding window size.

    - Resolved SSL EOF error and fixed race condition during MQTT data publishing.
