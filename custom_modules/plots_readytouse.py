import matplotlib.pyplot as plt
from datetime import datetime

def plot_paper_format(x_axis_data, y_axis_data, x_axis_label='X axis data (adim.)', y_axis_label='Y axis data (adim.)', showFigure=False, savePlot=True, pdf_plot=True, png_plot=True, plotPath=None):
    # Figure Width (inches)
    figSizeXinches = 3.5
    figSizeYinches = 3
    # Font size in Figures
    fontSize = 8
    # Line width in Figures (pt)
    lineWidth = 0.5
    # Choice of Font ("Arial" / "Times New Roman" / "CMU Serif")
    fontChoice = "Times New Roman"
    # Output File Paths for Plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if plotPath == None: # e.g. when standalone script
        plotPathPNG = timestamp + '.png'
        plotPathPDF = timestamp + '.pdf'
    else:
        plotPathPNG = plotPath + timestamp + '.png'
        plotPathPDF = plotPath + timestamp + '.pdf'

    # Plot Configuration
    plt.rcParams['font.family'] = fontChoice
    plt.rcParams['axes.linewidth'] = lineWidth
    plt.rcParams["figure.figsize"] = (figSizeXinches, figSizeYinches)

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

if __name__ == "__main__":
    print("Standalone script not yet delevoped.")