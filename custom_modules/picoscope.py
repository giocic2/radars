from math import log

def conform_sampling_frequency(samplingFrequency: float):
    if samplingFrequency >= 125e6:
        timebase = round(log(500e6/samplingFrequency,2))
        samplingFrequency = 1/(2**timebase/5)*1e8
    else:
        timebase=round(62.5e6/samplingFrequency+2)
        samplingFrequency = 62.5e6/(timebase-2)
    return samplingFrequency

if __name__ == "__main__":
    print("Standalone script not yet delevoped.")