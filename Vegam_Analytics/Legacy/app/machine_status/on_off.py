# # imported libraries
# import logging
# # import logers as log_file
# import itertools
# import numpy as np
import SourceCode.app.vanalytics_helper as v_helper
# import pandas as pd
import time
import json

# MachineStatus is class is called whenever the on of condition of machine is required


class MachineStatus (object):
    # log = log_file.customLogger(logging.DEBUG)

    # fftdata, samplingfrequency, equipment_id, sensor_id are input to the class taken from templist,metadata and equipmentdata
    def __init__(self, rmsdata, samplingfrequency, equipment_id, sensor_id):
        # threshold is set by observing penya data, it is not generic yet
        self.threshold = float(0.001)
        self.rmsdata = rmsdata
        self.samplingfrequency = samplingfrequency
        self.equipment_id = equipment_id
        self.sensor_id = sensor_id

    # Below method checks machine is on or off based on threshold declared above
    def check_machine_status(self):
        print(f"Machine on/off check for sensor {self.sensor_id}, received rms value: {self.rmsdata}")
        
        #  rms and threshold are compared belows
        if self.rmsdata >= self.threshold:
            machine_status = 1
        else:
            machine_status = 0
        # data is sent for publishing
        data = [self.equipment_id, self.sensor_id, "O", json.dumps(machine_status) + "$T$" + str(time.time() * 1000)]        
        v_helper.helper.data_to_publish.append(data)        
        return machine_status