"""
A demo to walk through an existing CdTe raw file.
"""

import numpy as np

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QSizePolicy, QVBoxLayout
import pyqtgraph as pg

from FoGSE.read_raw_to_refined.readRawToRefinedRTD import RTDReader
from FoGSE.demos.readRawToRefined_fake_rtd import RTDFileReader
from FoGSE.visualization import DetectorPlotView

    
class RTDWindow(DetectorPlotView):
    """
    An individual window to display RTD data read from a file.

    Parameters
    ----------
    data_file : `str` 
        The file to be passed to `FoGSE.read_raw_to_refined.readRawToRefinedRTD.RTDReader()`.
        If given, takes priority over `reader` input.
        Default: None

    reader : instance of `FoGSE.read_raw_to_refined.readRawToRefinedCdTe.ReaderBase()`
        The reader already given a file.
        Default: None
    """
    def __init__(self, data_file=None, reader=None, parent=None, name="RTD"):

        DetectorPlotView.__init__(self, parent, name)

        # decide how to read the data
        if data_file is not None:
            # probably the main way to use it
            self.reader = RTDReader(data_file)
        elif reader is not None:
            # useful for testing and if multiple windows need to share the same file
            self.reader = reader
        else:
            print("How do I read the RTD data?")

        self.graphPane_chip1 = self.graphPane
        self.graphPane_chip1.setMinimumSize(QtCore.QSize(800,350))
        self.graphPane_chip1.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.graphPane_chip2 = pg.PlotWidget(self)
        self.graphPane_chip2.setMinimumSize(QtCore.QSize(800,350))
        self.graphPane_chip2.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.chip2_layout = QVBoxLayout()
        self.chip2_layout.addWidget(
            self.graphPane_chip2
        )
        self.layoutCenter.addLayout(self.chip2_layout)

        self.graphPane_chip1.setBackground('w')
        self.graphPane_chip1.showGrid(x=True, y=True)
        self.graphPane_chip2.setBackground('w')
        self.graphPane_chip2.showGrid(x=True, y=True)

        #https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/legenditem.html
        self.graphPane_chip1.addLegend(offset=-0.5, labelTextSize='15pt',labelTextColor='k', **{'background-color':'w'}) 
        self.graphPane_chip2.addLegend(offset=-0.5, labelTextSize='15pt',labelTextColor='k', **{'background-color':'w'}) 

        # should match the data, big problems if not
        self.temp_sensors_chip1 = ['ts0', 'ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ts7', 'ts8']
        self.temp_sensors_chip2 = ['ts9', 'ts10', 'ts11', 'ts12', 'ts13', 'ts14', 'ts15', 'ts16', 'ts17']

        self.temp_sensor_names_chip1 = ['ts0', 'ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ts7', 'ts8']
        self.temp_sensor_names_chip2 = ['Formatter Pi CPU', 'Formatter SPMU-001 FPGA', 'DE Pi CPU', 'DE Pi SPMU-001 FPGA', 'Housekeeping microcontroller', 'Power 12 V regulator', 'Power 5 V regulator', 'Power 5.5 V regulator', 'CdTe canister 1 FPGA']
        self.colors_chip1       = ['b',   'g',   'r',   'c',   'y',   'm',  'brown','pink','purple']
        self.colors_chip2       = ['k', 'g', 'r',    'darkCyan',    'b',    'pink',    'darkGreen','darkGray', 'purple']

        self.sensor_plot_data_chip1 = dict(zip(['ti', *self.temp_sensors_chip1], [[],[],[],[],[],[],[],[],[],[]]))
        self.sensor_plot_data_chip2 = dict(zip(['ti', *self.temp_sensors_chip2], [[],[],[],[],[],[],[],[],[],[]]))

        self.sensor_plots_chip1 = dict()
        for c,(t,n) in enumerate(zip(self.temp_sensors_chip1, self.temp_sensor_names_chip1)):
            self.sensor_plots_chip1[t] = self.plot(self.graphPane_chip1, [0,0], [0,0], color=self.colors_chip1[c], plotname=n)
        
        self.sensor_plots_chip2 = dict()
        for c,(t,n) in enumerate(zip(self.temp_sensors_chip2, self.temp_sensor_names_chip2)):
            self.sensor_plots_chip2[t] = self.plot(self.graphPane_chip2, [0,0], [0,0], color=self.colors_chip2[c], plotname=n)

        # set title and labels
        self.set_labels(self.graphPane_chip1, xlabel="Time (UNIX)", ylabel="Temperature (C)", title="Chip 1: RTD Temperatures")
        self.set_labels(self.graphPane_chip2, xlabel="Time (UNIX)", ylabel="Temperature (C)", title="Chip 2: RTD Temperatures")

        self.reader.value_changed_collection.connect(self.update_plot)

        # Disable interactivity
        self.graphPane.setMouseEnabled(x=False, y=False)  # Disable mouse panning & zooming
        

    def update_plot(self):
        """
        Defines how the plot window is updated for time series.

        In subclass define methods: 
        *`get_data` to extract the new image frame from `self.data_file`, 
        *`update_image` to define how the new image affects the current one,
        *`process_data` to perform any last steps before updating the plot.
        """
        
        new_data = self.reader.collection.new_data
        print(new_data)
        if len(new_data['ti'])==0:
            return
        
        # defined how to add/append onto the new data arrays
        self.add_plot_data_chip1(new_data)
        self.add_plot_data_chip2(new_data)

        # plot the newly updated x and ys
        for c,t in enumerate(self.temp_sensors_chip1):
            _no_nans = ~np.isnan(self.sensor_plot_data_chip1[t]) #avoid plotting nans
            if len(self.sensor_plot_data_chip1[t][_no_nans])>1:
                #pyqtgraph won't plot 1 data-point and throws an error instead :|
                self.sensor_plots_chip1[t].clear()
                self.sensor_plots_chip1[t].setData(self.sensor_plot_data_chip1['ti'][_no_nans], self.sensor_plot_data_chip1[t][_no_nans])

        for c,t in enumerate(self.temp_sensors_chip2):
            _no_nans = ~np.isnan(self.sensor_plot_data_chip2[t]) #avoid plotting nans
            if len(self.sensor_plot_data_chip2[t][_no_nans])>1:
                #pyqtgraph won't plot 1 data-point and throws an error instead :|
                self.sensor_plots_chip2[t].clear()
                self.sensor_plots_chip2[t].setData(self.sensor_plot_data_chip2['ti'][_no_nans], self.sensor_plot_data_chip2[t][_no_nans])

    def add_plot_data_chip1(self, separated_data):
        """ Adds the new data to the array to be plotted. """

        _keep_s = 120 # secs

        self.sensor_plot_data_chip1['ti'] = np.array(list(self.sensor_plot_data_chip1['ti']) + list(separated_data['ti']))
        _keep_i = np.nonzero(self.sensor_plot_data_chip1['ti']>=(self.sensor_plot_data_chip1['ti'][-1]-_keep_s))
        self.sensor_plot_data_chip1['ti'] = self.sensor_plot_data_chip1['ti'][_keep_i]

        minmax = []
        for t in self.temp_sensors_chip1:
            self.sensor_plot_data_chip1[t] = np.array(list(self.sensor_plot_data_chip1[t]) + list(separated_data[t]))[_keep_i]
            minmax.append([np.min(self.sensor_plot_data_chip1[t]), np.max(self.sensor_plot_data_chip1[t])])
        minmax = np.array(minmax)
        
        if (not np.all(np.isnan(minmax[:,0]))):
            self.graphPane_chip1.plotItem.vb.setLimits(yMin=np.nanmin(minmax[:,0]))
        if (not np.all(np.isnan(minmax[:,1]))):
            self.graphPane_chip1.plotItem.vb.setLimits(yMax=np.nanmax(minmax[:,1]))
        self.graphPane_chip1.plotItem.vb.setLimits(xMin=self.sensor_plot_data_chip1['ti'][0], 
                                                   xMax=self.sensor_plot_data_chip1['ti'][-1]+1)#2.5 to make space for legend
        
    def add_plot_data_chip2(self, separated_data):
        """ Adds the new data to the array to be plotted. """

        _keep_s = 120 # secs

        self.sensor_plot_data_chip2['ti'] = np.array(list(self.sensor_plot_data_chip2['ti']) + list(separated_data['ti']))
        _keep_i = np.nonzero(self.sensor_plot_data_chip2['ti']>=(self.sensor_plot_data_chip2['ti'][-1]-_keep_s))
        self.sensor_plot_data_chip2['ti'] = self.sensor_plot_data_chip2['ti'][_keep_i]

        minmax = []
        for t in self.temp_sensors_chip2:
            self.sensor_plot_data_chip2[t] = np.array(list(self.sensor_plot_data_chip2[t]) + list(separated_data[t]))[_keep_i]
            minmax.append([np.min(self.sensor_plot_data_chip2[t]), np.max(self.sensor_plot_data_chip2[t])])
        minmax = np.array(minmax)
        
        if (not np.all(np.isnan(minmax[:,0]))):
            self.graphPane_chip2.plotItem.vb.setLimits(yMin=np.nanmin(minmax[:,0]))
        if (not np.all(np.isnan(minmax[:,1]))):
            self.graphPane_chip2.plotItem.vb.setLimits(yMax=np.nanmax(minmax[:,1]))
        self.graphPane_chip2.plotItem.vb.setLimits(xMin=self.sensor_plot_data_chip2['ti'][0], 
                                                   xMax=self.sensor_plot_data_chip2['ti'][-1]+1)#2.5 to make space for legend
        

    def set_labels(self, graph_widget, xlabel="", ylabel="", title=""):
        """
        Method just to easily set the x, y-label andplot title without having to write all lines below again 
        and again.

        [1] https://stackoverflow.com/questions/74628737/how-to-change-the-font-of-axis-label-in-pyqtgraph

        arameters
        ----------
        graph_widget : `PyQt6 PlotWidget`
            The widget for the labels

        xlabel, ylabel, title : `str`
            The strings relating to each label to be set.
        """
        graph_widget.setTitle(title, color='k', size='25pt')

        # Set label for both axes
        styles = {'color':'k', 'font-size':'20pt'} 
        graph_widget.setLabel('bottom', xlabel, **styles)
        graph_widget.setLabel('left', ylabel, **styles)

    def plot(self, graph_widget, x, y, color, plotname=''):
        pen = pg.mkPen(color=color, width=5)
        return graph_widget.plot(x, y, name=plotname, pen=pen)

    

if __name__=="__main__":
    # package top-level
    import os
    DATAFILE = os.path.dirname(os.path.realpath(__file__)) + "/../../../fake_temperatures.txt"
    DATAFILE = "/Users/kris/Desktop/housekeeping.log"

    def initiate_gui():
        app = QApplication([])

        # R = RTDFileReader(DATAFILE)
        R = RTDReader(DATAFILE)

        f0 = RTDWindow(reader=R)

        f0.show()
        app.exec()

    # def initiate_fake_rtds():
    #     from FoGSE.fake_foxsi.fake_rtds import fake_rtds

    #     # generate fake data and save to `datafile`
    #     fake_rtds(DATAFILE, loops=1_000_000)

    from multiprocessing import Process

    # fake temps
    # p1 = Process(target = initiate_fake_rtds)
    # p1.start()
    # live plot
    # p2 = Process(target = initiate_gui)
    # p2.start()
    # p2.join()

    initiate_gui()