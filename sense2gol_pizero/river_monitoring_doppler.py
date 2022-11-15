#!/usr/bin/python
# River monitoring using Sense2GoL Doppler radar

import glob
import os
import sys
from datetime import datetime
sys.path.insert(1, ".")
import shutil
from scipy import stats
import numpy as np

from custom_modules.plots_readytouse import plot_doppler_centroid, plot_IFI_IFQ, plot_spectrogram
from custom_modules.sense2gol import txt_extract, serialPort_acquisition, load_settings
from custom_modules.servo_motor import define_PWM_pin, rotate_servo_to_angle, shut_down_servo
from custom_modules.signal_processing import FFT

def main():
    SAMPLING_FREQUENCY, lines_to_be_read, ADC_RANGE_BITS, ADC_RANGE_V, COMPLEX_FFT, SMOOTHING, BANDWIDTH_THRESHOLD, HANNING_WINDOWING, ZERO_FORCING, FFT_initialized, freqBins_FFT, smoothingBins, minBin, frequencyMin_fixed, maxBin, frequencyMax_fixed, OFFSET_REMOVAL, SPECTROGRAM_ENABLED, STFT_OVERLAPPING_SAMPLES, STFT_SAMPLES_IN_SEGMENT, STFT_BINS, PWM_PIN, PWM_FREQUENCY, RAW_DATA, SHOW_FIGURE, SAVE_PLOTS, PNG_PLOT, PDF_PLOT, PLOT_PATH, REALTIME_MEAS, TARGET_THRESHOLD, DIRECTIONS, antennaBeamDirections_DEG, tiltAngle_DEG, tiltAngle_DEG_str, STATISTICAL_ANALYSIS, EPISODES = load_settings()

    # Save current *.json settings file for offline analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_filename = "./sense2gol_pizero/output/" + timestamp + ".json"
    shutil.copyfile("./sense2gol_pizero/settings.json",json_filename)
    
    # Array to save FFT peak amplitudes and frequencies
    FFT_dBV_peaks = np.zeros((EPISODES, DIRECTIONS))
    centroid_frequencies = np.zeros((EPISODES, DIRECTIONS))
    surface_velocities_table = np.zeros((EPISODES, DIRECTIONS))

    # Initiate servo motor
    servo_motor = define_PWM_pin(PWM_PIN, PWM_FREQUENCY)

    for episode in range(EPISODES):
        text = "EPISODE {:d} OF {:d}".format(episode+1, EPISODES)
        print(f"{text:-^60}")
        for direction in range(DIRECTIONS):
            text = "Scanning direction " + str(direction+1) + " of " + str(DIRECTIONS)
            print(f"{text:-^60}")
            direction_DEG = antennaBeamDirections_DEG[direction]
            direction_DEG_str = "dir" + str("{0:.1f}".format(direction_DEG)) + "deg"
            rotate_servo_to_angle(servo_motor, direction_DEG)

            # Acquisition from serial port
            completeFileName = serialPort_acquisition(tiltAngle_DEG_str, episode, EPISODES, direction_DEG_str, lines_to_be_read)

            # Extract time-domain signals
            I_array_mV, Q_array_mV, complexSignal_mV, timeAxis_s, IQ_arrays_length = txt_extract(completeFileName, ADC_RANGE_BITS, ADC_RANGE_V, SAMPLING_FREQUENCY)
            
            # Plot of time-domain signals
            plot_IFI_IFQ(timeAxis_s, I_array_mV, Q_array_mV, "time (s)", "voltage (mV)", SHOW_FIGURE, SAVE_PLOTS, PDF_PLOT, PNG_PLOT, PLOT_PATH)
            
            # FFT evaluation
            FFT_dBV_peaks[episode,direction], centroid_frequencies[episode,direction], centroid_start, centroid_stop, centroid_threshold, surface_velocities_table[episode,direction], FFT_dBV, FFT_dBV_smoothed, freqAxis_Hz = FFT(complexSignal_mV, COMPLEX_FFT, IQ_arrays_length, SAMPLING_FREQUENCY, freqBins_FFT, OFFSET_REMOVAL, HANNING_WINDOWING, ZERO_FORCING, minBin, maxBin, SMOOTHING, smoothingBins, TARGET_THRESHOLD, BANDWIDTH_THRESHOLD, frequencyMin_fixed, direction_DEG, tiltAngle_DEG, FFT_initialized)
            # Plot of FFT
            plot_doppler_centroid(freqAxis_Hz, FFT_dBV, FFT_dBV_smoothed, centroid_start, centroid_stop, centroid_threshold, "frequency (Hz)", "FFT magnitude (dBV)", ZERO_FORCING, frequencyMin_fixed, frequencyMax_fixed, SHOW_FIGURE, SAVE_PLOTS, PDF_PLOT, PNG_PLOT, PLOT_PATH)
            if SPECTROGRAM_ENABLED:
                plot_spectrogram(complexSignal_mV, SAMPLING_FREQUENCY, STFT_OVERLAPPING_SAMPLES, STFT_SAMPLES_IN_SEGMENT, STFT_BINS, 'time (s)', 'frequency (Hz)', SHOW_FIGURE, SAVE_PLOTS, PDF_PLOT, PNG_PLOT, PLOT_PATH)

            # Console log of real-time measurements
            if REALTIME_MEAS == True:
                print('Recap:')
                print('[EP.,\tDEG,\tdBV,\tHz,\tm/s]')
                for direction in range(DIRECTIONS):
                    print('[{:d},'.format(episode+1), end='\t')
                    print('{:.1f},'.format(antennaBeamDirections_DEG[direction]), end='\t')
                    print('{:.1f},'.format(FFT_dBV_peaks[episode, direction]), end='\t')
                    print('{:.1f},'.format(centroid_frequencies[episode, direction]), end='\t')
                    print('{:.1f}]'.format(surface_velocities_table[episode, direction]))
                if STATISTICAL_ANALYSIS == True and episode >= 2:
                    print('Statistical analysis (episode {:d} of {:d}):'.format(episode+1, EPISODES))
                    print('[angle, mean, std.dev., S.W. stat, S.W. p-value]')
                    print('[DEG,\tm/s,\tm/s,\tS.W.,\tp-value]')
                    for direction in range(DIRECTIONS):
                        shapiro_test = stats.shapiro(surface_velocities_table[:episode+1,direction])
                        print('[{:.1f},'.format(antennaBeamDirections_DEG[direction]), end='\t')
                        print('{:.3f},'.format(np.mean(surface_velocities_table[:episode+1,direction])), end='\t')
                        print('{:.3f},'.format(np.std(surface_velocities_table[:episode+1,direction], ddof=1)), end='\t')
                        print('{:.3f},'.format(shapiro_test.statistic), end='\t')
                        print('{:.3f}]'.format(shapiro_test.pvalue))
    # Report on *.txt file
    print('Generating report...')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    reportFileName = timestamp + "_report.txt"
    completeFileName = os.path.join(PLOT_PATH, reportFileName)
    with open(completeFileName,'w') as file:
        if REALTIME_MEAS == True:
            file.write('### SURFACE VELOCITY TABLE ###\n')
            file.write('[EP.,\tDEG,\tdBV,\tHz,\tm/s]\n')
            for episode in range(EPISODES):
                for direction in range(DIRECTIONS):
                    file.write('[{:d},\t'.format(episode+1))
                    file.write('{:.1f},\t'.format(antennaBeamDirections_DEG[direction]))
                    file.write('{:.1f},\t'.format(FFT_dBV_peaks[episode,direction]))
                    file.write('{:.1f},\t'.format(centroid_frequencies[episode,direction]))
                    file.write('{:.3f}]\n'.format(surface_velocities_table[episode,direction]))
            if STATISTICAL_ANALYSIS == True:
                file.write('### STATISTICAL ANALYSIS (@ episode {:d} of {:d}) ###\n'.format(episode+1, EPISODES))
                file.write('[scanning angle, mean value, std.dev., S.W. test statistic, S.W. test p-value]\n')
                file.write('[DEG,\tm/s,\tm/s,\tS.W.,\tp-value]\n')
                for direction in range(DIRECTIONS):
                    shapiro_test = stats.shapiro(surface_velocities_table[:episode+1,direction])
                    file.write('[{:.1f},\t'.format(antennaBeamDirections_DEG[direction]))
                    file.write('{:.3f},\t'.format(np.mean(surface_velocities_table[:episode+1,direction])))
                    file.write('{:.3f},\t'.format(np.std(surface_velocities_table[:episode+1,direction], ddof=1)))
                    file.write('{:.3f},\t'.format(shapiro_test.statistic))
                    file.write('{:.3f}]\n'.format(shapiro_test.pvalue))
    print('Done.')
    # End servo motor control
    shut_down_servo(servo_motor)
    # Delete raw data if not needed
    if not RAW_DATA:
        raw_samples_files = glob.glob('sense2gol_pizero/output/*.txt')
        for txtfile in raw_samples_files:
            os.remove(txtfile)

if __name__ == "__main__":
    main()