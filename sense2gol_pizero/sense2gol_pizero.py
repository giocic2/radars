#!/usr/bin/python
# Sense2GoL radar controlled by Raspberry Pi Zero.
# Launch the script from the root of the GitHub repository.

import json
import serial
from datetime import datetime
import os.path
import sys
sys.path.insert(1, ".")
from custom_modules.FFT import FFT_complex


def main():

    # Load settings from *.json file.
    with open('sense2gol_pizero/settings.json') as f:
        settings = json.load(f)
    f.close()

    # Sense2GoL settings
    SAMPLING_FREQUENCY = 3e3 # Hz
    print('Sampling frequency: {:,}'.format(SAMPLING_FREQUENCY) + ' Hz')
    time_resolution = 1/SAMPLING_FREQUENCY # s
    print('Time resolution: {:,}'.format(time_resolution) + ' s')
    ACQUISITION_TIME = settings["sense2gol"]["acquisition-time-s"] # s
    print("Acquisition time (for each direction): ", ACQUISITION_TIME, ' s')
    SAMPLES_PER_FRAME = int(settings["sense2gol"]["samples-per-frame"])
    frames = round(ACQUISITION_TIME * SAMPLING_FREQUENCY / SAMPLES_PER_FRAME)
    print("Samples per frame (for each direction): ", SAMPLES_PER_FRAME)
    print("Number of frames (for each direction): ", frames)
    OVERHEAD = settings["sense2gol"]["overhead"]
    lines_read = (frames * 8 + 1 + 1) * 2 + OVERHEAD

    # Signal processing settings
    FFT_RESOL = settings["signal-processing"]["fft-resolution-Hz"] # Hz
    SMOOTHING_WINDOW = settings["signal-processing"]["smoothing-window-Hz"] # Hz. Smoothing of FFT spectrum done with moving average.
    BANDWIDTH_THRESHOLD = settings["signal-processing"]["bandwidth-threshold-dB"] # dB. Parameter that defines the bandwidth of the Doppler centroid, with respect to the maximum value.
    HANNING_WINDOWING = settings["signal-processing"]["hanning-windowing"] # Boolean. Enable Hanning windowing on samples before FFT computation.
    ZERO_FORCING = settings["signal-processing"]["zero-forcing"] # Boolean. Enable forcing FFT to zero, everywhere except between FREQUENCY_MIN and FREQUENCY_MAX.
    FREQUENCY_MIN = settings["signal-processing"]["frequency-min-Hz"] # Hz. Before that frequency, FFT forced to zero.
    FREQUENCY_MAX = settings["signal-processing"]["frequency-max-Hz"] # Hz. After that frequency, FFT forced to zero.

    # Raspberry Pi Zero settings
    RAW_DATA = settings["raspberry-pi-zero"]["raw-data"] # Boolean. Data stored in *.csv files.
    REALTIME_MEAS = settings["raspberry-pi-zero"]["realtime-measurements"] # Boolean. Real-time measurements of Doppler velocity.
    TARGET_THRESHOLD = settings["raspberry-pi-zero"]["target-threshold-dBV"] # dBV. If FFT maximum is under this value, target not detected.

    # Statistical analysis settings
    STATISTICAL_ANALYSIS = settings["statistical-analysis"]["enabling"] # Boolean. Enable/disable statystical analysis.
    EPISODES = int(settings["statistical-analysis"]["episodes-number"]) # Number of episodes for the statystical analysis.
    if STATISTICAL_ANALYSIS == True:
        assert (EPISODES>=3), "Number of episodes should be 3 at least. Please edit \"settings.json\"."
    
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
    samplesFileName = timestamp + ".txt"
    completeFileName = os.path.join('sense2gol_pizero/raw-samples',samplesFileName)
    # open text file to store the current   
    text_file = open(completeFileName, 'wb')
    # read serial data and write it to the text file
    index = 0
    print("Acquisition started...")
    while index <= lines_read:
        if S2GL.inWaiting():
            x=S2GL.readline()
            text_file.write(x)
            if x=="\n":
                text_file.seek(0)
                text_file.truncate()
            text_file.flush()
        index += 1
    print("Raw data acquisition completed.")
    # close the serial connection and text file
    text_file.close()
    S2GL.close()
    

    FFT_complex(samplingFrequency=SAMPLING_FREQUENCY, resolution=FFT_RESOL, smoothingWindow=SMOOTHING_WINDOW, frequencyMin=FREQUENCY_MIN, frequencyMax=FREQUENCY_MAX)

if __name__ == "__main__":
    main()