import json
import numpy as np
import pandas as pd
# import logers as log
import logging
import vanalytics_helper as v_helper
import vanalytics_data as v_data
from logging_manager import rpm_logger
class RpmFromVibration():

    # log = rpm_logger.customLogger(logging.DEBUG)

    def __init__(self, sampling_freq, windowsize, shaftSpeed, sensor_id,
                 equipment_id, fftlist):
        '''
        sampling_freq : Sampling Frequency of the sensor
        noOfSample : Number of samples in FFT, Accelerometer X and Accelerometer Y
        windowsize : window size of the fft data
        shaftSpeed : Maximum speed of the Motor
        fftlist    : FFT Data
        FreqInHzConv : To convert RPM into Hz
        thresholdStart : Amplitude range starts at 0.3 times frequency  (float(1.2))
        thresholdend : Amplitude range ends at 1.2 times frequency  (float(1.2))
        FFTStartRng : FFT Start Range
        '''
        self.Sampling_Frequency = sampling_freq
        self.Window_Size = windowsize
        self.MaximumSpeed = shaftSpeed
        self.sensor_id = sensor_id
        self.equipment_id = equipment_id
        self.FFT_list = fftlist
        self.thresholdStart = float(2.3)
        self.thresholdend = float(2.8)
        self.start = 0.0
        self.end = 1.0
        self.FreqInHzConv = 60
        self.Two = 2
        self.FFTStartRng = 0

    def Speed_Detection(self):
        try:
            time = 1 / self.Sampling_Frequency
            # FFT Amplitudes
            # fft_y = np.array(self.FFT_list[self.FFTStartRng : self.Window_Size])
            # FFT Frequencies            
            fft_x = np.linspace(self.start, self.end /
                                (self.Two * time), self.Window_Size//2)
            
            fft_frequencies = list(fft_x)
            fft_amplitudes = self.FFT_list
            # Converting ShaftSpeed from rev/min to Hertz (Hz)
            maximum_rpm_hz = self.MaximumSpeed / self.FreqInHzConv
            # Frequency Start Limit
            rpm_thresholdStart = self.thresholdStart * maximum_rpm_hz
            # Frequency End Limit
            rpm_thresholdend = self.thresholdend * maximum_rpm_hz

            # Indexes which is between than Frequency Limits
            indexfreqencylesthanrpm = [fft_amplitudes[k] for k in range(
                len(fft_frequencies)) if rpm_thresholdStart <= fft_frequencies[k] <= rpm_thresholdend]

            # Maximum Amplitude among the list in amplitudesrpm
            maxoneamplitude = max(indexfreqencylesthanrpm)
            # Index of the Maximum Amplitude
            indexofamplitude = fft_amplitudes.index(maxoneamplitude)
            # Frequency corresponding to the Index
            freuencycorrestomaxampl = fft_frequencies[indexofamplitude]
            # Int of the Speed (Hz)
            RPM_from_Vib = round(freuencycorrestomaxampl/3, 2)

            data = [self.equipment_id, self.sensor_id, "R", RPM_from_Vib]
            v_helper.helper.data_to_publish.append(data)

            rpm_logger.info("Calculating Shaft Speed From FFT Data")
            if v_data.CommonFeatures.simulator_rpm > 0:
                return round((v_data.CommonFeatures.simulator_rpm / 60), 2)
            else:
                return RPM_from_Vib
        except:
            rpm_logger.error(
                "Exception occurred while Calculating Shaft Speed From FFT Data", exc_info=True)


#hi this is purbasha, test line to show how git works for nk and supriya
'''
check status
git add
git commit
git push
'''