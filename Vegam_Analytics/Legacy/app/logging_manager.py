from SourceCode.app.vanalytics_helper import LoggingManager
# from vanalytics_helper import LoggingManager


main_logger = LoggingManager('logger_main').my_logger
vanalytics_data_logger= LoggingManager('logger_vanalytics_data').my_logger
vanalytics_api_logger= LoggingManager('logger_vanalytics_api').my_logger
mqtt_logger= LoggingManager('mqtt_logger').my_logger
rpm_logger= LoggingManager('rpm_logger').my_logger
class_velo_fft_logger=LoggingManager('class_structure_velo_fft_logger').my_logger
analytic_vel_fft_logger=LoggingManager('analytic_vel_fft_logger').my_logger

bearing_logger = LoggingManager('bearing_logger').my_logger
looseness_logger = LoggingManager('looseness_logger').my_logger
unbalance_logger = LoggingManager('unbalance_logger').my_logger
machine_on_off_logger = LoggingManager('machine_on_off_logger').my_logger
# publish_logger = LoggingManager('publish_logger').my_logger
mqtt_subscribe_publish_logger = LoggingManager('mqtt_subscribe_publish_logger').my_logger