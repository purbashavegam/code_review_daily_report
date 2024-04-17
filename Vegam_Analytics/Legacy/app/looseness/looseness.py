

# import numpy as np
# import pandas as pd
# # import enum
# import vanalytics_helper as v_helper
# # import logers as log
import logging
# import util2 as fft_cal
from SourceCode.app.logging_manager import looseness_logger
import SourceCode.app.vmaint_constants as constants
import json
import time


class Looseness_Analysis(object):

    # log = log.customLogger(logging.DEBUG)

    '''
    This is a class to analyse looseness
    '''

    def __init__(self, samplingFrequency, noOfSample, windowsize, operating_rpm_X,
                 sensor_id, equipment_id, avgfft_data_X, avgfft_data_Y, avgfft_data_Z, freqn_X, freqn_Y, freqn_Z):
        '''
        samplingFrequency, windowsize : from sensor details (metadata)
        noOfSample : Number of sampales
        fftlist : FFT data from mqtt
        FREQUENCY_LIMIT = float(0.20)
        RMS_2X_THRESHOLD = float(0.40)
        RMS_3X_THRESHOLD = float(0.30)
        '''
        self.sampling_frequency = samplingFrequency
        self.number_sample = noOfSample
        self.window_size = windowsize
        self.operating_rpm_X = operating_rpm_X
        self.hrm=[]
        self.Equipment_id = equipment_id
        self.Sensor_id = sensor_id
        self.avgfft_data_X = avgfft_data_X
        self.avgfft_data_Y = avgfft_data_Y
        self.avgfft_data_Z = avgfft_data_Z
        self.Limits_of_harmonics = []
        self.sub_limits = []
        self.limit_low = []
        self.limit_high = []
        self.limit_max_values = []
        self.limit2 = []
        self.freqn_X = freqn_X
        self.freqn_Y = freqn_Y
        self.freqn_Z = freqn_Z
        self.amp_data = []

    def Start_End_Array(self, fftdata, freqn, operating_rpm,limit):
        # Shaft Rotational Speed
        try:
            if operating_rpm is not None:
                #FFT_DF = self.avgfft_data_radial
                #limit = operating_rpm *35
                for j in range(1,11):
                    Rpm = (operating_rpm)*j
                    lower_limit, upper_limit = Rpm - limit, Rpm + limit 
                    harmonic_value = [idx for idx, element in enumerate( freqn) if lower_limit <= element <= upper_limit]
                    self.hrm.append(harmonic_value)
                    amplitude_data = [fftdata[i] for i in harmonic_value]
                    max_value_1 = max(amplitude_data)
                    self.limit2.append(max_value_1)
                
                return self.limit2,amplitude_data
                # return self.amp_data

            else:
                return
        except Exception as e:
            print(f"Error in method: looseness.py - Start_End_Array, with ex {e}")
    
    def amp_call(self,operatingRpm):
        try:
            limit1=operatingRpm*constants.THIRTY_FIVE_PERCENT
            limit2=operatingRpm*constants.FORTY_PERCENT
            if self.number_sample==8192 and self.window_size==8192:
                max_ampx,ampx = self.Start_End_Array(
                    self.avgfft_data_X, self.freqn_X, self.operating_rpm_X,limit1)
                max_ampy,ampy = self.Start_End_Array(
                    self.avgfft_data_Y, self.freqn_Y, self.operating_rpm_X,limit1)
                max_ampz,ampz = self.Start_End_Array(
                    self.avgfft_data_Z, self.freqn_Z, self.operating_rpm_X,limit1)
            else:
                max_ampx,ampx = self.Start_End_Array(
                    self.avgfft_data_X, self.freqn_X, self.operating_rpm_X,limit2)
                max_ampy,ampy = self.Start_End_Array(
                    self.avgfft_data_Y, self.freqn_Y, self.operating_rpm_X,limit2)
                max_ampz,ampz = self.Start_End_Array(
                    self.avgfft_data_Z, self.freqn_Z, self.operating_rpm_X,limit2)
            return max_ampx,ampx
        except Exception as e:
            print(f"Error in method: looseness.py - amp_call, with ex {e}")
    
    def Looseness_Check(self):
        try:
            max_amplitude_at_harmonics_x, amp_x_1x_10x = self.amp_call(self.operating_rpm_X)
            max_amp1x = max_amplitude_at_harmonics_x[0]
            amp_2x_6x = max_amplitude_at_harmonics_x[1:]
            
            max_amp_1x_120 = constants.ONE_TWENTY_PERCENT * max_amp1x
            # max_amp_1x_120 = 1.5 * max_amp1x
            faultCounter = 0
            if amp_2x_6x is not None:
                for i in amp_2x_6x:
                    if i > max_amp_1x_120:
                        faultCounter = faultCounter+1
                    if faultCounter >= constants.TWO:
                        result = str('Looseness')
                        break
                    else:
                        result = str('No Looseness')

                return result
            else:
                return
        except Exception as e:
            print(f"Error in method: looseness.py - Looseness_Check, with ex: {e}")

    def Looseness_Total_Check(self):
        looseness_output_res = []
        try:
            Looseness_Check = self.Looseness_Check()
            if Looseness_Check is not None:
                if Looseness_Check == 'Looseness':

                    Looseness_Check = '14'
                    looseness_output_res.append(Looseness_Check)

                else:
                    Looseness_Check = '13'
                    
                    looseness_output_res.append(Looseness_Check)

                data = [self.Equipment_id, self.Sensor_id, "F", json.dumps(
                    looseness_output_res) + "$T$" + str(time.time())]
                
                # Stop individual data publish
                # v_helper.helper.data_to_publish.append(data)

                return looseness_output_res
            else:
                return
        except Exception as e:
            print(f"Error in method: lossness.py - Looseness_Total_Check, with ex: {e}")