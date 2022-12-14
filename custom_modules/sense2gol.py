import numpy as np
import itertools
import re
import os
import easygui
import serial
import sys
sys.path.insert(1, ".")
sys.path.insert(1, "../..")
from custom_modules.signal_processing import FFT_parameters
import json
from datetime import datetime

def load_settings():
    # Load settings from *.json file.
    with open('sense2gol_pizero/settings.json') as f:
        settings = json.load(f)
    
    # Radar installation settings
    HEIGHT_FROM_WATER_LEVEL = settings["radar-installation"]["height-from-water-level"] # meters.
    TILT_ANGLE_DEG = settings["radar-installation"]["tilt-angle-deg"] # Degree.
    tiltAngle_DEG_str = "tilt" + str("{0:.1f}".format(TILT_ANGLE_DEG)) + "deg"
    ANTENNA_BEAM_WIDTH_ELEVATION = settings["radar-installation"]["antenna-beam-width-elevation"] # Degree.
    ANTENNA_BEAM_WIDTH_AZIMUTH = settings["radar-installation"]["antenna-beam-width-azimuth"] # Degree.

    # Sense2GoL settings
    SAMPLING_FREQUENCY = float(settings["sense2gol"]["sampling-frequency-Hz"]) # Hz
    print('Sampling frequency: {:.3e}'.format(SAMPLING_FREQUENCY) + ' Hz')
    time_resolution = 1/SAMPLING_FREQUENCY # s
    print('Time resolution: {:.3e}'.format(time_resolution) + ' s')
    FRAMES = int(settings["sense2gol"]["number-of-frames"])
    print("Number of frames (for each direction): ", FRAMES)
    SAMPLES_PER_FRAME = int(settings["sense2gol"]["samples-per-frame"]) # To change this value, you must reprogram the Sense2GoL board.
    print("Samples per frame (for each direction): ", SAMPLES_PER_FRAME)
    EQ_ACQUISITION_TIME = 1/SAMPLING_FREQUENCY*SAMPLES_PER_FRAME*FRAMES
    print("Equivalent acquisition time (for each direction): {:.3e} s".format(EQ_ACQUISITION_TIME))
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
    FFT_initialized, freqBins_FFT, smoothingBins, minBin, frequencyMin_fixed, maxBin, frequencyMax_fixed = FFT_parameters(COMPLEX_FFT, SAMPLING_FREQUENCY, FFT_RESOL, SMOOTHING, SMOOTHING_WINDOW, FREQUENCY_MIN, FREQUENCY_MAX, PRINT_FFT_INFO)
    OFFSET_REMOVAL = settings["signal-processing"]["offset-removal"] # Boolean.
    SPECTROGRAM_ENABLED = settings["signal-processing"]["spectrogram-enabled"] # Boolean.
    STFT_OVERLAPPING_SAMPLES = settings["signal-processing"]["stft-overlapping-samples"] # Number of samples.
    STFT_SAMPLES_IN_SEGMENT = settings["signal-processing"]["stft-samples-in-segment"] # Number of samples.
    STFT_BINS = settings["signal-processing"]["stft-bins"] # Number of bins.

    # Raspberry Pi Zero settings
    PWM_PIN = settings["raspberry-pi-zero"]["pwm-board-pin"] # Board pin number.
    PWM_FREQUENCY = settings["raspberry-pi-zero"]["pwm-frequency"] # 50 Hz default.
    RAW_DATA = settings["raspberry-pi-zero"]["raw-data"] # Boolean. Data stored in *.txt files.
    SHOW_FIGURE = settings["raspberry-pi-zero"]["show-figure"] # Boolean. Disable if running on Raspberry Pi Zero without GUI.
    SAVE_PLOTS = settings["raspberry-pi-zero"]["save-plots"] # Boolean. For each acquisition, the plots saved in PNG or PDF format.
    PNG_PLOT = settings["raspberry-pi-zero"]["png-plot"] # Boolean.
    PDF_PLOT = settings["raspberry-pi-zero"]["pdf-plot"] # Boolean. 
    PLOT_PATH = settings["raspberry-pi-zero"]["plot-path"]
    REALTIME_MEAS = settings["raspberry-pi-zero"]["realtime-measurements"] # Boolean. Real-time measurements of Doppler velocity.
    TARGET_THRESHOLD = settings["raspberry-pi-zero"]["target-threshold-dBV"] # dBV. If FFT maximum is under this value, target not detected.
    MIN_BEAM_ANGLE = settings["raspberry-pi-zero"]["min-beam-angle"] # Degree. Angle between broadside direction and beam direction.
    MAX_BEAM_ANGLE = settings["raspberry-pi-zero"]["max-beam-angle"] # Degree. Angle between broadside direction and beam direction.
    DIRECTIONS = settings["raspberry-pi-zero"]["directions"]
    if DIRECTIONS == 1: # Only broadside direction
        antennaBeamDirections_DEG = np.array([0])
    else:
        antennaBeamDirections_DEG = np.linspace(start=MIN_BEAM_ANGLE, stop=MAX_BEAM_ANGLE, num=DIRECTIONS, endpoint=True) # Degrees.

    # Statistical analysis settings
    STATISTICAL_ANALYSIS = settings["statistical-analysis"]["enabling"] # Boolean. Enable/disable statystical analysis.
    EPISODES = int(settings["statistical-analysis"]["episodes-number"]) # Number of episodes for the statystical analysis.
    if STATISTICAL_ANALYSIS == True:
        assert (EPISODES>=3), "Number of episodes should be 3 at least. Please edit \"settings.json\"."
    
    return HEIGHT_FROM_WATER_LEVEL, ANTENNA_BEAM_WIDTH_ELEVATION, ANTENNA_BEAM_WIDTH_AZIMUTH, SAMPLING_FREQUENCY, lines_to_be_read, ADC_RANGE_BITS, ADC_RANGE_V, COMPLEX_FFT, SMOOTHING, BANDWIDTH_THRESHOLD, HANNING_WINDOWING, ZERO_FORCING, FFT_initialized, freqBins_FFT, smoothingBins, minBin, frequencyMin_fixed, maxBin, frequencyMax_fixed, OFFSET_REMOVAL, SPECTROGRAM_ENABLED, STFT_OVERLAPPING_SAMPLES, STFT_SAMPLES_IN_SEGMENT, STFT_BINS, PWM_PIN, PWM_FREQUENCY, RAW_DATA, SHOW_FIGURE, SAVE_PLOTS, PNG_PLOT, PDF_PLOT, PLOT_PATH, REALTIME_MEAS, TARGET_THRESHOLD, DIRECTIONS, antennaBeamDirections_DEG, TILT_ANGLE_DEG, tiltAngle_DEG_str, STATISTICAL_ANALYSIS, EPISODES

def txt_extract(file_name, ADC_RANGE_BITS, ADC_RANGE_V, SAMPLING_FREQUENCY):
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

def serialPort_acquisition(tiltAngle_DEG_str, episode, EPISODES, direction_DEG_str, lines_to_be_read):
    # Boolean variable that will represent 
    # whether or not the Sense2GoL is connected
    connected = False
    # Establish connection to the serial port that your Sense2GoL 
    # is connected to.
    LOCATIONS=['/dev/ttyACM0']
    for device in LOCATIONS:
        try:
            print("Trying...",device)
            S2GL = serial.Serial(device, 128000)
            break
        except:
            print("Failed to connect on ", device)

    # Loop until the Sense2GoL tells us it is ready
    while not connected:
        serin = S2GL.read()
        connected = True
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    episode_str = "episode" + str(episode+1) + "of" + str(EPISODES)
    raw_data_label = timestamp + "__" + tiltAngle_DEG_str + "__" + episode_str + "__" + direction_DEG_str
    completeFileName = txt_generate(S2GL, lines_to_be_read, raw_data_label)
    S2GL.close()
    return completeFileName

if __name__ == "__main__":
    print("Standalone script not yet developed.")
