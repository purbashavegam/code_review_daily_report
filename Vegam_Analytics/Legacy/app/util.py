import logging
import sys
import math
#   external library
import numpy as np
import pandas as pd
import vanalytics_helper as v_helper
# import logers as log_file
import itertools
import vmaint_constants as constants

# ParserFftCalculation  class calculates and returns the AVERAGE, rms, frequencies whose amplitude are >3*rms


class ParserFftCalculation(object):
    #log = log_file.customLogger(logging.DEBUG)

    @classmethod
    def parse_fft_rawdata(cls, sampling_frequency, fft_data, rms_threshold_range = constants.THREE):
        try:

            # average of FFT data is done
            fft_average = [sum(e)/len(e) for e in zip(*fft_data)]
            
            # frequencies are selected
            xf = np.linspace(constants.START_RANGE, constants.END / (constants.TWO *
                                                                     (constants.END / sampling_frequency)), len(fft_average))
            # rms is calculated using average of FFT
            rms_of_fft_average = np.sqrt(np.mean(np.square(fft_average)))
            
            # checks for amplitudes index greater than 3 * rms
            amplitude_rms_index = [list(fft_average).index(i) for i in fft_average]
            # checks for the amplitudes for the index values
            horizontamplitudabove_rms_values = [i for i in fft_average]
            # corresponding freqns of amplitudes greater than 3*rms
            frequency_above_rms_values = [list(xf)[i]
                                          for i in amplitude_rms_index]

            output = [fft_average, rms_of_fft_average, horizontamplitudabove_rms_values, frequency_above_rms_values]
            return output

        except Exception as e:
            print(f"Error in methos: util.py - parse_fft_rawdata, with Ex {e}")     