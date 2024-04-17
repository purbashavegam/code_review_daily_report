import inspect
import logging
from logging.handlers import RotatingFileHandler
import pathlib
import time

path = pathlib.Path(__file__)
path = path.parent
log_file_Path = str(path) + "\\metadata_app.log"


def app_logger(logLevel = logging.DEBUG):
    # Gets the name of the class / method from where this method is called
    loggerName = inspect.stack()[1][3]
    logger = logging.getLogger(loggerName)
    # By default, log all messages
    logger.setLevel(logLevel)

    ##this line helps to generate multiple log files wnvr the log file limit exceeds 10mb
    my_handler = RotatingFileHandler(log_file_Path, mode='a', maxBytes=10*1024*1024,
                                     backupCount=5, encoding=None, delay=0)

    my_handler.setLevel(logLevel)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    my_handler.setFormatter(formatter)
    logger.addHandler(my_handler)
    return logger
