import matplotlib.pyplot as plt
import numpy as np

def evaluate_antenna_footprint(HEIGHT_FROM_WATER_LEVEL, antennaBeamWidth_elevation_deg, antennaBeamWidth_azimuth_deg, tiltAngle_deg, horintal_direction_deg):
    antenna_footprint_vertical = np.abs(HEIGHT_FROM_WATER_LEVEL * (1/np.tan(np.deg2rad(tiltAngle_deg)) - 1/np.tan(np.deg2rad(tiltAngle_deg-antennaBeamWidth_elevation_deg/2))))
    antenna_footprint_horizontal = np.abs(HEIGHT_FROM_WATER_LEVEL * (1/np.tan(np.deg2rad(tiltAngle_deg)) - 1/np.tan(np.deg2rad(tiltAngle_deg-antennaBeamWidth_azimuth_deg/2))))