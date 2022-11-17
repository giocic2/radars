import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Figure Width (inches)
FIG_SIZE_X_INCHES = 3.5
FIG_SIZE_Y_INCHES = 3
# Font size in Figures
FONT_SIZE = 8
# Line width in Figures (pt)
LINE_WIDTH = 0.5
# Choice of Font ("Arial" / "Times New Roman" / "CMU Serif")
FONT_CHOICE = "Times New Roman"

def evaluate_antenna_footprint(HEIGHT_FROM_WATER_LEVEL: float, antennaBeamWidth_elevation_deg: float, antennaBeamWidth_azimuth_deg: float, tiltAngle_deg: float, horizontal_directions_deg: np.array, SHOW_FIGURE: bool = False, SAVE_PLOT: bool = False, PDF_PLOT: bool = False, PNG_PLOT: bool = False, PLOT_PATH = None):

    # Output File Paths for Plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if PLOT_PATH == None: # e.g. when standalone script
        plotPathPNG = timestamp + '.png'
        plotPathPDF = timestamp + '.pdf'
    else:
        plotPathPNG = PLOT_PATH + timestamp + '.png'
        plotPathPDF = PLOT_PATH + timestamp + '.pdf'

    # Plot Configuration
    plt.rcParams['font.family'] = FONT_CHOICE
    plt.rcParams['axes.linewidth'] = LINE_WIDTH
    plt.rcParams["figure.figsize"] = (FIG_SIZE_X_INCHES, FIG_SIZE_Y_INCHES)

    grid_parameters = np.zeros((horizontal_directions_deg.size, 8))
    # For each "horizontal direction" the following parameters are evaluated:
    # 0: radar-to-target distance beeline
    # 1: projection of radar-to-target distance beeline on ground level
    # 2: swath range
    # 3: antenna footprint center
    # 4,5,6,7: antenna footprint semiaxis (upper, lower, right, left)
    grid_parameters[:, 0] = radarTargetDistance_projection = HEIGHT_FROM_WATER_LEVEL / np.sin(np.deg2rad(tiltAngle_deg))
    grid_parameters[:, 1] = HEIGHT_FROM_WATER_LEVEL / np.tan(np.deg2rad(tiltAngle_deg))
    maxScanAngle = horizontal_directions_deg[-1]
    grid_parameters[:, 2] = radarTargetDistance_projection * np.tan(maxScanAngle) * 2
    print(f"Tilt Angle: {tiltAngle_deg:.1f} degree")
    print(f"Radar-to-target distance: {radarTargetDistance_projection:.1f} m")
    print(f"Radar-to-target distance (projection): {grid_parameters[0, 1]:.1f} m")
    print(f"Swath range: {grid_parameters[0, 2]:.1f} m")
    for index, direction in enumerate(horizontal_directions_deg):
        print("\tDirection: " + str(direction) + " degree")
        grid_parameters[index, 3] = radarTargetDistance_projection * np.tan(np.deg2rad(direction))
        grid_parameters[index, 4] = np.abs(HEIGHT_FROM_WATER_LEVEL * (1/np.tan(np.deg2rad(tiltAngle_deg)) - 1/np.tan(np.deg2rad(tiltAngle_deg-antennaBeamWidth_elevation_deg/2))))
        print("\t\tAntenna footprint, upper semiaxis: {:.2f} m".format(grid_parameters[index,4]))
        grid_parameters[index, 5] = np.abs(HEIGHT_FROM_WATER_LEVEL * (1/np.tan(np.deg2rad(tiltAngle_deg)) - 1/np.tan(np.deg2rad(tiltAngle_deg+antennaBeamWidth_elevation_deg/2))))
        print("\t\tAntenna footprint, lower semiaxis: {:.2f} m".format(grid_parameters[index,5]))
        grid_parameters[index, 6] = np.abs(radarTargetDistance_projection * np.tan(np.deg2rad(direction)) - radarTargetDistance_projection * np.tan(np.deg2rad(direction+antennaBeamWidth_azimuth_deg/2)))
        print("\t\tAntenna footprint, right semiaxis: " + str(grid_parameters[index,6]) + " m")
        grid_parameters[index, 7] = np.abs(radarTargetDistance_projection * np.tan(np.deg2rad(direction)) - radarTargetDistance_projection * np.tan(np.deg2rad(direction-antennaBeamWidth_azimuth_deg/2)))
        print("\t\tAntenna footprint, left semiaxis: " + str(grid_parameters[index,7]) + " m")
        plt.errorbar(grid_parameters[index,3], grid_parameters[index,1], xerr=[[grid_parameters[index,7]], [grid_parameters[index,6]]], yerr=[[grid_parameters[index,5]],[grid_parameters[index,4]]], fmt="o", color='r', markersize=7, capsize=10)
    plt.axis('equal')
    plt.grid(visible=True, which="both", linewidth=0.3)
    plt.tight_layout()
    if SAVE_PLOT and PNG_PLOT:
        plt.savefig(plotPathPNG)
    if SAVE_PLOT and PDF_PLOT:
        plt.savefig(plotPathPDF)
    if SHOW_FIGURE:
        plt.show()
    # Clear figure
    plt.clf()

if __name__ == "__main__":
    HEIGHT_FROM_WATER_LEVEL = float(input("Enter height from water level (m): "))
    tiltAngle_deg = float(input("Enter tilt angle (degree): "))
    antennaBeamWidth_elevation_deg = float(input("Enter antenna beam width in elevation (degree): "))
    antennaBeamWidth_azimuth_deg = float(input("Enter antenna beam width in azimuth (degree): "))
    min_direction = float(input("Enter minimum angle for horizontal direction (degree): "))
    max_direction = float(input("Enter maximum angle for horizontal direction (degree): "))
    number_of_directions = int(input("Enter number of directions: "))
    horizontal_directions_deg = np.linspace(start=min_direction, stop=max_direction, num=number_of_directions, endpoint=True)
    evaluate_antenna_footprint(HEIGHT_FROM_WATER_LEVEL, antennaBeamWidth_elevation_deg, antennaBeamWidth_azimuth_deg, tiltAngle_deg, horizontal_directions_deg, SHOW_FIGURE = True, SAVE_PLOT = False, PDF_PLOT = False, PNG_PLOT = False, PLOT_PATH = None)