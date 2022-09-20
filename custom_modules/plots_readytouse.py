import matplotlib.pyplot as plt
from datetime import datetime

def plot_paper_format(x_axis_data, y_axis_data, timestamp=None, showFigure=False, savePlot=True, pdf_plot=True, png_plot=True, plotPath=None):
    # Figure Width (inches)
    figSizeXinches = 7
    figSizeYinches = 3
    # Font size in Figures
    fontSize = 8
    # Line width in Figures (pt)
    lineWidth = 0.5
    # Choice of Font ("Arial" / "Times New Roman" / "CMU Serif")
    fontChoice = "Times New Roman"
    # Output File Paths for Plot
    if timestamp == None: # e.g. when standalone script
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if plotPath == None: # e.g. when standalone script
        plotPathPNG = timestamp + '.png'
        plotPathPDF = timestamp + '.pdf'
    else:
        plotPathPNG = plotPath + '.png'
        plotPathPDF = plotPath + '.pdf'

    # Plot Configuration
    plt.rcParams['font.family'] = fontChoice
    plt.rcParams['axes.linewidth'] = lineWidth
    plt.rcParams["figure.figsize"] = (figSizeXinches, figSizeYinches)

    plt.plot(x_axis_data, y_axis_data)
    plt.ylabel('Y axis data (adim.)')
    plt.xlabel('X axis data (adim.)')
    plt.grid(True)

    if savePlot and png_plot:
        plt.savefig(plotPathPNG)
    if savePlot and pdf_plot:
        plt.savefig(plotPathPDF)
    if showFigure:
        plt.show()

if __name__ == "__main__":
    print("Standalone script not yet delevoped.")