# FFT evaluation of complex signal
import numpy as np

def FFT_parameters(complexFFT: bool, samplingFrequency: float, resolution: float, smoothing: bool, smoothingWindow: float, frequencyMin: float, frequencyMax: float, print_FFT_info=True):
    '''
    Define FFT bins and resolution.
    :return: Boolean flag (True) after FFT parameters are defined.
    '''
    global freqBins_FFT, smoothingBins, minBin, frequencyMin_fixed, maxBin, frequencyMax_fixed
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
        print('FFT resolution: ' + str(samplingFrequency / freqBins_FFT) + ' Hz')
        print('FFT bins: ' + str(freqBins_FFT))
        if smoothing == True:
            print('Size of smoothing window (moving average): ' + str(smoothingBins) + ' bins')
        print("Minimum frequency of interest: {:.1f} Hz".format(frequencyMin_fixed))
        print("Maximum frequency of interest: {:.1f} Hz".format(frequencyMin_fixed))
    return True  

def centroid_estimation(inputArray, bandwidthThreshold, freqAxis_Hz, frequencyMin):
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
    centroid_frequencies[episodeNumber, directionIndex] = (stopBand + startBand)/2
    surface_velocities_table[episodeNumber, directionIndex] = (3e8 * (stopBand + startBand)/2) / (2 * (VCOfreq * 1e6) * np.cos(np.deg2rad(directions_DEG[directionIndex]) * np.cos(tiltAngle_avg)))
    print('Amplitude of FFT peak: {:.1f}'.format(np.amax(FFT_dBV)) + ' dBV')
    print('Amplitude of FFT peak (norm.smooth.): {:.1f}'.format(FFT_norm_dB_smooth_max) + ' dB')
    print('Bandwidth threshold (norm.smooth.): {:.1f}'.format(FFT_norm_dB_smooth_max - BANDWIDTH_THRESHOLD) + ' dB')
    print('Bandwidth: {:.1f}'.format(stopBand - startBand) + ' Hz')
    print('Bandwidth starts at {:.1f}'.format(startBand) + ' Hz')
    print('Bandwidth stops at {:.1f}'.format(stopBand) + ' Hz')
    print('Center of Doppler centroid: {:.1f}'.format((stopBand + startBand)/2) + ' Hz')
    print('Resulting surface velocity: {:.1f}'.format((3e8 * (stopBand + startBand)/2) / (2 * (VCOfreq * 1e6) * np.cos(np.deg2rad(directions_DEG[directionIndex]) * np.cos(tiltAngle_avg)))), ' m/s')


def FFT(signal_mV, complexFFT: bool, totalSamples: int, samplingFrequency: float, offsetRemoval: bool, hanningWindowing: bool, zeroForcing: bool, smoothing: bool, targetThreshold: float, bandwidthThreshold: float):
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
        FFT_max = np.amax(FFT_mV)
        FFT_dBV = 20*np.log10(FFT_mV/1000)
        freqAxis = np.fft.fftshift(np.fft.fftfreq(freqBins_FFT)) # freqBins+1
        freqAxis_Hz = freqAxis * samplingFrequency
        # FFT normalization
        FFT_norm = FFT_mV / FFT_max
        FFT_norm_max = np.amax(FFT_norm)
        if smoothing == True:
            FFT_norm = np.convolve(FFT_norm, np.ones(smoothingBins), 'same') / smoothingBins
            shift_of_FFT_max = FFT_norm_max - np.amax(FFT_norm)
            print("After smoothing, the FTT peak is shifted by {:.1f} dB".format(20*np.log10(shift_of_FFT_max)))
        FFT_norm_dB = 20*np.log10(FFT_norm)
        FFT_norm_dB_max = np.amax(FFT_norm_dB)
        peakFreq = freqAxis_Hz[FFT_norm_dB.argmax()] # If two identical maxima, only the first occurrence is shown (negative frequency)
    else: # FFT of real signal
        print("real FFT to be completed")
    
    if (np.amax(FFT_norm_dB) < targetThreshold):
        print('WARNING: Target not detected.')
    elif (FFT_norm_dB[minBin] >= np.amax(FFT_norm_dB) - bandwidthThreshold):
        print('WARNING: The zero-forcing window is too narrow.')
    else:
        # Doppler centroid
        centroid_estimation(FFT_norm_dB, bandwidthThreshold, freqAxis_Hz, frequencyMin_fixed)


if __name__ == "__main__":
    print("Standalone script not yet developed.")