# FFT evaluation of complex signal
import numpy as np

def FFT_parameters(complexFFT: bool, samplingFrequency: float, resolution: float, smoothing: bool, smoothingWindow: float, frequencyMin: float, frequencyMax: float, print_FFT_info=True):
    '''
    Define FFT bins and resolution.
    :return: Boolean flag (True) after FFT parameters are defined.
    '''
    freqBins_FFT = int(2**np.ceil(np.log2(abs(samplingFrequency/2/resolution))))
    smoothingBins = int(round(smoothingWindow / (samplingFrequency / freqBins_FFT)))
    if complexFFT==True:
        minBin = int(freqBins_FFT/2 + np.round(frequencyMin / (samplingFrequency/freqBins_FFT)))
        frequencyMin_fixed = -samplingFrequency/2 + minBin * samplingFrequency/freqBins_FFT
        maxBin = int(freqBins_FFT/2 + np.round(frequencyMax / (samplingFrequency/freqBins_FFT)))
        frequencyMax_fixed = -samplingFrequency/2 + maxBin * samplingFrequency/freqBins_FFT
    else:
        minBin = int(np.round(FREQUENCY_MIN / (samplingFrequency/freqBins_FFT)))
        FREQUENCY_MIN = minBin * samplingFrequency/freqBins_FFT
        print("Minimum frequency of interest: {:.1f} Hz".format(FREQUENCY_MIN))
        maxBin = int(np.round(FREQUENCY_MAX / (samplingFrequency/freqBins_FFT)))
        FREQUENCY_MAX = maxBin * samplingFrequency/freqBins_FFT
    if print_FFT_info==True:
        print('FFT resolution: {:.3e} Hz'.format(samplingFrequency / freqBins_FFT))
        print('FFT bins: {:,d}'.format(freqBins_FFT))
        if smoothing == True:
            print('Size of smoothing window (moving average): {:,d} bins, {:.1f} Hz'.format(smoothingBins, smoothingWindow))
        print("Minimum frequency of interest: {:.1f} Hz".format(frequencyMin_fixed))
        print("Maximum frequency of interest: {:.1f} Hz".format(frequencyMax_fixed))
    return True, freqBins_FFT, smoothingBins, minBin, maxBin

def centroid_estimation(inputArray, bandwidthThreshold, freqAxis_Hz, frequencyMin, FFT_dBV_max, freqBins_FFT):
    maxValue = np.amax(inputArray)
    freqIndex = 0
    stopIndex = 0
    start_detected = False
    startBand = 0
    stopBand = 0
    centroidDetected = False
    while centroidDetected == False:
        for element in inputArray:
            if element >= (maxValue - bandwidthThreshold):
                if start_detected == False:
                    startBand = max(freqAxis_Hz[freqIndex], frequencyMin)
                    start_detected = True
                stopIndex = max(stopIndex,freqIndex)
                stopBand = freqAxis_Hz[stopIndex]
            freqIndex += 1
            if freqIndex >= (freqBins_FFT+1):
                centroidDetected = True
                break
    centroid_frequency = (stopBand + startBand)/2
    print('Amplitude of FFT peak: {:.1f}'.format(FFT_dBV_max) + ' dBV')
    centroid_threshold = FFT_dBV_max - bandwidthThreshold
    print('Bandwidth threshold (norm.smooth.): {:.1f}'.format(centroid_threshold) + ' dB')
    print('Bandwidth: {:.1f}'.format(stopBand - startBand) + ' Hz')
    print('Bandwidth starts at {:.1f}'.format(startBand) + ' Hz')
    print('Bandwidth stops at {:.1f}'.format(stopBand) + ' Hz')
    print('Center frequency of Doppler centroid: {:.1f}'.format(centroid_frequency) + ' Hz')
    return centroid_frequency, startBand, stopBand, centroid_threshold

def evaluate_surface_velocity(centroid_frequency, antennaBeamDirection_DEG, tiltAngle_DEG):
    surface_velocity = (3e8 * centroid_frequency) / (2 * (24.125e9) * np.cos(np.deg2rad(antennaBeamDirection_DEG) * np.cos(np.deg2rad(tiltAngle_DEG))))
    print('Resulting surface velocity: {:.3f}'.format((3e8 * centroid_frequency) / (2 * (24.125e9) * np.cos(np.deg2rad(antennaBeamDirection_DEG) * np.cos(tiltAngle_DEG)))), ' m/s')
    return surface_velocity

def FFT(signal_mV, complexFFT: bool, totalSamples: int, samplingFrequency: float, freqBins_FFT, offsetRemoval: bool, hanningWindowing: bool, zeroForcing: bool, minBin, maxBin, smoothing: bool, smoothingBins, targetThreshold: float, bandwidthThreshold: float, frequencyMin_fixed, antennaBeamDirection_DEG: float, tiltAngle_DEG: float):
    if complexFFT == True: # FFT of complex signal
        if offsetRemoval==True:
            signal_mV = signal_mV - np.mean(signal_mV)
        if hanningWindowing==True:
            signal_mV = signal_mV * np.hamming(totalSamples)
        FFT = np.fft.fftshift(np.fft.fft(signal_mV, n = freqBins_FFT)) # FFT of complex signal
        FFT_mV = np.abs(1/(totalSamples)*FFT) # FFT magnitude
        if zeroForcing == True:
            FFT_mV[0:minBin] = 0
            FFT_mV[maxBin:-1] = 0
        FFT_dBV = 20*np.log10(FFT_mV/1000)
        FFT_dBV_max = np.amax(FFT_dBV)
        if smoothing == True:
            FFT_dBV_smoothed = np.convolve(FFT_dBV, np.ones(smoothingBins), 'same') / smoothingBins
            FFT_dBV_max_previous = FFT_dBV_max
            FFT_dBV_max = np.amax(FFT_dBV_smoothed)
            shift_of_FFT_max = FFT_dBV_max_previous - FFT_dBV_max # dB
            print("After smoothing, the FTT peak is shifted by {:.1f} dB".format(shift_of_FFT_max))
        freqAxis = np.fft.fftshift(np.fft.fftfreq(freqBins_FFT)) # freqBins+1
        freqAxis_Hz = freqAxis * samplingFrequency
        peakFreq = freqAxis_Hz[FFT_dBV.argmax()] # If two identical maxima, only the first occurrence is shown (negative frequency)
    else: # FFT of real signal
        print("real FFT to be completed")
    
    if (FFT_dBV_max < targetThreshold):
        print('WARNING: Target not detected.')
        centroid_frequency = 0 # Hz
    elif (FFT_dBV_smoothed[minBin] >= FFT_dBV_max - bandwidthThreshold):
        print('WARNING: The zero-forcing window is too narrow.')
        raise ValueError
    else:
        # Doppler centroid
        centroid_frequency, centroid_start, centroid_stop, centroid_threshold = centroid_estimation(FFT_dBV_smoothed, bandwidthThreshold, freqAxis_Hz, frequencyMin_fixed, FFT_dBV_max)
    surface_velocity = evaluate_surface_velocity(centroid_frequency, antennaBeamDirection_DEG, tiltAngle_DEG)
    return FFT_dBV_max, centroid_frequency, centroid_start, centroid_stop, centroid_threshold, surface_velocity, FFT_dBV, FFT_dBV_smoothed, freqAxis_Hz

if __name__ == "__main__":
    print("Standalone script not yet developed.")