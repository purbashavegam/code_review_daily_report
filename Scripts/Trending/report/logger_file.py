import logging
import os
import sys
import traceback
# import logging.handlers
from logging.handlers import TimedRotatingFileHandler

try:
    log_folder_path = 'C:\\Vegam\\Trends_alert\\logs'
    # log_folder_path = 'logs'
    if not os.path.exists(log_folder_path):
        try:
            os.makedirs(log_folder_path)
            logging.info(f'Created "{log_folder_path}" folder.')
        except Exception as e:
            logging.info(f'Error creating "{log_folder_path}" folder: {str(e)}')

    logger = logging.getLogger()
    log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s -' \
                 ' %(message)s'
    logging.basicConfig(
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )

    # file_handler = RotatingFileHandler(
    #     'C:\\Vegam\\Missed_burst_calc_new_version\\logs\\missed_burst.log', maxBytes=200 * 1024 * 1024,
    #     backupCount=10, mode='a'
    # )
    file_handler = TimedRotatingFileHandler(f'C:\\Vegam\\Trends_alert\\logs\\daily_report.log', when='h', interval=24, backupCount=365)

    # file_handler = RotatingFileHandler(
    #     'logs/daily_report.log', maxBytes=200 * 1024 * 1024, backupCount=10, mode='a'
    # )
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
except Exception as ex:
    logging.error(f"Error occured during config file checking -  {ex}, {traceback.print_exception(*sys.exc_info())}")
