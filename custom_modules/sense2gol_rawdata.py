import numpy as np
import itertools
import re
import os

def txt_extract(file_name):
    # Extract raw samples from txt file
    text_file = open(file_name, 'rb')
    temp_line = text_file.readline()
    done = False
    I_samples = []
    Q_samples = []
    # Locate I samples
    temp_line = text_file.readline()
    temp_line = temp_line.decode('ascii')
    while temp_line != '  ------------- I raw samples ------------- \n':
        temp_line = text_file.readline()
        temp_line = temp_line.decode('ascii')

    while not done:
        if temp_line == '  ------------- I raw samples ------------- \n':
            temp_line = text_file.readline()
            temp_line = temp_line.decode('ascii')
            while temp_line != '  ------------- Q raw samples ------------- \n':
                temp_line_int = list(map(int, re.findall(r'\d+', temp_line)))
                if temp_line_int != '\r\n':
                    I_samples = list(itertools.chain(I_samples, temp_line_int))
                temp_line = text_file.readline()
                temp_line = temp_line.decode('ascii')
                if temp_line == '':
                    done = True
                    break
            if temp_line == '  ------------- Q raw samples ------------- \n':
                temp_line = text_file.readline()
                temp_line = temp_line.decode('ascii')
        temp_line_int = list(map(int, re.findall(r'\d+', temp_line)))
        if temp_line_int != '\r\n' and temp_line != '':
            Q_samples = list(itertools.chain(Q_samples, temp_line_int))
        temp_line = text_file.readline()
        temp_line = temp_line.decode('ascii')
        if temp_line == '':
            done = True
    print("Raw data extracted from .txt file.")
    print("Number of IFI samples: ", len(I_samples))
    print("Number of IFQ samples: ", len(Q_samples))

    array_length = min(len(I_samples), len(Q_samples))
    print("Processed signals length: ", array_length)

    # Seems that Q and I needs to be inverted
    Q_array = np.array(I_samples[0:array_length])
    I_array = np.array(Q_samples[0:array_length])

    return I_array, Q_array, array_length

def txt_generate(serialDevice, lines_to_be_read, timestamp):
    samplesFileName = timestamp + ".txt"
    completeFileName = os.path.join('sense2gol_pizero/raw-samples',samplesFileName)
    # open text file to store the current
    text_file = open(completeFileName, 'wb')
    # read serial data and write it to the text file
    index = 0
    print("Acquisition started...")
    while index <= lines_to_be_read:
        if serialDevice.inWaiting():
            x=serialDevice.readline()
            text_file.write(x)
            if x=="\n":
                text_file.seek(0)
                text_file.truncate()
            text_file.flush()
        index += 1
    print("Raw data acquisition completed.")
    # close the serial connection and text file
    text_file.close()
    return completeFileName

if __name__ == "__main__":
    print("Standalone script not yet developed.")