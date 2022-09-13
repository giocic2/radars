#!/usr/bin/python
# Sense2GoL radar controlled by Raspberry Pi Zero.
# Launch the script from the root of the GitHub repository.

from doctest import ELLIPSIS_MARKER
import json
import serial
from datetime import datetime
import os.path
import sys
sys.path.insert(1, ".")
from custom_modules.FFT import FFT_parameters, FFT
from custom_modules.sense2gol_rawdata import txt_extract, txt_generate
import numpy as np


def main():

    # Load settings from *.json file.
    with open('sense2gol_pizero/settings.json') as f:
        settings = json.load(f)
    f.close()

    # Sense2GoL settings
    COMPLEX_FFT = settings["sense2gol"]["complex-fft"] # Boolean. If True, the FFT of a complex signal (two-sided spectrum) is computed.
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
    ADC_RANGE_V = settings["sense2gol"]["adc-resolution"] # Volts.

    # Signal processing settings
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
    REALTIME_MEAS = settings["raspberry-pi-zero"]["realtime-measurements"] # Boolean. Real-time measurements of Doppler velocity.
    TARGET_THRESHOLD = settings["raspberry-pi-zero"]["target-threshold-dBV"] # dBV. If FFT maximum is under this value, target not detected.
    DIRECTIONS = settings["raspberry-pi-zero"]["directions"]

    # Statistical analysis settings
    STATISTICAL_ANALYSIS = settings["statistical-analysis"]["enabling"] # Boolean. Enable/disable statystical analysis.
    EPISODES = int(settings["statistical-analysis"]["episodes-number"]) # Number of episodes for the statystical analysis.
    if STATISTICAL_ANALYSIS == True:
        assert (EPISODES>=3), "Number of episodes should be 3 at least. Please edit \"settings.json\"."
    
    for episode in range(EPISODES):
        for direction in range(DIRECTIONS):
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
                    print("Failed to connect on ",device)

            # Loop until the Sense2GoL tells us it is ready
            while not connected:
                serin = S2GL.read()
                connected = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            completeFileName = txt_generate(S2GL, lines_to_be_read, timestamp)
            S2GL.close()

            I_array, Q_array, array_length = txt_extract(completeFileName)
            I_array_mV = I_array * (ADC_RANGE_V / ADC_RANGE_BITS)
            Q_array_mV = Q_array * (ADC_RANGE_V / ADC_RANGE_BITS)
            complexSignal_mV = np.array(array_length)
            complexSignal_mV = np.add(I_array_mV, 1j*Q_array_mV)
            timeAxis_s = np.linspace(start=0, num=array_length, stop=array_length, endpoint=False) / SAMPLING_FREQUENCY
            
            assert FFT_initialized, "FFT not initialized. Use \'FFT_parameters()\' from FFT.py costum module."
            FFT(complexSignal_mV, COMPLEX_FFT, array_length, SAMPLING_FREQUENCY, OFFSET_REMOVAL, HANNING_WINDOWING, ZERO_FORCING, SMOOTHING, TARGET_THRESHOLD, BANDWIDTH_THRESHOLD)

if __name__ == "__main__":
    main()