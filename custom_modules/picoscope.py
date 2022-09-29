from math import log
import string

def conform_sampling_frequency(samplingFrequency: float):
    if samplingFrequency >= 125e6:
        timebase = round(log(500e6/samplingFrequency,2))
        samplingFrequency = 1/(2**timebase/5)*1e8
    else:
        timebase=round(62.5e6/samplingFrequency+2)
        samplingFrequency = 62.5e6/(timebase-2)
    return samplingFrequency

def get_channel_range_id(channelRange: str):
    if channelRange == '20e-3':
        channel_range_id = 1
    elif channelRange == '50e-3':
        channel_range_id = 2
    elif channelRange == '100e-3':
        channel_range_id = 3
    elif channelRange == '200e-3':
        channel_range_id = 4
    elif channelRange == '500e-3':
        channel_range_id = 5
    elif channelRange == '1':
        channel_range_id = 6
    elif channelRange == '2':
        channel_range_id = 7
    elif channelRange == '5':
        channel_range_id = 8
    elif channelRange == '10':
        channel_range_id = 9
    elif channelRange == '20':
        channel_range_id = 10
    else:
        raise ValueError("The channel range specified in settings.json is not valid.")
    return channel_range_id    

if __name__ == "__main__":
    print("Standalone script not yet delevoped.")