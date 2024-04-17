# Release Results - Version 1.0.0

## Introduction
This document summarizes the outcomes of Release 1.0.0 for the Velocity FFT Project.
It provides insights into the key achievements, testing, and deployment of the release.

## Scope and Objectives
The scope of Release 1.0.0 included:
- Implementation of a feature - velocity FFT, ACC FFT , Velocity RMS calculation  # not new feature? 
- Performance improvements in MQTT
- Bug fixes for critical issues like threading, SSL error.

The objectives for this release were to enhance user experience and system stability.


## Key Achievements
- Feature - velocity FFT, ACC FFT , Velocity RMS calculation is successfully implemented, enhancing user engagement.
- MQTT connection now performs with Secure Sockets Layer, improving overall system performance.
- Critical bugs resolved, leading to greater system stability.

## Release Notes
For detailed release notes, please refer to the [full release notes document](https://github.com/VegamSolutions/Vegam_Analytics/blob/updated_dir_analytics/RELEASE.md).

## Testing and Quality Assurance
- Comprehensive unit testing conducted for all features.
- Regression testing ensured backward compatibility.
- Load testing demonstrated system stability under high load.

Please refer to the [test result summary](https://aureoleinc.sharepoint.com/:x:/r/sites/analytics/_layouts/15/doc2.aspx?sourcedoc=%7BDF8054BC-47BE-4FA7-ADC5-DE3F44F045FD%7D&file=Test_Result_Summary.xlsx&action=default&mobileredirect=true&DefaultItemOpen=1&web=1&clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiIyNy8yMzA5MjkxMTIwNyIsIkhhc0ZlZGVyYXRlZFVzZXIiOmZhbHNlfQ%3D%3D) 
and [test document](https://aureoleinc.sharepoint.com/:w:/r/sites/analytics/_layouts/15/Doc.aspx?sourcedoc=%7BA61BD963-3B85-46E1-9631-D94A24A319C5%7D&file=test_cases_V_FFT_release.docx&action=default&mobileredirect=true)

## Performance and Scalability
- Performance of the system improved by optimizing the codes for data processing, multi threading.
- Scalability enhancements increased the capacity to handle more sensor data as input.
- MQTT connections have been strengthened with SSL, providing enhanced security for data transmission.


## Solved Issues(⭐)
- **_Issue 1:_** EOF occurred in violation of protocol (_ssl.c:2427) [SSL EOF ERROR](check link)

- **_Issue 2:_** In ,mqtt for one time data publishing, multiple times data coming as result - Race condition in threads. 
  [reference 1](https://superfastpython.com/thread-condition/)
  [reference 2](https://medium.com/@shashikantrbl123/understanding-condition-variables-in-python-for-thread-synchronization-329a166dfc9e)
  [reference 3](https://medium.com/@cipiklevis/how-to-resolve-a-race-conditions-in-python-5ac7fdd9285c)
  

## Known Issues/enhancement 🐛
- **_Issue 1:_** EOF occurred in violation of protocol (_ssl.c:2427) _if 250 sensors data being processed_ [SSL EOF ERROR](https://github.com/eclipse/paho.mqtt.python/issues/637)

- **_Issue 2:_** [An operation was attempted on something that is not a socket.](https://groups.google.com/g/rabbitmq-users/c/Ba1OiwyJ1IM)
   
   [link2](https://github.com/paramiko/paramiko/issues/512) , [link3](https://stackoverflow.com/questions/35889267/an-operation-was-attempted-on-something-that-is-not-a-socket-tried-fixing-a-lot)
- **_Enhancement 1:_** If else conditions in process_sensor_raw_data() -->  all these checks can be moved to a different function, improves readability.
- **_Enhancement 2:_** Remove infinite loop _[ while True condition ]_ while true, and have event based processing.



These issues will be addressed in Release 1.0.1

## Dependencies and Compatibility
- Added dependency on <span style="color:green;">requirements_dev.txt</span> [path](Software/src/requirements_dev.txt)
- Compatibility with [ need to add or remove?]

## Deployment and Rollout
- Deployment executed without any critical issues by NSSM to make windows service.
- Rollout conducted over the weekend to minimize user disruption.

## Feedback and User Response
User feedback:
- [is it needed? not sure]
## Conclusion
Release 1.0.0 was a success, meeting its objectives of improving the system's performance and stability. The team's efforts have been commendable, and user feedback has been overwhelmingly positive.

## Acknowledgments
xyz

## References
- [Project Documentation](link-to-project-docs.md)
- [User Feedback Summary](link-to-user-feedback.md)

## Contact Information
For inquiries or feedback, please contact:
- xyz (is it required@example.com)

---

**Appendix**

[Performance Metrics Chart](link-to-performance-chart.png)

**Note:** if required [ ??]
