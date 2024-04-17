import numpy as np
import pandas as pd
import os
import time
import SourceCode.app.vanalytics_helper as v_helper
from SourceCode.app.logging_manager import machine_on_off_logger

# import logers as l1
# import logging
import json
import time

DIR = os.path.dirname(__file__)


if not DIR:
    FILE_PATH = "velocity_severity.csv"
    #FILE_PATH1 = "vs_equipmets.csv"
    FILE_PATH1 = "equipment_severity.json"
else:
    FILE_PATH = DIR + "/velocity_severity.csv"
    #FILE_PATH1 = DIR +"/vs_equipmets.csv"
    FILE_PATH1 = DIR +"/equipment_severity.json"


class velocity_severity(object):
    v_iso_table = pd.read_csv(FILE_PATH)
    #v_input_table = pd.read_csv(FILE_PATH1)
    with open(FILE_PATH1, 'r') as readfile:
        v_input_table = json.load(readfile)


    # log = l1.customLogger(logging.DEBUG)

    def __init__(self, power, vel_value, equipment_id, sensor_id):
        self.power = power
        self.vel_value = vel_value
        self.sensor_id = sensor_id
        self.equipment_id = equipment_id
       

    ####checking the class of machine  ####
    ####fun to check the class of machine ###
    def mclass(self):  # power in KW
        try:
            self.power = int(self.power)
            
            if self.power < 15:
                self.classofmotor = 'class1'
            elif self.power in range(15, 75):  # range values are in kW
                self.classofmotor = 'class2'
            elif self.power in range(75, 10000):
                self.classofmotor = 'class3'
            elif self.power > 10000:
                self.classofmotor = 'class4'
            
            return self.classofmotor
        except:
            machine_on_off_logger.error(
                "Exception occurred while checking Class of motor", exc_info=True)
            
        
    #####checking velocity severity level

    def velocity_check(self, motorclass):
        try:
            # velocity iso standard values
            self.viso_val = np.array(
                velocity_severity.v_iso_table['Vrms_mm/s'])
            # difference of velocity values
            self.diff_val = np.abs(self.viso_val-self.vel_value)
            # index of velocity iso values
            self.iso_index = list(self.diff_val).index(min(self.diff_val))
            self.severityLevel = velocity_severity.v_iso_table[motorclass][self.iso_index]

            # returns the level
            return self.severityLevel
        except:
            machine_on_off_logger.error(
                "Exception occurred while checking velocity Severity", exc_info=True)
         

    def velocity_total_check(self):
        try:
            #v_inputfile = velocity_severity.v_input_table
            #vinp_val = v_inputfile['equip_id'].str
            if self.equipment_id in velocity_severity.v_input_table['equipment_ids']:
                #eqp_thrhld_val = v_inputfile.loc[v_inputfile['equip_id'] == self.equipment_id]
                vinp_threshold_low = velocity_severity.v_input_table['equipment_ids'][self.equipment_id]['low']
                vinp_threshold_high = velocity_severity.v_input_table['equipment_ids'][self.equipment_id]['high']

                #vinp_threshold_low = list(eqp_thrhld_val.iloc[:, 3])
                #vinp_threshold_high =list(eqp_thrhld_val.iloc[:, 4])
                #print(vinp_threshold_low,vinp_threshold_high)
                if self.vel_value <= vinp_threshold_low:
                    velocity_check = 0
                    
                elif self.vel_value <= vinp_threshold_high:
                    velocity_check = 1
                    
                else:
                     velocity_check = 2
                    
            else:
                class_of_machine = self.mclass()
                velocity_check = self.velocity_check(class_of_machine)
                if velocity_check.lower() == "good" or velocity_check.lower() == "satisfactory":
                    velocity_check = 0
                elif velocity_check.lower() == "unsatisfactory":
                    velocity_check = 1
                else:
                    velocity_check = 2

            # H - represents "Health" here
            data = [self.equipment_id, self.sensor_id, "H", json.dumps(velocity_check) + "$T$" + str(time.time() * 1000)]            
            v_helper.helper.data_to_publish.append(data)
            return velocity_check
            
        except:
           machine_on_off_logger.error("Exception occurred while checking velocity Severity Status", exc_info=True)