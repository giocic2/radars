# FFT evaluation of complex signal
import numpy as np

def FFT_complex(samplingFrequency, resolution, smoothingWindow, frequencyMin, frequencyMax):
    # FFT bins and resolution
    freqBins_FFT = int(2**np.ceil(np.log2(abs(samplingFrequency/2/resolution))))
    print('FFT resolution: ' + str(samplingFrequency / freqBins_FFT) + ' Hz')
    print('FFT bins: ' + str(freqBins_FFT))
    smoothingBins = int(round(smoothingWindow / (samplingFrequency / freqBins_FFT)))
    print('Size of smoothing window (moving average): ' + str(smoothingBins) + ' bins')
    minBin = int(freqBins_FFT/2 + np.round(frequencyMin / (samplingFrequency/freqBins_FFT)))
    frequencyMin = -samplingFrequency/2 + minBin * samplingFrequency/freqBins_FFT
    print("Minimum frequency of interest: {:.1f} Hz".format(frequencyMin))
    maxBin = int(freqBins_FFT/2 + np.round(frequencyMax / (samplingFrequency/freqBins_FFT)))
    frequencyMax = -samplingFrequency/2 + maxBin * samplingFrequency/freqBins_FFT
    print("Maximum frequency of interest: {:.1f} Hz".format(frequencyMin))