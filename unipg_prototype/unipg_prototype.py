import json
from datetime import datetime
import shutil
import custom_modules.picoscope as picoscope
from custom_modules.signal_processing import *

def main():

    # Load settings from *.json file.
    with open('unipg_prototype/settings.json') as f:
        settings = json.load(f)
    f.close()

    # Save current *.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_filename = "./unipg_prototype/raw_samples/" + timestamp + ".json"
    shutil.copyfile("./unipg_prototype/settings.json", json_filename)

    # Mounting support and antennas settings
    PIVOT_HEIGHT = settings["mounting-support"]["pivot-height-m"] # m. Height of the pivot of the tiltable plane.
    WATER_VERTICAL_DISTANCE = settings["mounting-support"]["water-vertical-distance-m"] # m. Vertical distance from water level and radar mounting support.
    RX_ANTENNA_OFFSET = settings["mounting-support"]["rx-antenna-offset-m"] # m. Distance between RX antenna and pivot.
    MIN_SCAN_ANGLE = settings["mounting-support"]["min-scan-angle-deg"] # Degrees. Minimum horizontal beam angle, where 0° is the broadside direction.
    MAX_SCAN_ANGLE = settings["mounting-support"]["max-scan-angle-deg"] # Degrees. Maximum horizontal beam angle, where 0° is the broadside direction.

    # PicoScope 2206B settings
    ACQUISITION_TIME = float(settings["picoscope"]["acquisition-time-s"]) # s
    SAMPLING_FREQUENCY = float(settings["picoscope"]["sampling-frequency-Hz"]) # Hz
    SAMPLING_FREQUENCY = picoscope.conform_sampling_frequency(SAMPLING_FREQUENCY)
    print('Sampling frequency: {:,}'.format(SAMPLING_FREQUENCY) + ' Hz')
    time_resolution = 1/SAMPLING_FREQUENCY # s
    print('Time resolution: {:,}'.format(time_resolution) + ' s')
    totalSamples = round(ACQUISITION_TIME/time_resolution)
    print('Number of total samples (for each channel): {:,}'.format(totalSamples))
    CH_A_RANGE_V = settings["picoscope"]["channel-a-range-v"] # Volts.
    CH_B_RANGE_V = settings["picoscope"]["channel-b-range-v"] # Volts.

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

if __name__ == "__main__":
    main()