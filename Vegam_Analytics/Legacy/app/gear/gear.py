# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 18:35:09 2021

@author: laptop58
"""


# imported libraries
import numpy as np
import math
# import vanalytics_helper as v_helper
# # import logging
# # import logers as log_file
# import itertools
# import rpm as shaftspeed
# from util2 import ParserFftCalculation as fft
import SourceCode.app.vmaint_constants as constants
import json
import time
from nltk import flatten


class Gear(object):
    #log = log_file.customLogger(logging.DEBUG)

    def __init__(self, operating_rpm_X, number_of_teeth_pinion, samplingFrequency, nsamp, 
                 windowsize, equipment_id, sensor_id, avgfft_data_X, avgfft_data_Y, avgfft_data_Z,freqn, 
                 freqn_X, freqn_Y, freqn_Z, rms):
        '''
           samplingFrequency : Sampling Frequency of the sensor
           nsamp : Number of samples
           windowsize : window size of the fft data
           max_rpm : Maximum speed of the Motor
           number_of_teeth_pinion: number of teeths of gear
           fftlist : FFT Data
           '''
        self.limit_value = float(0.1)
        #self.operatingRpm = float(operatingRpm)
        self.number_of_teeth_pinion = int(number_of_teeth_pinion)
        self.sampling_frequency = int(samplingFrequency)
        self.no_sample = int(nsamp)
        self.window_Size = int(windowsize)
        self.avgfft_data_X = avgfft_data_X
        self.avgfft_data_Y = avgfft_data_Y
        self.avgfft_data_Z = avgfft_data_Z
        self.freqn=freqn
        self.freqn_X = freqn_X
        self.freqn_Y = freqn_Y
        self.freqn_Z = freqn_Z
        self.operating_rpm_X = operating_rpm_X
        self.equipment_id = equipment_id
        self.sensor_id = sensor_id
        self.limit2 = []
        #self.frequency = frequency
        self.rms = rms
        self.freqn_data = []

    def Start_End_Array(self, fftdata, freqn, operatingRpm,limit):
       # Shaft Rotational Speed
       try:
            if operatingRpm is not None:
                FFT_DF = fftdata
                #limit = operatingRpm * constants.THIRTY_PERCENT
                for j in range(1, 11):
                    Rpm = (operatingRpm)*j
                    lower_limit, upper_limit = Rpm - limit, Rpm + limit
                    harmonic_value = [idx for idx, element in enumerate(
                        freqn) if lower_limit <= element <= upper_limit]
                    
                    amplitude_data = [FFT_DF[i] for i in harmonic_value]
                    frequency_values = [freqn[i] for i in harmonic_value]
                    #max_value_1 = max(amplitude_data)
                    #self.limit2.append(max_value_1)
                    self.freqn_data.append(frequency_values)
                    freqn_list = flatten(self.freqn_data)
                return freqn_list

            else:
                return
       except Exception as e:
           print(f"Error in method: gear.py - Start_End_Array, with ex: {e}")
    
    # speed and number of teeths are the inputs to the gear analysis
    def gear_mesh_frequency(self, operatingRpm):
        try:
            GMFF = float(operatingRpm * self.number_of_teeth_pinion)

            return GMFF
        except Exception as e:
           print(f"Error in method: gear.py - gear_mesh_frequency, with ex: {e}")
        # except:
        #     self.log.error(
        #         "Exception occurred while calculating gear mesh frequency", exc_info=True)

    # fault ranges of gear mesh frequency is calculated below
    def fault_range(self, input_value):
        try:
            if input_value is not None:

                # 67+13.14=76
                finalrange_high = float(input_value+1)
                finalrange_high2 = float(input_value+2)

                # 67-13.4=56
                finalrange_low = float(input_value-1)
                finalrange_low2 = float(input_value-2)

                return finalrange_low, finalrange_high, finalrange_high2, finalrange_low2
            else:
                return
        except Exception as e:
           print(f"Error in method: gear.py - fault_range, with ex: {e}")
        # except:
        #     self.log.error(
        #         "Exception occurred while calculating gear ranges", exc_info=True)

    # checks whether gear mesh frequency range matches the the frequency greater then rms obtained from the parser
    #   11 - No Gear Fault
    #   12 - Gear Fault
    def frequency_call(self,operatingRpm):
        try:
            limit1=operatingRpm*constants.THIRTY_PERCENT
            limit2=operatingRpm*constants.FORTY_PERCENT
            if self.no_sample==8192 and self.window_Size == 8192:
                Frequencies_x = self.Start_End_Array(
                    self.avgfft_data_X, self.freqn, self.operating_rpm_X,limit1)
                frequencies_y = self.Start_End_Array(
                    self.avgfft_data_Y, self.freqn, self.operating_rpm_X,limit1)
                frequencies_z = self.Start_End_Array(
                    self.avgfft_data_Z, self.freqn, self.operating_rpm_X,limit1)
            else:
                Frequencies_x = self.Start_End_Array(
                    self.avgfft_data_X, self.freqn, self.operating_rpm_X,limit2)
                frequencies_y = self.Start_End_Array(
                    self.avgfft_data_Y, self.freqn, self.operating_rpm_X,limit2)
                frequencies_z = self.Start_End_Array(
                    self.avgfft_data_Z, self.freqn, self.operating_rpm_X,limit2)
            return Frequencies_x
        except Exception as e:
            print(f"Error in method: gear.py - frequency_call, with ex: {e}")
    
    def gmff(self, fault_freqn_list):
        try:
            frequencies_x = self.frequency_call(self.operating_rpm_X)
            if frequencies_x is not None:
                gear_list = []
                gear_result = "11"
                if any(x in fault_freqn_list for x in frequencies_x):
                    gear_result = "12"
               
                    
                if any(x in 2*fault_freqn_list for x in 2*frequencies_x):
                    gear_result = "12"
              

                if any(x in 3*fault_freqn_list for x in 3*frequencies_x):
                    gear_result = "12"
                gear_list.append(gear_result)
                return gear_list
            else:
                return
        except Exception as e:
           print(f"Error in method: gear.py - gmff, with ex: {e}")
        # except Exception:
        #     self.log.critical(
        #         "Exception occurred while comparing the calculated gear harmonic ranges to obtained ranges through fft", exc_info=True)

    # all the above methods are called here
    def gmff_total_check(self):
        try:
            gmff = self.gear_mesh_frequency(self.operating_rpm_X)
            if gmff is not None:
                gmff_values = list(self.fault_range(gmff))
                gear_result = self.gmff(gmff_values)

                data = [self.equipment_id, self.sensor_id, "F",
                        json.dumps(gear_result) + "$T$" + str(time.time())]
                # Stop individual data publish
                # v_helper.helper.data_to_publish.append(data)
                return gear_result

            else:
                return
        except Exception as e:
            print(f"Error in method: gear.py - gmff_total_check, with ex: {e}")
        # except:
        #     self.log.critical(
        #         "Exception occurred while calling the functions", exc_info=True)
