import numpy as np
import itertools
import re
import os
import easygui
import sys
sys.path.insert(1, ".")
sys.path.insert(1, "../..")
from custom_modules.plots_readytouse import plot_paper_format
import json
from custom_modules.signal_processing import FFT_parameters, FFT

def txt_extract(file_name):
    # Extract raw samples from txt file
    text_file = open(file_name, 'rb')
    temp_line = text_file.readline()
    done = False
    I_samples = []
    Q_samples = []
    # Locate I samples
    temp_line = text_file.readline()
    temp_line = temp_line.decode('ascii')
    while temp_line != '  ------------- I raw samples ------------- \n':
        temp_line = text_file.readline()
        temp_line = temp_line.decode('ascii')

    while not done:
        if temp_line == '  ------------- I raw samples ------------- \n':
            temp_line = text_file.readline()
            temp_line = temp_line.decode('ascii')
            while temp_line != '  ------------- Q raw samples ------------- \n':
                temp_line_int = list(map(int, re.findall(r'\d+', temp_line)))
                if temp_line_int != '\r\n':
                    I_samples = list(itertools.chain(I_samples, temp_line_int))
                temp_line = text_file.readline()
                temp_line = temp_line.decode('ascii')
                if temp_line == '':
                    done = True
                    break
            if temp_line == '  ------------- Q raw samples ------------- \n':
                temp_line = text_file.readline()
                temp_line = temp_line.decode('ascii')
        temp_line_int = list(map(int, re.findall(r'\d+', temp_line)))
        if temp_line_int != '\r\n' and temp_line != '':
            Q_samples = list(itertools.chain(Q_samples, temp_line_int))
        temp_line = text_file.readline()
        temp_line = temp_line.decode('ascii')
        if temp_line == '':
            done = True
    print("Raw data extracted from .txt file.")
    print("Number of IFI samples: ", len(I_samples))
    print("Number of IFQ samples: ", len(Q_samples))

    IQ_arrays_length = min(len(I_samples), len(Q_samples))
    print("Processed signals length: ", IQ_arrays_length)

    # Seems that Q and I needs to be inverted
    Q_array = np.array(I_samples[0:IQ_arrays_length])
    I_array = np.array(Q_samples[0:IQ_arrays_length])

    # Convert V to mV
    I_array_mV = I_array * (ADC_RANGE_V / ADC_RANGE_BITS) * 1000 # mV
    Q_array_mV = Q_array * (ADC_RANGE_V / ADC_RANGE_BITS) * 1000 # mV
    # Convert to complex
    complexSignal_mV = np.array(IQ_arrays_length)
    complexSignal_mV = np.add(I_array_mV, 1j*Q_array_mV)
    timeAxis_s = np.linspace(start=0, num=IQ_arrays_length, stop=IQ_arrays_length, endpoint=False) / SAMPLING_FREQUENCY

    return I_array_mV, Q_array_mV, complexSignal_mV, timeAxis_s, IQ_arrays_length

def txt_generate(serialDevice, lines_to_be_read, timestamp):
    samplesFileName = timestamp + ".txt"
    completeFileName = os.path.join('sense2gol_pizero/output',samplesFileName)
    # open text file to store the current
    text_file = open(completeFileName, 'wb')
    # read serial data and write it to the text file
    index = 0
    print("Acquisition started...")
    while index <= lines_to_be_read:
        if serialDevice.inWaiting():
            x=serialDevice.readline()
            text_file.write(x)
            if x=="\n":
                text_file.seek(0)
                text_file.truncate()
            text_file.flush()
        index += 1
    print("Raw data acquisition completed.")
    # close the serial connection and text file
    text_file.close()
    return completeFileName

if __name__ == "__main__":
    # Open raw samples from *.txt files
    txt_filename = None
    while txt_filename == None:
        txt_filename = easygui.fileopenbox(title = "Choose *.txt file to analyse...", default = "*.txt")
    print(txt_filename)
    # Read tilt angle and direction angle from filename
    tiltAngle_DEG = re.search('__tilt(.+?)deg__', txt_filename)
    tiltAngle_DEG = float(tiltAngle_DEG.group(1))
    print("Tilt angle: {:.1f} degree".format(tiltAngle_DEG))
    antennaBeamDirection_DEG = re.search('__dir(.+?)deg', txt_filename)
    antennaBeamDirection_DEG = float(antennaBeamDirection_DEG.group(1))
    print("Beam direction: {:.1f} degree".format(antennaBeamDirection_DEG))
    # Open acquisition settings
    json_filename = None
    while json_filename == None:
        json_filename = easygui.fileopenbox(title = "Choose *.json file to read acquisition settings...", default = "*.json")
    print(json_filename)

    # Load settings from *.json file.
    with open(json_filename) as f:
        settings = json.load(f)
    f.close()

    # Sense2GoL settings
    SAMPLING_FREQUENCY = 3e3 # Hz
    print('Sampling frequency: {:,}'.format(SAMPLING_FREQUENCY) + ' Hz')
    time_resolution = 1/SAMPLING_FREQUENCY # s
    print('Time resolution: {:,}'.format(time_resolution) + ' s')
    FRAMES = int(settings["sense2gol"]["number-of-frames"])
    print("Number of frames (for each direction): ", FRAMES)
    SAMPLES_PER_FRAME = int(settings["sense2gol"]["samples-per-frame"]) # To effectively change this value, you must reprogram the Sense2GoL board.
    print("Samples per frame (for each direction): ", SAMPLES_PER_FRAME)
    EQ_ACQUISITION_TIME = 1/SAMPLING_FREQUENCY*SAMPLES_PER_FRAME*FRAMES
    print("Equivalent acquisition time (for each direction): {:,}", EQ_ACQUISITION_TIME, ' s')
    OVERHEAD = int(settings["sense2gol"]["overhead"])
    lines_to_be_read = int((FRAMES * 8 + 1 + 1) * 2 + OVERHEAD)
    ADC_RANGE_BITS = int(2**settings["sense2gol"]["adc-resolution-bits"]) # Bits.
    ADC_RANGE_V = settings["sense2gol"]["adc-range-v"] # Volts.

    # Signal processing settings
    COMPLEX_FFT = settings["signal-processing"]["complex-fft"] # Boolean. If True, the FFT of a complex signal (two-sided spectrum) is computed.
    FFT_RESOL = settings["signal-processing"]["fft-resolution-Hz"] # Hz
    SMOOTHING = settings["signal-processing"]["fft-smoothing"] # Boolean.
    SMOOTHING_WINDOW = settings["signal-processing"]["smoothing-window-Hz"] # Hz. Smoothing of FFT spectrum done with moving average.
    BANDWIDTH_THRESHOLD = settings["signal-processing"]["bandwidth-threshold-dB"] # dB. Parameter that defines the bandwidth of the Doppler centroid, with respect to the maximum value.
    HANNING_WINDOWING = settings["signal-processing"]["hanning-windowing"] # Boolean. Enable Hanning windowing on samples before FFT computation.
    ZERO_FORCING = settings["signal-processing"]["zero-forcing"] # Boolean. Enable forcing FFT to zero, everywhere except between FREQUENCY_MIN and FREQUENCY_MAX.
    FREQUENCY_MIN = settings["signal-processing"]["frequency-min-Hz"] # Hz. Before that frequency, FFT forced to zero.
    FREQUENCY_MAX = settings["signal-processing"]["frequency-max-Hz"] # Hz. After that frequency, FFT forced to zero.
    PRINT_FFT_INFO = settings["signal-processing"]["print-fft-info"] # Boolean.
    FFT_initialized = FFT_parameters(COMPLEX_FFT, SAMPLING_FREQUENCY, FFT_RESOL, SMOOTHING, SMOOTHING_WINDOW, FREQUENCY_MIN, FREQUENCY_MAX, PRINT_FFT_INFO)
    OFFSET_REMOVAL = settings["signal-processing"]["offset-removal"] # Boolean.

    # Raspberry Pi Zero settings
    RAW_DATA = settings["raspberry-pi-zero"]["raw-data"] # Boolean. Data stored in *.csv files.
    SHOW_FIGURE = settings["raspberry-pi-zero"]["show-figure"] # Boolean. Disable if running on Raspberry Pi Zero without GUI.
    SAVE_PLOTS = settings["raspberry-pi-zero"]["save-plots"] # Boolean. For each acquisition, the plots saved in PNG or PDF format.
    PNG_PLOT = settings["raspberry-pi-zero"]["png-plot"] # Boolean.
    PDF_PLOT = settings["raspberry-pi-zero"]["pdf-plot"] # Boolean. 
    REALTIME_MEAS = settings["raspberry-pi-zero"]["realtime-measurements"] # Boolean. Real-time measurements of Doppler velocity.
    TARGET_THRESHOLD = settings["raspberry-pi-zero"]["target-threshold-dBV"] # dBV. If FFT maximum is under this value, target not detected.
    DIRECTIONS = settings["raspberry-pi-zero"]["directions"]

    # Time-domain signals
    I_array, Q_array, array_length = txt_extract(txt_filename)
    timeAxis = np.linspace(start=0, num=array_length, stop=array_length, endpoint=False)
    # Time domain plots of I/Q components.
    plot_paper_format(timeAxis, I_array, "Sample number (adim.)", "IFI (ADC level)", timestamp=None, showFigure=True, savePlot=False)
    plot_paper_format(timeAxis, Q_array, "Sample number (adim.)", "IFQ (ADC level)", timestamp=None, showFigure=True, savePlot=False)

    # FFT
    I_array_mV = I_array * (ADC_RANGE_V / ADC_RANGE_BITS)
    Q_array_mV = Q_array * (ADC_RANGE_V / ADC_RANGE_BITS)
    complexSignal_mV = np.array(array_length)
    complexSignal_mV = np.add(I_array_mV, 1j*Q_array_mV)
    FFT_dBV_peak, centroid_frequency, surface_velocity, FFT_dBV, freqAxis_Hz = FFT(complexSignal_mV, COMPLEX_FFT, array_length, SAMPLING_FREQUENCY, OFFSET_REMOVAL, HANNING_WINDOWING, ZERO_FORCING, SMOOTHING, TARGET_THRESHOLD, BANDWIDTH_THRESHOLD, antennaBeamDirection_DEG, tiltAngle_DEG)
    # FFT plot
    plot_paper_format(freqAxis_Hz, FFT_dBV, "Frequency (Hz)", "FFT magnitude (dBV)", timestamp=None, showFigure=True, savePlot=False)
