import pylab as pyl
import numpy as np
import scipy as sy
import scipy.fftpack as syfp
from scipy import signal
from scipy.fftpack import fft, ifft
import matplotlib.pyplot as plt
import pandas as pd
import os
from scipy.signal import find_peaks_cwt
import csv
import heapq
import datetime
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import scipy.signal
import numpy as np
import collections
from numpy import (array, dot, arccos, clip)
from numpy.linalg import norm
from configparser import ConfigParser

import timeit
import time
import math
from collections import Counter

class Angle:
	def __init__(self,horizontAccelData, verticalAccelData):
		self.df1 = horizontAccelData
		self.df2 = verticalAccelData



	def angleis(self):
		try:
			v1=self.df1
			v2=self.df2
			c = dot(v1,v2)/norm(v1)/norm(v2)
			angle = arccos(clip(c, -1, 1)) 
			AngleinDegree = (angle*360)/(2*3.14)
			# print(AngleinDegree)
			return AngleinDegree
		except Exception as e:
			print(f"Error in method: phase_angle.py - angleis, with ex: {e}")
	
	def CallerMain(self):
		self.angleis()

	# Below is online code, since I have used it inside dataframe, below use self.df1['v'] for horizont and vertical
	def phasefind(self):
		try:
			horizontalaxesamplitude = list(self.df1)#['v'])
			verticalamplitude = list(self.df2)#['v'])
			if len(self.df2)!=len(self.df1):
				difference = abs(len(horizontalaxesamplitude)-len(verticalamplitude))
				if len(horizontalaxesamplitude)>len(verticalamplitude):
					horizontalaxesamplitude = horizontalaxesamplitude[: -difference or None]  #to delete last n elemenets
					verticalamplitude = verticalamplitude
				elif len(verticalamplitude)>len(horizontalaxesamplitude):
					verticalamplitude = verticalamplitude[: -difference or None] 
					horizontalaxesamplitude = horizontalaxesamplitude
				amplitudeX =  horizontalaxesamplitude 
				amplitudeY =  verticalamplitude 
				c = dot(amplitudeX,amplitudeY)/norm(amplitudeX)/norm(amplitudeY)
				angle = arccos(clip(c, -1, 1))
				angleindegree = ((angle*360)/(2*3.14))
				# print('angle in degree',((angle*360)/(2*3.14)))
				return angleindegree
			else:
				amplitudeX =  horizontalaxesamplitude 
				amplitudeY =  verticalamplitude
				c = dot(amplitudeX,amplitudeY)/norm(amplitudeX)/norm(amplitudeY)
				angle = arccos(clip(c, -1, 1))
				angleindegree = ((angle*360)/(2*3.14))
				# print('angle in degree',((angle*360)/(2*3.14)))
				return angleindegree
		except Exception as e:
			print(f"Error in method: phase_angle.py - phasefind, with ex {e}")

# for_phase_accel_Horizon = pd.read_csv(r'D:\vegam_csv_files\Literature_data\normal_Mafaulda\Downsampled_and_sending_vMaint\acceleromter_values_downsampled\v3_20.2752.csv')
# for_phase_accel_verti = pd.read_csv(r'D:\vegam_csv_files\Literature_data\normal_Mafaulda\Downsampled_and_sending_vMaint\acceleromter_values_downsampled\25.csv')
# v1 = for_phase_accel_Horizon['v']
# v2 = for_phase_accel_verti['v']
