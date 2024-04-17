import pytest
import pathlib
import sys

#from finalised_code_velocity_fft_vrms import AnalyticsVelFFTCal
import numpy as np
path = r"D:\velocity_new_algo"
path1=r'D:\velocity_new_algo\tests\data_for_validations'

sys.path.insert(1, str(path) + '\\SourceCode\\app\\velocity_fft')
sys.path.insert(2, str(path) + '\\tests\\data_for_validations')

from Software.src.backup_before_make_change_avg_8192 import AnalyticsVelFFTCal
# import Software.src.import_constants as constants
import pandas as pd

test_acc_data = list(range(100)) #  data with 8192 samples
sampling_rate = 1200  # Hz
number_of_samples = 100
windowsize = 100
accfft_25hz=pd.read_csv(r'data_25.csv')['col1'].values
vfft_25hz=pd.read_csv(r'data_25.csv')['col2'].values

accfft_50hz=pd.read_csv(r'data_50.csv')['col1'].values
vfft_50hz=pd.read_csv(r'data_50.csv')['col2'].values

accfft_200hz=pd.read_csv(r'data_200.csv')['col1'].values
vfft_200hz=pd.read_csv(r'data_200.csv')['col2'].values

accfft_400hz=pd.read_csv(r'data_400.csv')['col1'].values
vfft_400hz=pd.read_csv(r'data_400.csv')['col2'].values

accfft_800hz=pd.read_csv(r'data_800.csv')['col1'].values
vfft_800hz=pd.read_csv(r'data_800.csv')['col2'].values

accfft_1000hz=pd.read_csv(r'data_1000.csv')['col1'].values
vfft_1000hz=pd.read_csv(r'data_1000.csv')['col2'].values


accfft_vyn2=pd.read_csv(r'data_vyna_1.csv')['col1'].values
vfft_vyn2=pd.read_csv(r'data_vyna_1.csv')['col2'].values


accfft_vyn3=pd.read_csv(r'data_vyna_1_25.csv')['col1'].values
vfft_vyn3=pd.read_csv(r'data_vyna_1_25.csv')['col2'].values


@pytest.fixture
def analytics_calculator():
    return AnalyticsVelFFTCal()
### test with sine wave data
def test_25hz_signal(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 25 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_25hz, abs=0.1)
    assert result2 == pytest.approx(vfft_25hz, abs=0.1)
    assert result3 == pytest.approx(44.1387, abs=tolerance)

def test_50hz_signal(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 50 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_50hz, abs=0.1)
    assert result2 == pytest.approx(vfft_50hz, abs=0.1)
    assert result3 == pytest.approx(22.06, abs=tolerance)


def test_200hz_signal_vrms(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 200 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_200hz, abs=0.1)
    assert result2 == pytest.approx(vfft_200hz, abs=0.1)
    assert result3 == pytest.approx(5.5174, abs=tolerance)


def test_400hz_signal_vrms(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 400 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_400hz, abs=0.1)
    assert result2 == pytest.approx(vfft_400hz, abs=0.1)
    assert result3 == pytest.approx(2.7587, abs=tolerance)


def test_800hz_signal_vrms(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 800 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_800hz, abs=tolerance)
    assert result2 == pytest.approx(vfft_800hz, abs=tolerance)
    assert result3 == pytest.approx(1.3793, abs=tolerance)

def test_1000hz_signal_vrms(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 1000 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_1000hz, abs=tolerance)
    assert result2 == pytest.approx(vfft_1000hz, abs=tolerance)
    assert result3 == pytest.approx(1.1036, abs=tolerance)



def test_vyana_signal_vrms(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1.83 * np.sin(2 * np.pi * 78 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_vyn2, abs=tolerance)
    assert result2 == pytest.approx(vfft_vyn2, abs=tolerance)
    assert result3 == pytest.approx(26.5, abs=tolerance)


def test_vyana_signal(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1.83 * np.sin(2 * np.pi * 78 * time)
    tolerance = 1
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert result == pytest.approx(accfft_vyn3, abs=tolerance)
    assert result2 == pytest.approx(vfft_vyn3, abs=tolerance)
    assert result3 == pytest.approx(26.5, abs=tolerance)
    

# Test case to check if the output is a NumPy array
def test_type_of_output(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 1 * np.sin(2 * np.pi * 800 * time)
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert isinstance(result, np.ndarray)


# Test case to check if the output array has the correct length
def test_len_of_output(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 2 * np.sin(2 * np.pi * 800 * time)
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert len(result) == (4096) // 2 + 1  # Since we use rfft, the output length is N/2 + 1
def test_type_of_output_two(analytics_calculator):
    time = np.linspace(0, 1.28, 8192)
    accelerometer_data = 2 * np.sin(2 * np.pi * 800 * time)
    result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)
    assert isinstance(result3, float)

def test_exception(analytics_calculator):
    accelerometer_data = None
    sampling_rate=None
    number_of_samples=None
    windowsize=None
    with pytest.raises(ValueError) as exc_info:
        result,result2,result3 = analytics_calculator.get_acc_fft_velo_fft_vrms(accelerometer_data,sampling_rate,number_of_samples,windowsize)

    assert str(exc_info.value) == "data_improper"
