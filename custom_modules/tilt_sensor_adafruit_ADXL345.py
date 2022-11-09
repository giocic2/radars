import busio
import board
import adafruit_adxl34x
import time
from struct import unpack
import numpy as np

def setup_ADX345():
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100e3)
    accelerometer = adafruit_adxl34x.ADXL345(i2c)
    accelerometer.range = adafruit_adxl34x.Range.RANGE_16_G # Range

    # Offset compensation
    OFSX = 0x00 # X-axis offset in LSBs
    OFSY = 0x00 # Y-axis offset in LSBs
    OFSZ = 0x00 # Z-axis offset in LSBs
    accelerometer._write_register_byte(adafruit_adxl34x._REG_OFSX, OFSX)
    accelerometer._write_register_byte(adafruit_adxl34x._REG_OFSY, OFSY) 
    accelerometer._write_register_byte(adafruit_adxl34x._REG_OFSZ, OFSZ)

    # Data rate and power mode control
    # bit5: low power (disabled)
    # bit4-1: output data rate (100 Hz)
    accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001010)

    # Power-saving feature control
    # bit6: link (disabled)
    # bit5: auto sleep (disabled)
    # bit4: measure (disabled --> enabled)
    # bit3: sleep (disabled)
    # bit2-1: wakeup bits (8 Hz) 
    accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000000)
    accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001000)

    # Data format control
    # bit8: self test (disabled)
    # bit7: SPI mode (4 wire)
    # bit6: interrupt active level (active high)
    # bit4: full resolution bit (enabled)
    # bit3: justify (right)
    # bit2-1: range (16g)
    accelerometer._write_register_byte(adafruit_adxl34x._REG_DATA_FORMAT, 0b00001011)

    # FIFO control
    # bit8-7: FIFO mode (stream)
    # bit6: trigger (INT1, but unuseful)
    # bit5-1: samples needed to trigger watermark interrupt (immediately)
    accelerometer._write_register_byte(adafruit_adxl34x._REG_FIFO_CTL, 0b10000000)

    return accelerometer

def calibration(accelerometer, iterations):
    x_avg = 0
    y_avg = 0
    z_avg = 0
    x_min = 4096
    y_min = 4096
    z_min = 4096
    x_max = -4096
    y_max = -4096
    z_max = -4096
    time.sleep(0.1)

    while True:
        for index in range(iterations):
            DATA_XYZ = accelerometer._read_register(adafruit_adxl34x._REG_DATAX0, 6)
            x, y, z = unpack("<hhh",DATA_XYZ)
            print(x, y, z)
            time.sleep(0.1)
            x_avg = x_avg + x/iterations
            y_avg = y_avg + y/iterations
            z_avg = z_avg + z/iterations
        x_avg = round(x_avg)
        y_avg = round(y_avg)
        z_avg = round(z_avg)
        print("Average values: ", x_avg, y_avg, z_avg)
        if x_avg < x_min:
            x_min = x_avg
        if x_avg > x_max:
            x_max = x_avg
        if y_avg < y_min:
            y_min = y_avg
        if y_avg > y_max:
            y_max = y_avg
        if z_avg < z_min:
            z_min = z_avg
        if z_avg > z_max:
            z_max = z_avg
        delta_x = x_max - x_min
        delta_y = y_max - y_min
        delta_z = z_max - z_min
        print("Minimum values (LSB): ", x_min, y_min, z_min)
        print("Maximum values (LSB): ", x_max, y_max, z_max)
        print("Excursion (LSB): ", delta_x, delta_y, delta_z)
        if delta_x > 524 or delta_y > 524 or delta_z > 524 or delta_x < 500 or delta_y < 500 or delta_z < 500:
            print("WARNING: your sensors seems to be out of range! (by 12 LSBs at least...)")
            print("Excursion should be 512 LSB (+-1g).")
        step=input("Press \'Enter\' to repeat, \'q'\ to quit calibration.")
        x_avg = 0
        y_avg = 0
        z_avg = 0
        accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000000)
        accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001000)
        if step == 'q':
            break
        
    return x_min, x_max, y_min, y_max, z_min, z_max

def tilt_angle(accelerometer, x_min, x_max, y_min, y_max, z_min, z_max, accel_averages, repeatMeasurement):
    # Offset expressed in LSB.
    # We use this instead of OFS_ registers for finer tuning.
    # These numbers depends on calibration results for a specific sensor.
    x_offset = round((x_min + x_max) / 2)
    y_offset = round((y_min + y_max) / 2)
    z_offset = round((z_min + z_max) / 2)

    # Calibrated full-scale factor, for rescaling.
    # We assume that LSB:g relation is linear after rescaling.
    # These numbers depends on calibration.py results for a specific sensor.
    x_cfs = np.ceil((x_max - x_min) / 2)
    y_cfs = np.ceil((y_max - y_min) / 2)
    z_cfs = np.ceil((z_max - z_min) / 2)

    x_g_avg = 0
    y_g_avg = 0
    z_g_avg = 0
    tiltAngle_1st_avg = 0
    tiltAngle_2nd_avg = 0
    tiltAngle_evaluated = False

    while not tiltAngle_evaluated:
        for measurement in range(accel_averages):
            DATA_XYZ = accelerometer._read_register(adafruit_adxl34x._REG_DATAX0, 6)
            time.sleep(0.1)
            x, y, z = unpack("<hhh",DATA_XYZ)
            x_g = x - x_offset
            y_g = y - y_offset
            z_g = z - z_offset
            x_g_avg = x_g_avg + x_g/accel_averages
            y_g_avg = y_g_avg + y_g/accel_averages
            z_g_avg = z_g_avg + z_g/accel_averages
            # Two formulas to evaluate the same tilt angle
            tiltAngle_1st = np.arcsin(- z_g / z_cfs)
            tiltAngle_2nd = np.arccos(+ y_g / y_cfs)
            tiltAngle_1st_avg = tiltAngle_1st_avg + tiltAngle_1st/accel_averages
            tiltAngle_2nd_avg = tiltAngle_2nd_avg + tiltAngle_2nd/accel_averages
        tiltAngle_avg = (tiltAngle_1st_avg + tiltAngle_2nd_avg) / 2
        print("Tilt angle [deg]: {0:.1f}".format(np.rad2deg(tiltAngle_avg)))
        if round(x_g_avg) != 0:
            print("WARNING: gravity along X-axis should be 0! Please align the sensor horizontally.")
            print("x: ", round(x_g_avg))
        accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000000)
        accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00001000)
        if repeatMeasurement:
            whatNext = input("Repeat tilt angle measurement? [y/n]: ")
            continueTakingUserInput = True
            while continueTakingUserInput == True:
                if whatNext == 'y':
                    continueTakingUserInput = False
                elif whatNext == 'n':
                    repeatMeasurement = False
                    continueTakingUserInput = False
                else:
                    print("Please type correctly [y/n].")
                    continueTakingUserInput = True
            time.sleep(0.5)
            x_g_avg = 0
            y_g_avg = 0
            z_g_avg = 0
            tiltAngle_1st_avg = 0
            tiltAngle_2nd_avg = 0
        else:
            tiltAngle_evaluated = True
    tiltAngle_DEG = np.rad2deg(tiltAngle_avg)
    return tiltAngle_DEG

def sleep_mode(accelerometer):
    # Accelerometer in sleep mode
    accelerometer._write_register_byte(adafruit_adxl34x._REG_BW_RATE, 0b00000100)

if __name__ == "__main__":
    print("Standalone script not yet delevoped.")