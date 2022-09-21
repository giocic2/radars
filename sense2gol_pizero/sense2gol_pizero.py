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
from custom_modules.signal_processing import FFT_parameters, FFT
from custom_modules.sense2gol_rawdata import txt_extract, txt_generate
from custom_modules.plots_readytouse import plot_paper_format
import numpy as np
import shutil
import time
from scipy import stats


def main():

    # Load settings from *.json file.
    with open('sense2gol_pizero/settings.json') as f:
        settings = json.load(f)
    f.close()

    # Save current *.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = "./sense2gol_pizero/raw-samples/" + timestamp + ".json"
    shutil.copyfile("./sense2gol_pizero/settings.json",json_filename)
    time.sleep(1)

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
    PLOT_PATH = settings["raspberry-pi-zero"]["plot-path"]
    REALTIME_MEAS = settings["raspberry-pi-zero"]["realtime-measurements"] # Boolean. Real-time measurements of Doppler velocity.
    TARGET_THRESHOLD = settings["raspberry-pi-zero"]["target-threshold-dBV"] # dBV. If FFT maximum is under this value, target not detected.
    DIRECTIONS = settings["raspberry-pi-zero"]["directions"]
    if DIRECTIONS == 1: # Only broadside direction
        antennaBeamDirections_DEG = np.array([0])
    else:
        antennaBeamDirections_DEG = np.linspace(start=-15, stop=+15, num=DIRECTIONS, endpoint=True) # Degrees.
    tiltAngle_DEG = 45 # Degrees.
    tiltAngle_DEG_str = "tilt" + str("{0:.1f}".format(tiltAngle_DEG)) + "deg"

    # Statistical analysis settings
    STATISTICAL_ANALYSIS = settings["statistical-analysis"]["enabling"] # Boolean. Enable/disable statystical analysis.
    EPISODES = int(settings["statistical-analysis"]["episodes-number"]) # Number of episodes for the statystical analysis.
    if STATISTICAL_ANALYSIS == True:
        assert (EPISODES>=3), "Number of episodes should be 3 at least. Please edit \"settings.json\"."
    
    # Array to save FFT peak amplitudes and frequencies
    FFT_dBV_peaks = np.zeros((EPISODES, DIRECTIONS))
    centroid_frequencies = np.zeros((EPISODES, DIRECTIONS))
    surface_velocities_table = np.zeros((EPISODES, DIRECTIONS))

    for episode in range(EPISODES):
        print("*****************")
        print("EPISODE {:d} OF {:d}:".format(episode+1, EPISODES))
        for direction in range(DIRECTIONS):
            print("*****************")
            print("Scanning direction " + str(direction+1) + " of " + str(DIRECTIONS) + "...")
            direction_DEG = antennaBeamDirections_DEG[direction]
            direction_DEG_str = "dir" + str("{0:.1f}".format(direction_DEG)) + "deg"
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
            raw_data_label = timestamp + "__" + tiltAngle_DEG_str + "__" + direction_DEG_str
            completeFileName = txt_generate(S2GL, lines_to_be_read, raw_data_label)
            S2GL.close()

            # Extract time-domain signals
            I_array, Q_array, array_length = txt_extract(completeFileName)
            I_array_mV = I_array * (ADC_RANGE_V / ADC_RANGE_BITS)
            Q_array_mV = Q_array * (ADC_RANGE_V / ADC_RANGE_BITS)
            complexSignal_mV = np.array(array_length)
            complexSignal_mV = np.add(I_array_mV, 1j*Q_array_mV)
            timeAxis_s = np.linspace(start=0, num=array_length, stop=array_length, endpoint=False) / SAMPLING_FREQUENCY
            # Plot of time-domain signals
            plot_paper_format(timeAxis_s, I_array_mV, "Time (s)", "IFI (ADC level)", timestamp=timestamp, showFigure=True, savePlot=False)
            plot_paper_format(timeAxis_s, Q_array_mV, "Time (s)", "IFQ (ADC level)", timestamp=None, showFigure=True, savePlot=False)
            
            # FFT evaluation
            assert FFT_initialized, "FFT not initialized. Use \'FFT_parameters()\' from FFT.py costum module."
            FFT_dBV_peaks[episode,direction], centroid_frequencies[episode,direction], surface_velocities_table[episode,direction], FFT_dBV, freqAxis_Hz = FFT(complexSignal_mV, COMPLEX_FFT, array_length, SAMPLING_FREQUENCY, OFFSET_REMOVAL, HANNING_WINDOWING, ZERO_FORCING, SMOOTHING, TARGET_THRESHOLD, BANDWIDTH_THRESHOLD, direction_DEG, tiltAngle_DEG)
            # Plot of FFT
            plot_paper_format(freqAxis_Hz, FFT_dBV, "Frequency (Hz)", "FFT magnitude (dBV)", timestamp, SHOW_FIGURE, SAVE_PLOTS, PDF_PLOT, PNG_PLOT, PLOT_PATH)

            if REALTIME_MEAS == True:
                print('Recap:')
                print('[EP.,\tDEG,\tdBV,\tHz,\tm/s]')
                for direction in antennaBeamDirections_DEG:
                    print('[{:d},'.format(episode+1), end='\t')
                    print('{:.1f},'.format(direction), end='\t')
                    print('{:.1f},'.format(FFT_dBV_peaks[episode, direction]), end='\t')
                    print('{:.1f},'.format(centroid_frequencies[episode, direction]), end='\t')
                    print('{:.1f}]'.format(surface_velocities_table[episode, direction]))
                if STATISTICAL_ANALYSIS == True and episode >= 2:
                    print('Statistical analysis (episode {:d} of {:d}):'.format(episode+1, EPISODES))
                    print('[angle, mean, std.dev., S.W. stat, S.W. p-value]')
                    print('[DEG,\tm/s,\tm/s,\tS.W.,\tp-value]')
                    for direction in antennaBeamDirections_DEG:
                        shapiro_test = stats.shapiro(surface_velocities_table[:episode+1,direction])
                        print('[{:.1f},'.format(direction), end='\t')
                        print('{:.1f},'.format(np.mean(surface_velocities_table[:episode+1,direction])), end='\t')
                        print('{:.1f},'.format(np.std(surface_velocities_table[:episode+1,direction], ddof=1)), end='\t')
                        print('{:.1f},'.format(shapiro_test.statistic), end='\t')
                        print('{:.3f}]'.format(shapiro_test.pvalue))
    
    # Generate report
    print('Generating report...')
    time.sleep(1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reportFileName = timestamp + "_report.txt"
    completeFileName = os.path.join(PLOT_PATH, reportFileName)
    with open(completeFileName,'w') as file:
        if REALTIME_MEAS == True:
            file.write('### SURFACE VELOCITY TABLE ###\n')
            file.write('[EP.,\tDEG,\tdBV,\tHz,\t\tm/s]\n')
            for episode in range(EPISODES):
                for direction in antennaBeamDirections_DEG:
                    file.write('[{:d},\t\t'.format(episode+1))
                    file.write('{:.1f},\t'.format(direction))
                    file.write('{:.1f},\t'.format(FFT_dBV_peaks[episode,direction]))
                    file.write('{:.1f},\t'.format(centroid_frequencies[episode,direction]))
                    file.write('{:.1f}]\n'.format(surface_velocities_table[episode,direction]))
            if STATISTICAL_ANALYSIS == True:
                file.write('### STATISTICAL ANALYSIS (@ episode {:d} of {:d}) ###\n'.format(episode+1, EPISODES))
                file.write('[scanning angle, mean value, std.dev., S.W. test statistic, S.W. test p-value]\n')
                file.write('[DEG,\tm/s,\tm/s,\tS.W.,\tp-value]\n')
                for direction in antennaBeamDirections_DEG:
                    shapiro_test = stats.shapiro(surface_velocities_table[:episode+1,direction])
                    file.write('[{:.1f},\t'.format(direction))
                    file.write('{:.1f},\t'.format(np.mean(surface_velocities_table[:episode+1,direction])))
                    file.write('{:.1f},\t'.format(np.std(surface_velocities_table[:episode+1,direction], ddof=1)))
                    file.write('{:.1f},\t'.format(shapiro_test.statistic))
                    file.write('{:.3f}]\n'.format(shapiro_test.pvalue))
    print('Done.')

if __name__ == "__main__":
    main()