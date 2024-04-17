# import logging
# import sys
import math
# external library
# import numpy as np
# import pandas as pd
# import vanalytics_helper as v_helper
# # import logers as log_file
import itertools
# import util as fft
import SourceCode.app.vmaint_constants as constants
import time
import json
import os
from nltk import flatten

DIR = os.path.dirname(__file__)
if not DIR:
    FILE_PATH = "bearing_config.json"
else:
    FILE_PATH = DIR + "/bearing_config.json"

bearing_config = None
with open(FILE_PATH, 'r') as readfile:
    bearing_config = json.load(readfile)


class Bearing(object):
    #log = log_file.customLogger(logging.DEBUG)

    def __init__(self, number_of_balls, inner_diameter, outer_diameter, angle, partNumber, operating_rpm_X, 
                 sampling_frequency, number_sample, window_size, equipment_id, sensor_id, avgfft_data_X, 
                 avgfft_data_Y, avgfft_data_Z,freqn, freqn_X, freqn_Y, freqn_Z, rms):
        '''samplingFrequency : Sampling Frequency of the sensor
           nsamp : Number of samples 
           windowsize : window size of the fft data
           operatingRpm : rpm of the Motor
           number_of_balls : number of balls present in bearing
           inner_diameter :inner_diameter of bearing
           outer_diameter :outer_diameter of bearing
           angle : contact angle of bearing
           fftlist : FFT Data
        '''
        self.limit_value = float(0.1)
        self.number_of_balls = 0 if number_of_balls is None else int(
            number_of_balls)
        self.inner_diameter = 0.0 if inner_diameter is None else float(
            inner_diameter)
        self.outer_diameter = 1.0 if outer_diameter is None else float(
            outer_diameter)
        self.angle = 0 if angle is None else float(angle)
        self.sampling_frequency = sampling_frequency
        self.number_sample = number_sample
        self.window_size = window_size
        self.equipment_id = equipment_id
        self.sensor_id = sensor_id
        self.avgfft_data_X = avgfft_data_X
        self.avgfft_data_Y = avgfft_data_Y
        self.avgfft_data_Z = avgfft_data_Z
        self.freqn=freqn
        self.freqn_X = freqn_X
        self.freqn_Y = freqn_Y
        self.freqn_Z = freqn_Z
        self.operating_rpm_X = operating_rpm_X
       
        self.rms_threshold = constants.THREE
        self.partNo = partNumber
        self.freqn_data = []
        self.limit2 = []
        self.hrm = []
        self.rms = rms
    # bearing characterstic frequencies are calculated in the below method
    # number_of_balls,inner_diameter,outer_diameter,angle are bearing inputs

    def bearing_characterstic_frequency(self, operatingRpm):
        try:
            if self.partNo is not None:
                self.partNo = self.partNo.strip().upper().replace(" ", "")
                if len(self.partNo) > 0:
                    return self.get_bearing_freq_using_partNo(operatingRpm)

            return self.get_bearing_freq(operatingRpm)
        except Exception as e:
            print(f"Error in method: bearing.py - bearing_characterstic_frequency, with ex: {e}")

        # except:
        #     self.log.error(
        #         "Exception occurred while calculating bearing characterstic frequencies using part number", exc_info=True)

    def get_bearing_freq_using_partNo(self, operatingRpm):
        try:
            cage_factor = bearing_config[self.partNo]["cage"]
            ballspin_factor = bearing_config[self.partNo]["ballspin"]
            innerrace_factor = bearing_config[self.partNo]["innerace"]
            outerrace_factor = bearing_config[self.partNo]["outerrace"]

            cage_freq = int(cage_factor * operatingRpm)
            ballspin_freq = int(ballspin_factor * operatingRpm)
            innerrace_freq = int(innerrace_factor * operatingRpm)
            outerrace_freq = int(outerrace_factor * operatingRpm)

            return [innerrace_freq, outerrace_freq, ballspin_freq, cage_freq]
        except Exception as e:
            print(f"Error in method: bearing.py - get_bearing_freq_using_partNo, with ex: {e}")
        # except:
        #     self.log.error(
        #         "Exception occurred while calculating bearing characterstic frequencies using part number", exc_info=True)

    def get_bearing_freq(self, operatingRpm):
        try:
            # all four bearing characterstic frequencies are calculated
            cage_therotical = (
                (constants.ONE/constants.TWO)*(constants.ONE-(self.inner_diameter/self.outer_diameter)*math.cos(self.angle)))
            # fundamental train frequency is calculated using formula
            cage = cage_therotical * operatingRpm
            cage_result = int(cage)

            innerrace_therotical = (
                (self.number_of_balls/constants.TWO)*(constants.ONE+(self.inner_diameter/self.outer_diameter)*math.cos(self.angle)))
            # ball pass frequency of inner race is calculated using formula
            innerrace = innerrace_therotical * operatingRpm
            innerace_result = int(innerrace)

            outerrace_therotical = (
                (self.number_of_balls/constants.TWO)*(constants.ONE-(self.inner_diameter/self.outer_diameter)*math.cos(self.angle)))
            # ball pass frequency  of outer race is calculated using formula
            outerrace = outerrace_therotical * operatingRpm
            outerrace_result = int(outerrace)

            ball_spin_therotical = ((self.outer_diameter/(constants.TWO*self.inner_diameter))*(
                constants.ONE-((self.inner_diameter/self.outer_diameter)*(math.cos(self.angle)))**constants.TWO))
            # ball spin frequency is calculated using formula
            ballspin = ball_spin_therotical * operatingRpm
            ballspin_result = int(ballspin)

            return [innerace_result, outerrace_result, ballspin_result, cage_result]
        except Exception as e:
           
           print(f"Error in method: bearing.py - get_bearing_freq, with ex: {e}")
        # except:
        #     self.log.error(
        #         "Exception occurred while calculating bearing characterstic frequencies", exc_info=True)

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
                    #self.hrm.append(harmonic_value)
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
            print(f"Error in method: bearing.py - Start_End_Array, with ex: {e}")

    def faultrange(self, input_value):
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
           print(f"Error in method: bearing.py - faultrange, with ex: {e}")
    
    def frequency_call(self,operatingRpm):
        try:
            limit1=operatingRpm*constants.THIRTY_PERCENT
            limit2=operatingRpm*constants.FORTY_PERCENT
            if self.number_sample==8192 and self.window_size==8192:
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
            print(f"Error in method: bearing.py - frequency_call, with ex: {e}")
    # except:
        #     self.log.error(
        #         "Exception occurred while calculating ranges of bearing characterstic frequency", exc_info=True)
     # checks whether cage therotical frequencies  range matches the the frqns greater then rms obtained from the parser
    
    def cage(self, fault_freqn_list):
        try:
            frequencies_x = self.frequency_call(self.operating_rpm_X)
                
            if frequencies_x is not None:
                cage_result = []
                if any(x in fault_freqn_list for x in frequencies_x):

                    bearing_result = "4"
                    cage_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    cage_result.append(bearing_result)

                # second harmonic check
                if any(x in 2*fault_freqn_list for x in 2*frequencies_x):

                    bearing_result = "4"
                    cage_result.append(bearing_result)

                else:
                    bearing_result = "0"
                    cage_result.append(bearing_result)

                # third harmonic check
                if any(x in 3*fault_freqn_list for x in 3*frequencies_x):

                    bearing_result = "4"
                    cage_result.append(bearing_result)

                else:
                    bearing_result = "0"
                    cage_result.append(bearing_result)

                return cage_result
            else:
                return
        except Exception as e:
           print(f"Error in method: bearing.py - cage, with ex: {e}")
        # except:
        #     self.log.critical(
        #         "Exception occurred while comparing the calculated cage harmonic ranges to obtained ranges through fft", exc_info=True)

    # checks whether ball spin therotical frequencies  range matches the the frqns greater then rms obtained from the parser
    
    def ballspin(self, fault_freqn_list):
        try:
            frequencies_x = self.frequency_call(self.operating_rpm_X)

            if frequencies_x is not None:

                ballspin_result = []

                if any(x in fault_freqn_list for x in frequencies_x):
                    bearing_result = "3"
                    ballspin_result.append(bearing_result)

                else:
                    bearing_result = "0"
                    ballspin_result.append(bearing_result)
                # second harmonic check
                if any(x in 2*fault_freqn_list for x in 2*frequencies_x):

                    bearing_result = "3"
                    ballspin_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    ballspin_result.append(bearing_result)

                # third harmonic check
                if any(x in 3*fault_freqn_list for x in 3*frequencies_x):

                    bearing_result = "3"
                    ballspin_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    ballspin_result.append(bearing_result)

                return ballspin_result
            else:
                return
        except Exception as e:
           print(f"Error in method: bearing.py - ballspin, with ex: {e}")
        # except:
        #     self.log.critical(
        #         "Exception occurred while comparing the calculated ball spin harmonic ranges to obtained ranges through fft", exc_info=True)

    # checks whether outerrace therotical frequencies  range matches the the frqns greater then rms obtained from the parser
    
    def outerrace(self, fault_freqn_list):
        try:
            frequencies_x = self.frequency_call(self.operating_rpm_X)
            outerrace_result = []

            if frequencies_x is not None:

                if any(x in fault_freqn_list for x in frequencies_x):

                    bearing_result = "2"
                    outerrace_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    outerrace_result.append(bearing_result)

                # second harmonic check
                if any(x in 2*fault_freqn_list for x in 2*frequencies_x):
                    bearing_result = "2"
                    outerrace_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    outerrace_result.append(bearing_result)

                # third harmonic check
                if any(x in 3*fault_freqn_list for x in 3*frequencies_x):
                    bearing_result = "2"
                    outerrace_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    outerrace_result.append(bearing_result)

                return outerrace_result
            else:
                return
        except Exception as e:
           print(f"Error in method: bearing.py - outerrace, with ex: {e}")
        # except:
        #     self.log.critical(
        #         "Exception occurred while comparing the calculated Outerrace harmonic ranges to obtained ranges through fft", exc_info=True)

    # checks whether innerrace therotical frequencies  range matches the the frqns greater then rms obtained from the parser
    
    def innerrace(self, fault_freqn_list):
        try:
            frequencies_x = self.frequency_call(self.operating_rpm_X)

            innerrace_result = []
            if frequencies_x is not None:
                if any(x in fault_freqn_list for x in frequencies_x):

                    bearing_result = "1"
                    innerrace_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    innerrace_result.append(bearing_result)

                if any(x in 2*fault_freqn_list for x in 2*frequencies_x):

                    bearing_result = "1"
                    innerrace_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    innerrace_result.append(bearing_result)
                if any(x in 3*fault_freqn_list for x in 3*frequencies_x):

                    bearing_result = "1"
                    innerrace_result.append(bearing_result)
                else:
                    bearing_result = "0"
                    innerrace_result.append(bearing_result)

                return innerrace_result
            else:
                return
        except Exception as e:
          print(f"Error in method: bearing.py - innerrace, with ex: {e}")
        # except:
        #     self.log.critical(
        #         "Exception occurred while comparing the calculated innerrace harmonic ranges to obtained ranges through fft", exc_info=True)

    # all the above methods are called one by one
    def bearing_total_check(self):

        try:
            fault_freq = self.bearing_characterstic_frequency(
                self.operating_rpm_X)
            
            if fault_freq is not None and len(fault_freq) == 4:
                inner = fault_freq[0]
                outer = fault_freq[1]
                ball = fault_freq[2]
                cages = fault_freq[3]

                faultrange_cage = list(self.faultrange(
                    cages))

                faultrange_ballspin = list(self.faultrange(
                    ball))

                faultrange_outerrace = list(self.faultrange(
                    outer))

                faultrange_innerrace = list(self.faultrange(
                    inner))

                cage_result_total = self.cage(
                    faultrange_cage)

                ballspin_result_total = self.ballspin(
                    faultrange_ballspin)

                outerrace_result_total = self.outerrace(
                    faultrange_outerrace)

                innerrace_result_total = self.innerrace(
                    faultrange_innerrace)

                # combining all the above list into a single list
                combined_list = itertools.chain(
                    innerrace_result_total, outerrace_result_total, ballspin_result_total, cage_result_total)
                bearing_algorithm_list = list(set(combined_list))
                # print(bearing_algorithm_list)

                # checks whether all values of combined list is zero
                if all([v == "0" for v in bearing_algorithm_list]):
                    bearing_result_new = "0"
                    bearing_result_new = list(bearing_result_new)
                else:
                    bearing_result_ignore = "0"
                    # removes 0 from the list
                    bearing_result_new = [
                        i for i in bearing_algorithm_list if i not in bearing_result_ignore]
                    # removes duplicates from the list

                # "F" indicates the fault
                data = [self.equipment_id, self.sensor_id, "F", json.dumps(
                    bearing_result_new) + "$T$" + str(time.time())]
                # Stop individual data publish
                # v_helper.helper.data_to_publish.append(data)
                return bearing_result_new

            else:
                return None

        except Exception as e:
            print(f"Error in method: bearing.py - bearing_total_check, with ex: {e}")
        # except:
