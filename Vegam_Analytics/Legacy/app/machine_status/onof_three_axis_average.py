# imported libraries
import numpy as np
import logging
import statistics
import vanalytics_helper as v_helper
import itertools
import util as fft
import time
import json
import vmaint_constants as constants
# import logers as log_file

class MachineStatus (object):

    log = log_file.customLogger(logging.DEBUG)

    # rmsdata, samplingfrequency, equipment_id, sensor_id are input to the class
    def __init__(self, samplingfrequency, equipment_id, sensor_id, rms_valueX, rms_valueY, rms_valueZ):
        self.rmsthreshold = constants.rmsthreshold
        self.rms_valueX = rms_valueX
        self.rms_valueY = rms_valueY
        self.rms_valueZ = rms_valueZ
        self.samplingfrequency = samplingfrequency
        self.equipment_id = equipment_id
        self.sensor_id = sensor_id

    def avg_three_axis(self):
        try:
            average_total = (self.rms_valueX + self.rms_valueY +
                            self.rms_valueZ) / constants.THREE
            return average_total
        except:
            self.log.critical(
                "Exception occurred while calculating average in onoff", exc_info=True)

    # Below method checks machine is on or off based on threshold declared above
    def check_machine_status(self):
        try:
            average_rms = self.avg_three_axis()
            self.log.info("average_rms value is=",average_rms,"of sensorid=",self.sensor_id,"time=",str(time.time()))
            #   1 machine on & 0 machine off
            if average_rms >= self.rmsthreshold:
                machine_status = 1  
            else:
                machine_status = 0
            
            data = [self.equipment_id, self.sensor_id, "O", json.dumps(machine_status) + "$T$" + str(time.time())]
            
            v_helper.helper.data_to_publish.append(data)
            return machine_status
        except:
            self.log.critical(
                "Exception occurred while checking the machine status", exc_info=True)
