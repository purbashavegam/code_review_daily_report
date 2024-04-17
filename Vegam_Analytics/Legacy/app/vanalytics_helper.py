__name__ = "vanalytics_helper"

#import queue
# import json
import os, errno
import datetime
import logging.handlers
# import errno
from concurrent_log_handler import ConcurrentRotatingFileHandler as crf

from multiprocessing import Queue

class helper:
    data_to_publish = []
    # data_queue = queue.Queue(maxsize=0)
    data_queue = Queue(maxsize=0)


class BrokerInfo:

    def __init__(self, ipAddress, portNumber, userName, password, brokerName=None, qos=2):
        self.ipAddress = ipAddress
        self.portNumber = portNumber
        self.userName = userName
        self.password = password
        self.brokerName = brokerName
        self.isConnected = 0
        self.qos = qos
        self.MqttClient = None
        self.SubTopics = []

class EquipmentInfo:
    
    def __init__(self, equipmentNumber, equipmentName, equipmentClass, attachedSensors):
        self.equipmentNumber = equipmentNumber
        self.equipmentName = equipmentName
        self.equipmentClass = equipmentClass
        self.SensorInfo = attachedSensors

class SensorInfo:
    
    def __init__(self, sensorIdentifier, connectionMode, axisX, axisY, axisZ, sensorIdentifierOld, tags):
        self.sensorIdentifier = sensorIdentifier
        self.connectionMode = connectionMode
        self.axisX = axisX
        self.axisY = axisY
        self.axisZ = axisZ
        self.sensorIdentifierOld = sensorIdentifierOld
        self.Tags = tags

class Tags:
    
    def __init__(self, topicRepresents, topic, topicType, broker):
        self.topicRepresents = topicRepresents
        self.topic = topic
        self.topicType = topicType
        self.unique_id = None
        self.BrokerInfo = broker

class Entity:

    def __init__(self, unique_id, unique_name, group, description, properties):
        self.unique_id = unique_id
        self.unique_name = unique_name
        self.group = group
        self.description = description
        self.property = properties

class Property:

    def __init__(self, key, value, data_type, tag, range, unit, description):
        self.key = key
        self.value = value
        self.data_type = data_type
        self.tag = tag
        self.range = range
        self.unit = unit
        self.description = description


class LoggingManager:
    def __init__(self, logger_name):
        # self.make_sure_path_exists("D://vegam_projects//GIT_works//Vegam_Analytics//SourceCode//app//logs//")#self.make_sure_path_exists("logs//")
        self.make_sure_path_exists("C://logs_Vfft//")#self.make_sure_path_exists("logs//")
        # log_filename = 'logs//'+logger_name+'.log'

        current_time = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        # log_filename = 'D://vegam_projects//GIT_works//Vegam_Analytics//SourceCode//app//logs//' + logger_name + '_' + current_time + '.log'
        log_filename = 'C://logs_Vfft//' + logger_name + '_' + current_time + '.log'
        log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s\n%(message)s'

        # log_format = '%(asctime)s - [%(filename)s::%(lineno)d] - %(levelname)12s - %(threadName)22s  - %(funcName)s -' \
        #              ' %(message)s'
        # Set up a specific logger with our desired output level
        log_level = logging.DEBUG #logging.WARNING
        '''Add the log message handler to the logger'''
        handler = crf(log_filename, maxBytes= 20*1024*1024, backupCount=50)
        # handler = logging.handlers.RotatingFileHandler(
        #             log_filename, maxBytes= 20*1024*1024, backupCount=50)
        # handler = logging.handlers.TimedRotatingFileHandler(log_filename, when = 's', interval = 40, backupCount = 200, encoding = None, delay = False, utc = False, atTime= None)
        handler.setFormatter(logging.Formatter(log_format))
        self.my_logger = logging.getLogger(logger_name)
        self.my_logger.setLevel(log_level)
        self.my_logger.addHandler(handler)
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        # create formatter
        formatter = logging.Formatter(log_format,datefmt='%m/%d/%Y %I:%M:%S %p') #added
        # add formatter to ch
        ch.setFormatter(formatter)

    @staticmethod
    def make_sure_path_exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

#pm
