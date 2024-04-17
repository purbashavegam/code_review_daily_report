# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 15:19:41 2021

@author: laptop58
"""


import numpy as np
import pandas as pd
# import enum
# import vanalytics_helper as v_helper
# # import logers as log
# import logging
# import util2 as fft_cal
import json
import time
from numpy.linalg import norm
from numpy import (dot, arccos, clip)
import SourceCode.app.vmaint_constants as constants
from statistics import mean
import math


class Misalignment_Analysis(object):

    #log = log.customLogger(logging.DEBUG)

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
        #self.operating_rpm1 = operating_rpm1
        self.Equipment_id = equipment_id
        self.Sensor_id = sensor_id
        self.avgfft_data_X = avgfft_data_X
        self.avgfft_data_Y = avgfft_data_Y
        self.avgfft_data_Z = avgfft_data_Z
        self.sub_limits = []

        self.freqn_X = freqn_X
        self.freqn_Y = freqn_Y
        self.freqn_Z = freqn_Z
        #self.dataframe_Y=accy
        #self.dataframe_X=accx
        self.amp_data = []
        self.limit2 = []
        self.indexes = []
        self.indexes1 = []
        self.hrm = []

    def Start_End_Array(self, fftdata, freqn, operating_rpm,limit):
        # Shaft Rotational Speed
        try:
            if operating_rpm is not None:
                FFT_DF = fftdata
                #FFT_DF = self.avgfft_data_radial
                #limit = operating_rpm *35
                for j in range(1,11):
                    Rpm = (operating_rpm)*j
                    lower_limit, upper_limit = Rpm - limit, Rpm + limit 
                    harmonic_value = [idx for idx, element in enumerate( freqn) if lower_limit <= element <= upper_limit]
                    #self.hrm.append(harmonic_value)
                    amplitude_data = [FFT_DF[i] for i in harmonic_value]
                    max_value_1 = max(amplitude_data)
                    self.limit2.append(max_value_1)
                
                return self.limit2,amplitude_data
                # return self.amp_data

            else:
                return
        except Exception as e:
            print(f"Error in method: mislaignment.py - Start_End_Array, with ex: {e}")

    """ def accelerometer_data(self):

        try:
            if (self.dataframe_X is not None) and (self.dataframe_Y is not None):
                # Accelerometer X-axes Data
                amplitudeX = pd.DataFrame(self.dataframe_X)
                # converting string to numeric
                amplitudeX = amplitudeX.apply(pd.to_numeric, errors='coerce')
                x = amplitudeX[0]
                # Accelerometer Y-axes Data
                amplitudeY = pd.DataFrame(self.dataframe_Y)
                # converting string to numeric
                amplitudeY = amplitudeY.apply(pd.to_numeric, errors='coerce')
                y = amplitudeY[0]
                return x, y
            else:
                 return
        except Exception as e:
            print(e)

    def phasefind(self):
        try:
            horizontalaxesamplitude, verticalamplitude = self.accelerometer_data()
            if (horizontalaxesamplitude is not None) and (verticalamplitude is not None):
                if len(horizontalaxesamplitude) != len(verticalamplitude):
                    # Absolute value of difference
                    difference = abs(
                        len(horizontalaxesamplitude) - len(verticalamplitude))
                    diff = -(int(difference))
                    # If the lenth of Acc_X-axes is greater than Acc_Y-axes
                    if len(horizontalaxesamplitude) > len(verticalamplitude):
                        # Eliminate the noOfdifference in Acceleromer X-axes
                        df_horizontal = horizontalaxesamplitude[: diff]
                        df_vertical = verticalamplitude
                    # If the lenth of Acc_Y-axes is greater than Acc_X-axes
                    elif len(verticalamplitude) > len(horizontalaxesamplitude):
                        # Eliminate the noOfdifference in Acceleromer Y-axes
                        df_vertical = verticalamplitude[: diff]
                        df_horizontal = horizontalaxesamplitude
                    # Data for calculating Phase Difference
                    amplitudeX = df_horizontal
                    amplitudeY = df_vertical
                    c = dot(amplitudeX, amplitudeY) / \
                        norm(amplitudeX)/norm(amplitudeY)
                    # Phase Difference in Radians
                    angleinradians = arccos(clip(c, -1, 1))
                    # Phase Difference in degrees
                    angleindegree = (
                        (angleinradians * int(constants.ANGLE_IN_DEGREE)) / int(constants.TWO * math.pi))
                else:
                    amplitudeX = horizontalaxesamplitude
                    amplitudeY = verticalamplitude
                    c = dot(amplitudeX, amplitudeY) / \
                        norm(amplitudeX)/norm(amplitudeY)
                    # Phase Difference in Radians
                    angleinradians = arccos(clip(c, -1, 1))
                    degree=math.degrees(angleinradians)
                    print("radians",angleinradians)
                    print("degree",degree)
                    # Phase Difference in degrees
                    angleindegree = (
                        (angleinradians * int(constants.ANGLE_IN_DEGREE)) / (int(constants.TWO) * math.pi))
                return degree
            else:
                return
        except Exception as e:
            print(e)"""
    
    def amp_call(self,operatingRpm):
        try:
            limit1=operatingRpm*constants.THIRTY_PERCENT
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
            print(f"Error in method: mislaignment.py - amp_call, with ex {e}")
    
    def max_val_data(self, fftdata, freqn, operating_rpm):
        try:
            maxamp_values, amp_values = self.amp_call(self.operating_rpm_X)
            amp_3x_6x = maxamp_values[2:]
            #amp_1x_50 = maxamp_values[0]*constants.FIFTY_PERCENT
            amp_1x_25 = maxamp_values[0]*constants.ONE_TWENTY_FIVE_PERCENT
            amp_1x_200 = maxamp_values[0]*constants.TWO_HUNDRED_PERCENT
            #amp_1x_150 = maxamp_values[0]*constants.ONE_FIFTY_PERCENT
            amp_2x_50 = maxamp_values[1]*constants.FIFTY_PERCENT

            if amp_1x_25 < maxamp_values[1] <= amp_1x_200:
                result = str('misalignment')
                if maxamp_values[1] > amp_1x_200:
                    result = str('severe misalignment')

            else:
                result = str('No misalignment')

            return result, amp_values
        except Exception as e:
            print(f"Error in method: mislaignment.py - max_val_data, with ex: {e}")

    def mis_axis_check(self, fftdata, freqn, operating_rpm):

        misalignment_res = []
        try:
            max_value, amp_value = self.max_val_data(
                fftdata, freqn, operating_rpm)
            #mis_result_axial = self.mis_total_check(self.avgfft_data_axial, self.freqn_axial)
            #mis_result_radial = self.mis_total_check(
            #self.avgfft_data_radial, self.freqn_radial)
            #angle_phase = self.phasefind()
            misalignment_output_res = []

            if max_value is not None:
                if max_value == 'misalignment':
                    Misalignment_Check = "7"
                    misalignment_output_res.append(Misalignment_Check)

                if max_value == 'severe misalignment':
                    Misalignment_Check = "7"
                    misalignment_output_res.append(Misalignment_Check)
                if max_value == 'No misalignment':
                    Misalignment_Check = "8"
                    misalignment_output_res.append(Misalignment_Check)
                #print(misalignment_output_res)
                return misalignment_output_res
            else:
                return
        except Exception as e:
            print(f"Error in method: mislaignment.py - mis_axis_check, with ex: {e}")

    def mis_total_axis_check(self):
        misalignment_res = []
        try:

            result_x = self.mis_axis_check(
                self.avgfft_data_X, self.freqn_X, self.operating_rpm_X)
            result_y = self.mis_axis_check(
                self.avgfft_data_Y, self.freqn_Y, self.operating_rpm_X)
            result_z = self.mis_axis_check(
                self.avgfft_data_Z, self.freqn_Z, self.operating_rpm_X)

            if result_x == ['7'] or result_y == ['7']:
                mis_res = "7"
                mis_res_1 = "misalignment"
                misalignment_res.append(mis_res)
            else:
                mis_res = "8"
                mis_res_1 = " no misalignment"
                misalignment_res.append(mis_res)
            data = [self.Equipment_id, self.Sensor_id, "F", json.dumps(
                misalignment_res) + "$T$" + str(time.time())]
            
            # Stop individual data publish
            # v_helper.helper.data_to_publish.append(data)
            return misalignment_res

           
        except Exception as e:
            print(f"Error in method: mislaignment.py - mis_total_axis_check, with ex: {e}")
