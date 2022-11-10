import matplotlib.pyplot as plt
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

def plot_signal(x_axis_data, y_axis_data, x_axis_label='X axis data (adim.)', y_axis_label='Y axis data (adim.)', showFigure=False, savePlot=True, pdf_plot=True, png_plot=True, plotPath=None):
    # Output File Paths for Plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if plotPath == None: # e.g. when standalone script
        plotPathPNG = timestamp + '.png'
        plotPathPDF = timestamp + '.pdf'
    else:
        plotPathPNG = plotPath + timestamp + '.png'
        plotPathPDF = plotPath + timestamp + '.pdf'

    # Plot Configuration
    plt.rcParams['font.family'] = FONT_CHOICE
    plt.rcParams['axes.linewidth'] = LINE_WIDTH
    plt.rcParams["figure.figsize"] = (FIG_SIZE_X_INCHES, FIG_SIZE_Y_INCHES)

    plt.plot(x_axis_data, y_axis_data)
    plt.ylabel(y_axis_label)
    plt.xlabel(x_axis_label)
    plt.grid(True)
    plt.tight_layout()

    if savePlot and png_plot:
        plt.savefig(plotPathPNG)
    if savePlot and pdf_plot:
        plt.savefig(plotPathPDF)
    if showFigure:
        plt.show()
    # Clear figure
    plt.clf()

def plot_IFI_IFQ(ifi_x_axis_data, ifi_y_axis_data, ifq_x_axis_data, ifq_y_axis_data, x_axis_label='X axis data (adim.)', y_axis_label='Y axis data (adim.)', showFigure=False, savePlot=True, pdf_plot=True, png_plot=True, plotPath=None):
    # Output File Paths for Plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if plotPath == None: # e.g. when standalone script
        plotPathPNG = timestamp + '.png'
        plotPathPDF = timestamp + '.pdf'
    else:
        plotPathPNG = plotPath + timestamp + '.png'
        plotPathPDF = plotPath + timestamp + '.pdf'

    # Plot Configuration
    plt.rcParams['font.family'] = FONT_CHOICE
    plt.rcParams['axes.linewidth'] = LINE_WIDTH
    plt.rcParams["figure.figsize"] = (FIG_SIZE_X_INCHES, FIG_SIZE_Y_INCHES)

    plt.plot(ifi_x_axis_data, ifi_y_axis_data)
    plt.plot(ifq_x_axis_data, ifi_y_axis_data)
    plt.ylabel(y_axis_label)
    plt.xlabel(x_axis_label)
    plt.grid(True)
    plt.tight_layout()

    if savePlot and png_plot:
        plt.savefig(plotPathPNG)
    if savePlot and pdf_plot:
        plt.savefig(plotPathPDF)
    if showFigure:
        plt.show()
    # Clear figure
    plt.clf()

def plot_doppler_centroid(FFT_x_axis_data, FFT_y_axis_data, FFT_smoothed_y_axis_data, centroid_start, centroid_stop, centroid_threshold, x_axis_label='X axis data (adim.)', y_axis_label='Y axis data (adim.)', zeroForcing=False, frequency_min=-1000, frequency_max=1000, showFigure=False, savePlot=True, pdf_plot=True, png_plot=True, plotPath=None):
    # Output File Paths for Plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if plotPath == None: # e.g. when standalone script
        plotPathPNG = timestamp + '.png'
        plotPathPDF = timestamp + '.pdf'
    else:
        plotPathPNG = plotPath + timestamp + '.png'
        plotPathPDF = plotPath + timestamp + '.pdf'

    # Plot Configuration
    plt.rcParams['font.family'] = FONT_CHOICE
    plt.rcParams['axes.linewidth'] = LINE_WIDTH
    plt.rcParams["figure.figsize"] = (FIG_SIZE_X_INCHES, FIG_SIZE_Y_INCHES)

    plt.plot(FFT_x_axis_data, FFT_y_axis_data)
    plt.plot(FFT_x_axis_data, FFT_smoothed_y_axis_data)
    plt.ylabel(y_axis_label)
    plt.xlabel(x_axis_label)
    if zeroForcing == True:
        plt.xlim(frequency_min, frequency_max)
    plt.axhline(y=centroid_threshold, color='r', linestyle='-')
    plt.axvline(x=centroid_start, color='k', linestyle=':')
    plt.axvline(x=centroid_stop, color='k', linestyle=':')
    plt.grid(True)
    plt.legend(['initial', 'smoothed'])
    plt.tight_layout()

    if savePlot and png_plot:
        plt.savefig(plotPathPNG)
    if savePlot and pdf_plot:
        plt.savefig(plotPathPDF)
    if showFigure:
        plt.show()
    # Clear figure
    plt.clf()

if __name__ == "__main__":
    print("Standalone script not yet delevoped.")