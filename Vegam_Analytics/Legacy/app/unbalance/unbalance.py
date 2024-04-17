import numpy as np
import pandas as pd
import math
from numpy.linalg import norm
from numpy import (dot, arccos, clip)
# import logers as log
# import logging
import SourceCode.app.vanalytics_helper as v_helper
# import util as fft_cal
# import rpm as Shaftspeed
import SourceCode.app.vmaint_constants as constants
import json
import time
from SourceCode.app.logging_manager import unbalance_logger


class unbalance(object):

    # log = log.customLogger(logging.DEBUG)

    def __init__(self, sampling_freq, noOfSample, windowsize, operating_rpm, sensor_id,
                 equipment_id, avg_fftx,avg_ffty,avg_fftz,rms):
        '''
        sampling_freq : Sampling Frequency of the sensor
        noOfSample : Number of samples in FFT, Accelerometer X and Accelerometer Y
        windowsize : window size of the fft data
        shaftSpeed : Maximum speed of the Motor
        fftlist : FFT X-axes Data
        END_THRESHOLD = Amplitude range 1.2 times  (float(1.2))
        SECONDS = 60 seconds
        ANGLE_IN_DEGREE = Complete Angle (360 deg)
        IDEAL_DEGREE = Ideal phase difference
        DEGREE_RANGE = Limit for the Phase difference(+-30 deg)
        START_FREQ_LIMIT = start of frequency range for 1st Harmonic
        END_FREQ_LIMIT = End of frequency range for 1st Harmonic
        LoosenessRange = Harmonics for the other faults
        HARMONIC_ALLOWANCE = At each harmonics frequency limit is 0.2
        MAX_AMP_LIMIT_1X = Amplitude 40 percent at 1st Harmonic
        HARMONIC_END = Harmonics (2X to 10X)
        HARMONICS_RANGE = Harmonics range (0.5X, 1X, 1.5X, 2X,....10.5X)
        START_RANGE = 0
        TWO = 2
        START = 0.0
        END = 1.0
        INI_WINDOWSIZE = 0
        '''
        self.Sampling_Frequency = sampling_freq
        self.Number_sample = noOfSample
        self.Window_Size = windowsize
        self.operating_rpm = operating_rpm
        self.Sensor_id = sensor_id
        self.Equipment_id = equipment_id
        self.avg_fftx=avg_fftx
        self.avg_ffty=avg_ffty
        self.avg_fftz=avg_fftz

        self.window_val = self.Window_Size
        self.HarmonicsStart = []
        self.HarmonicsEnd = []
        self.Harmonic_Frequency = []
        self.rms = rms
        self.rms_threshold = constants.THREE

    def unbalance_axes(self,avg_fftdata):
        try:

            if self.operating_rpm is not None:
                time = 1 / self.Sampling_Frequency
                # FFT Frequencies
                fft_x = np.linspace(int(constants.START), int(constants.END) /
                                    (constants.TWO * time), self.Window_Size)
                fft_x_list = list(fft_x)
                
                fft_rms_index = [index for index, value in enumerate(avg_fftdata)
                                 if value > constants.END_THRESHOLD * self.rms]

                fft_rms_values = [value for index, value in enumerate(avg_fftdata)
                                  if value > constants.END_THRESHOLD * self.rms]
                frequency_above_rms = [fft_x_list[fft_rms_index[i]]
                                       for i in range(len(fft_rms_index))]
                # # Taking rpm 1x range to detect unbalance fault
                rpm1xranage = [frequency_above_rms[i] for i in range(len(frequency_above_rms))
                               if constants.START_FREQ_LIMIT * self.operating_rpm <= frequency_above_rms[i] <= constants.END_FREQ_LIMIT * self.operating_rpm]
                #            # Index of the freq above rms value
                #            indexFreqAboveRMS = [frequency_above_rms[rpm1xranage[i]]
                #                                        for i in range(len(rpm1xranage))]
                indexFreqAboveRMS = frequency_above_rms.index(rpm1xranage[0])

                # Amplitude of the freq
                max1xrpmAmplitude = fft_rms_values[indexFreqAboveRMS]

                # amplitudes and corresponding freq above the threshold and max amplitude in the list
                #            return RPM#fft_rms_values, frequency_above_rms, max1xrpmAmplitude
                return fft_rms_values, frequency_above_rms, max1xrpmAmplitude
            else:
                return
        except:
            unbalance_logger.error(
                "Exception occurred while checking Frequency above Threshold", exc_info=True)

    def unbalance_harmonics_check(self):

        values_x = self.unbalance_axes(self.avg_fftx)
        values_y = self.unbalance_axes(self.avg_ffty)
        values_z = self.unbalance_axes(self.avg_fftz)
        

        if values_x is not None:
            fft_rms_values = values_x[0]
            frequency_above_rms = values_x[1]
            max1xrpmAmplitude = values_x[2]
        else:
            return
        # harmonicsfrequ = self.unbalance_harmonics_check()
        #rpm = int(self.RpmFromVib()[0])
        try:
            if self.operating_rpm is not None:

                harmonics = np.arange(int(constants.START), int(
                    constants.HARMONIC_END), float(constants.HARMONICS_RANGE))

                for j in harmonics:
                    Start_val = (
                        (self.operating_rpm * j) - (self.operating_rpm * float(constants.HARMONIC_ALLOWANCE)))
                    End_val = (
                        (self.operating_rpm * j) + (self.operating_rpm * float(constants.HARMONIC_ALLOWANCE)))
                    self.HarmonicsStart.append(Start_val)
                    self.HarmonicsEnd.append(End_val)

                k = list(zip(self.HarmonicsStart, self.HarmonicsEnd))
                # Checking for multiple harmonics with 20%, from 2x to 10.5x
                # and checking harmonics corresponding to 1x harmonic
                for harmonic_freq_values in frequency_above_rms:
                    for i, j in k:
                        if i <= harmonic_freq_values <= j:
                            self.Harmonic_Frequency.append(
                                harmonic_freq_values)
                        else:
                            pass
                harmonicAmpli = [fft_rms_values[frequency_above_rms.index(
                    i)] for i in self.Harmonic_Frequency]
                # Considering harmonics above 40% of 1x harmonics to detect other faults
                HrmAmpAbv40_per1x = [i for i in harmonicAmpli if i >
                                     float(constants.MAX_AMP_LIMIT_1X) * max1xrpmAmplitude]
                return HrmAmpAbv40_per1x
            else:
                return
        # return HrmAmpAbv40_per1x
        except:
            unbalance_logger.error("Exception occurred while checking amplitudes at multiple Harmonics",
                           exc_info=True)
    
    def phaseShift(self, freq_hz=60):
        try:
            no_of_sample = len(self.avg_fftx)
            ab_corr = np.correlate(self.avg_fftx, self.avg_ffty, "full")
            time_slot = np.linspace(0.0, ((no_of_sample - 1) /self.Sampling_Frequency), no_of_sample)
            dtime_slot = np.linspace(-time_slot[-1], time_slot[-1], (2 * no_of_sample) - 1)
            t_shift_alt = (1.0 / self.Sampling_Frequency) * ab_corr.argmax() - time_slot[-1]
            t_shift = dtime_slot[ab_corr.argmax()]
            phase_shift = ((2.0 * np.pi) * ((t_shift / (1.0 / freq_hz)) % 1.0)) - np.pi        
            phase_shift_angle = phase_shift / math.pi * 360
            print(f'Observed Phaseshift: {phase_shift} & Phaseshift (angle) {phase_shift_angle}')
            phase_shift_angle = abs(phase_shift_angle)
            return phase_shift_angle
        except Exception as e:
            print(f"Error in method: unbalance.py - phaseShift, with ex: {e}")
 
    def phase_estimation(self,fund_freq_1: int, fund_freq_2: int):
        xf = np.fft.fftfreq(len(self.avg_fftx), 1 /self.Sampling_Frequency)
        
        index_one = np.where(np.isclose(xf, fund_freq_1))
        fftdata1=np.array(self.avg_fftx)
        phase_one = np.degrees(np.angle(fftdata1[index_one])) + 90
        index_two = np.where(np.isclose(xf, fund_freq_2))
        fftdata2=np.array(self.avg_ffty)
        phase_two = np.degrees(np.angle(fftdata2[index_two])) + 90
        phasediff=phase_two-phase_two
        return phasediff
       
    def unbalance_total_check(self):
        unbalance_output_res = []
        try:
            AmplitueAbove40Percent1XHarmonic = self.unbalance_harmonics_check()
            phasedata=self.phaseShift()
            phasedata2=self.phase_estimation(fund_freq_1=50, fund_freq_2=150)
            # Returning faults with respect to their condition
            # Check for other faults
            if AmplitueAbove40Percent1XHarmonic == 1:
                Unbalance_result = "10"
                unbalance_output_res.append(Unbalance_result)

            # There's no Unbalance Fault
            else:
                Unbalance_result = "9"
                unbalance_output_res.append(Unbalance_result)

            data = [self.Equipment_id, self.Sensor_id, "F", json.dumps(unbalance_output_res) + "$T$" + str(time.time())]
            
            # Stop individual data publish
            # v_helper.helper.data_to_publish.append(data)

            return unbalance_output_res
        except:
            unbalance_logger.error(
                "Exception occurred while checking Unbalance result", exc_info=True)
