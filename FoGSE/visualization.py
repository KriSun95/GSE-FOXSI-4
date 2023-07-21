import sys, typing, logging, math, json
import numpy as np
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QAbstractSeries
from PyQt6.QtWidgets import QWidget, QPushButton, QRadioButton, QComboBox, QGroupBox, QLineEdit, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QTabWidget, QDialog, QDialogButtonBox, QCheckBox, QFormLayout, QFileDialog, QSlider
import pyqtgraph as pg

from FoGSE.readBackwards import BackwardsReader
import FoGSE.application
# from FoGSE.application import GSEFocus, GSEMain
from FoGSE import communication as comm
from FoGSE import configuration as config
import os

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class AbstractVisualization(QWidget):
    """
    CURRENTLY UNUSED
    """
    def __init__(self):
        super().__init__()
        self.widgets = []               # store widgets that comprise the visualization
        self.layout = None              # store layout of widgets
        self.data = np.array([])        # store source data for display (may be singleton or whole spectra in dict etc.)

    def updateDisplay(self):
        pass

    def retrieveData(self, source):
        pass



class GlobalCommandPanel(QWidget):
    """
    `GlobalCommandPanel` provides a unified interface to send any uplink commands to the Formatter. This is enabled by the communication.FormatterUDPInterface, which handles the socket I/O. The widget is laid out horizontally on the screen and provides a series of dropdown menus used to build up a valid command bitstring.

    :param name: Unique name of this panel interface.
    :type name: str
    :param label: Label for this interface (for display).
    :type label: str
    :param cmddeck: Command deck object (instantiated using .json config files), used for command validation and filtering.
    :type cmddeck: communication.UplinkCommandDeck
    :param fmtrif: Formatter UDP interface object.
    :type fmtrif: communication.FormatterUDPInterface
    """

    def __init__(self, parent=None, name="PLACEHOLDER", configuration=None, formatter_if=comm.FormatterUDPInterface()):
        QWidget.__init__(self, parent)

        self.name = name
        self.label = "Global command uplink"

        # build and validate list of allowable uplink commands
        # self.cmddeck = comm.UplinkCommandDeck("config/all_systems.json", "config/all_commands.json")
        # self.cmddeck = comm.UplinkCommandDeck("foxsi4-commands/all_systems.json", "foxsi4-commands/commands.json")
        self.cmddeck = comm.UplinkCommandDeck("foxsi4-commands/systems.json")

        # open UDP socket to remote
        # self.fmtrif = comm.FormatterUDPInterface(addr="127.0.0.1", port=9999, logging=True, logfilename=None)
        self.fmtrif = formatter_if

        # track current command being assembled in interface
        self._working_command = []
        
        # group all UI elements in widget
        self.cmd_box = QGroupBox(self.label)

        # make UI widgets:
        self.box_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.system_label = QLabel("System")
        self.system_combo_box = QComboBox()
        self.command_label = QLabel("Command")
        self.command_combo_box = QComboBox()
        self.args_label = QLabel("Argument")
        self.command_args_text = QLineEdit()
        self.send_label = QLabel("")
        self.command_send_button = QPushButton("Send command")

        # populate dialogs with valid lists:
        for sys in self.cmddeck.systems:
            self.system_combo_box.addItem(sys.name.lower())

        # for cmd in self.cmddeck[].commands:
        #     self.command_combo_box.addItem(cmd.name)

        # populate layout:
        self.grid_layout.addWidget(
            self.system_label,
            0,0,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.system_combo_box,
            1,0,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.command_label,
            0,1,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.command_combo_box,
            1,1,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.args_label,
            0,2,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.command_args_text,
            1,2,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.send_label,
            0,3,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.grid_layout.addWidget(
            self.command_send_button,
            1,3,1,1,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )

        # somehow, this aligns the Widgets in the grid top-left:
        self.grid_layout.setRowStretch(self.grid_layout.rowCount(),1)
        self.grid_layout.setColumnStretch(self.grid_layout.columnCount(),1)

        # add grid layout to box
        self.cmd_box.setLayout(self.grid_layout)

        # add box to a global layout for whole self widget
        self.box_layout.addWidget(self.cmd_box)
        self.box_layout.addStretch(10)
        self.setLayout(self.box_layout)

        # hook up callbacks
        self.system_combo_box.activated.connect(self.systemComboBoxClicked)
        self.command_combo_box.activated.connect(self.commandComboBoxClicked)
        self.command_args_text.returnPressed.connect(self.commandArgsEdited)
        self.command_send_button.clicked.connect(self.commandSendButtonClicked)

        # disable downstream command pieces (until selection is made)
        self.command_combo_box.setEnabled(False)
        self.command_args_text.setEnabled(False)
        self.command_send_button.setEnabled(False)
    
    def systemComboBoxClicked(self, events):
        self.command_combo_box.setEnabled(False)
        self.command_args_text.setEnabled(False)
        self.command_send_button.setEnabled(False)

        cmds = self.cmddeck.get_commands_for_system(self.system_combo_box.currentText())
        names = [cmd.name for cmd in cmds]
        
        # start working command with address of selected system
        self._working_command = []
        self._working_command.append(self.cmddeck.get_system_by_name(self.system_combo_box.currentText()).addr)
        # todo: if adding delimiters, do it here.

        self.command_combo_box.clear()
        self.command_combo_box.addItems(names)
        self.command_combo_box.setEnabled(True)

    def commandComboBoxClicked(self, events):
        self.command_args_text.setEnabled(False)
        self.command_send_button.setEnabled(False)
        cmd = self.cmddeck.get_command_by_system_by_name(self.system_combo_box.currentText(), self.command_combo_box.currentText())

        # add cmd bitstring to working command
        self._working_command.append(cmd.hex)

        if cmd.arg_len > 0:
            self.command_args_text.setEnabled(True)
            # todo: some arg validation set up here. Implement in UplinkCommandDeck.
        else:
            self.command_send_button.setEnabled(True)

    def commandArgsEdited(self):
        # todo: some arg validation
        text = self.command_args_text.text()

        # add arg to working command
        self._working_command.append(int(text, 10))
        self.command_send_button.setEnabled(True)

    def commandSendButtonClicked(self, events):

        print("\tvalidating command...")
        # todo: validate
        if len(self._working_command) == 3:
            self.fmtrif.send(self._working_command[0], self._working_command[1], self._working_command[2])
        elif len(self._working_command) == 2:
            self.fmtrif.send(self._working_command[0], self._working_command[1])
        else:
            print(self._working_command)
            raise Exception("wrong length working command")

        print("\tlogging command (placeholder)...")
        # todo: log file setup, open, plus the actual logging

        self.command_combo_box.setEnabled(False)
        self.command_args_text.setEnabled(False)
        self.command_send_button.setEnabled(False)



class DetectorTableView(QWidget):
    """
    `DetectorTableView` is a PLACEHOLDER view for a strip/pixel data table. Will be used to view and edit strip/pixel data.
    """

    def __init__(self, parent=None, name="PLACEHOLDER", configuration=None, formatter_if=None):
        QWidget.__init__(self,parent)

        self.name=name
        self.label="Table"
        self.formatter_if=formatter_if

        self.widget = QLabel(self.label)
        self.layout = QGridLayout()
        self.layout.addWidget(self.widget, 1,1,1,1)
        self.setLayout(self.layout)



class DetectorParametersView(QWidget):
    # PLACEHOLDER
    def __init__(self, parent=None, name="PLACEHOLDER", configuration=None, formatter_if=None):
        QWidget.__init__(self,parent)

        self.name=name
        self.label="Parameters"
        self.formatter_if=formatter_if

        self.widget = QLabel(self.label)
        self.layout = QGridLayout()
        self.layout.addWidget(self.widget, 1,1,1,1)
        self.setLayout(self.layout)



class DetectorCommandView(QWidget):
    # PLACEHOLDER
    def __init__(self, parent=None, name="PLACEHOLDER", configuration=None, formatter_if=None):
        QWidget.__init__(self,parent)

        self.name=name
        self.label="Commands"
        self.formatter_if=formatter_if

        self.widget = QLabel(self.label)
        self.layout = QGridLayout()
        self.layout.addWidget(self.widget, 1,1,1,1)
        self.setLayout(self.layout)



class DetectorPlotView(QWidget):
    def __init__(self, parent=None, name="PLACEHOLDER", configuration=None, formatter_if=None):
        """
        Initialize a DetectorPlotView (inherits from PyQt6.QtWidgets.QWidget). This Widget consists of a central plot surrounded by buttons for controlling plot and detector behavior.

        :param parent: Optional parent widget.
        :type parent: PyQt6.QtWidgets.QWidget or None
        :return: a new DetectorPlotView object.
        :rtype: DetectorPlotView
        """

        QWidget.__init__(self, parent)

        # set up the plot:
        self.graphPane = pg.PlotWidget(self)
        self.spacing = 20
        self.name = name
        self.label = "Plot"
        self.formatter_if = formatter_if

        # initialize buttons:

        # used by DetectorContainer and DetectorPopout, do not use here! Gotta find a safer way to do this.
        # self.popout_button = QPushButton("Focus detector", self)
        self.popout_button = QPushButton("", parent=self)
        self.popout_button.setIcon(QtGui.QIcon("./assets/icon_popout_bg.svg"))
        self.popout_button.setFixedSize(24,24)
        self.popout_button.setIconSize(QtCore.QSize(24,24))
        self.popout_button.setStyleSheet("QPushButton {border-style: outset; border-width: 0px;}")

        # include buttons to allow GUI start/stop data reading/display
        self.modalStartPlotDataButton = QPushButton("Start plotting data", self)
        # self.modalStartPlotDataButton = QPushButton("", self)
        # self.modalStartPlotDataButton.setIcon(QtGui.QIcon("./assets/icon_play_bg.svg"))
        # self.modalStartPlotDataButton.setFixedSize(32,32)
        # self.modalStartPlotDataButton.setIconSize(QtCore.QSize(32,32))
        # self.modalStartPlotDataButton.setStyleSheet("QPushButton {border-style: outset; border-width: 0px;}")

        self.modalStopPlotDataButton = QPushButton("Stop plotting data", self)

        self.plotADCButton = QRadioButton("Plot in ADC bin", self)
        self.plotADCButton.setChecked(True)
        self.plotEnergyButton = QRadioButton("Plot in energy bin", self)
        self.plotStyleButton = QPushButton("Plot style", self)

        self.temperatureLabel = QLabel("Temperature (ºC):", self)
        self.voltageLabel = QLabel("Voltage (mV):", self)
        self.currentLabel = QLabel("Current (mA):", self)

        self.groupBox = QGroupBox(self.name)
        self.groupBox.setStyleSheet("QGroupBox {border-width: 2px; border-style: outset; border-radius: 10px; border-color: black;}")
        self.globalLayout = QHBoxLayout()

        # organize layout
        self.layoutLeftTop = QVBoxLayout()
        # self.layoutLeftTop.addWidget(
        #     self.popout_button,
        #     alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        # )
        self.layoutLeftTop.addStretch(self.spacing)

        self.layoutLeftBottom = QVBoxLayout()
        self.layoutLeftBottom.addWidget(
            self.temperatureLabel,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutLeftBottom.addWidget(
            self.voltageLabel,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutLeftBottom.addWidget(
            self.currentLabel,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutLeftBottom.addStretch(self.spacing)

        self.layoutRightTop = QVBoxLayout()
        self.layoutRightTop.addWidget(
            self.popout_button,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutRightTop.addWidget(
            self.plotADCButton,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutRightTop.addWidget(
            self.plotEnergyButton,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutRightTop.addWidget(
            self.plotStyleButton,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutRightTop.addStretch(self.spacing)

        self.layoutLeftTop.addWidget(
            self.modalStartPlotDataButton,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.layoutLeftTop.addWidget(
            self.modalStopPlotDataButton,
            alignment=QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        )
        
        self.layoutRightBottom = QVBoxLayout()
        self.layoutLeftTop.addStretch(self.spacing)

        self.layoutLeft = QVBoxLayout()
        self.layoutLeft.addLayout(self.layoutLeftTop)
        self.layoutLeft.addLayout(self.layoutLeftBottom)

        self.layoutRight = QVBoxLayout()
        self.layoutRight.addLayout(self.layoutRightTop)
        self.layoutRight.addLayout(self.layoutRightBottom)

        self.layoutCenter = QVBoxLayout()
        self.layoutCenter.addWidget(self.graphPane)
        self.layoutCenter.addSpacing(self.spacing)

        self.graphPane.setMinimumSize(QtCore.QSize(150,100))
        self.graphPane.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)

        self.layoutMain = QHBoxLayout()
        self.layoutMain.addLayout(self.layoutLeft)
        self.layoutMain.addLayout(self.layoutCenter)
        self.layoutMain.addLayout(self.layoutRight)

        self.groupBox.setLayout(self.layoutMain)
        self.globalLayout.addWidget(self.groupBox)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.setLayout(self.globalLayout)
        
        # connect to callbacks
        self.plotADCButton.clicked.connect(self.plotADCButtonClicked)
        self.plotEnergyButton.clicked.connect(self.plotEnergyButtonClicked)
        self.plotStyleButton.clicked.connect(self.plotStyleButtonClicked)
        self.modalStartPlotDataButton.clicked.connect(self.startPlotUpdate)
        self.modalStopPlotDataButton.clicked.connect(self.stopPlotUpdate)

        # set file to listen for that has the data in it
        self.dataFile = "foxsi.txt"
        # update plot every 100 ms
        self.callInterval = 100
        # read 50,000 bytes from the end of `self.dataFile` at a time
        self.bufferSize = 50_000 

    def plotADCButtonClicked(self, events):
        logging.debug("plotting in ADC space")
    
    def plotEnergyButtonClicked(self, events):
        logging.debug("plotting in energy space")

    def plotStyleButtonClicked(self, events):
        logging.debug("changing plot style")

    def startPlotUpdate(self):
        """
        Called when the `modalStartPlotDataButton` button is pressed.
        
        This starts a QTimer which calls `self.updatePlotData` with a cycle every `self.callInterval` 
        milliseconds. 

        [1] https://doc.qt.io/qtforpython/PySide6/QtCore/QTimer.html
        """

        logging.debug("starting to plot data")

        # define what happens to GUI buttons and start call timer
        self.modalStartPlotDataButton.setStyleSheet('QPushButton {background-color: white; color: green;}')
        self.modalStopPlotDataButton.setStyleSheet('QPushButton {background-color: white; color: black;}')
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.callInterval) # fastest is every millisecond here, with a value of 1
        self.timer.timeout.connect(self.updatePlotData) # call self.updatePlotData every cycle
        self.timer.start()

        logging.debug("data is plotting")

    def stopPlotUpdate(self):
        """
        Called when the `modalStopPlotDataButton` button is pressed.
        
        This stops a QTimer set by `self.start_plot_update`. 
        """

        logging.debug("stopping the data from plotting")
        self.modalStartPlotDataButton.setStyleSheet('QPushButton {background-color: white; color: black;}')
        self.modalStopPlotDataButton.setStyleSheet('QPushButton {background-color: white; color: red;}')
        self.timer.stop()
        logging.debug("data stopped from plotting")

    def updatePlotData(self):
        """Method has to be here to give `startPlotUpdate` method something to call."""
        pass

    def setlabels(self, graphWidget, xlabel="", ylabel="", title=""):
        """
        Method just to easily set the x, y-label andplot title without having to write all lines below again 
        and again.

        [1] https://stackoverflow.com/questions/74628737/how-to-change-the-font-of-axis-label-in-pyqtgraph

        arameters
        ----------
        graphWidget : `PyQt6 PlotWidget`
            The widget for the labels

        xlabel, ylabel, title : `str`
            The strings relating to each label to be set.
        """

        graphWidget.setTitle(title)

        # Set label for both axes
        graphWidget.setLabel('bottom', xlabel)
        graphWidget.setLabel('left', ylabel)


class DetectorPlotView1D(DetectorPlotView):
    """
    Detector plot class specifically for 1D data products (e.g., time profiles and spectra).
    """
    def __init__(self, parent=None, name="PLACEHOLDER", **kwargs):
        DetectorPlotView.__init__(self, parent, name, configuration=kwargs["configuration"])

        # initial time profile data
        self.x, self.y = [], []

        # plot the "data" that we have
        self.dataLine = self.graphPane.plot(
                                             self.x, 
                                             self.y,
                                             title="A chart",
                                             xlabel="x",
                                             ylabel="y"
                                            )


class DetectorPlotViewTP(DetectorPlotView1D):
    """
    Detector panel class specifically for time profiles.
    """

    def __init__(self, parent=None, name="PLACEHOLDER", **kwargs):
        DetectorPlotView1D.__init__(self, parent, name, configuration=kwargs["configuration"], formatter_if=kwargs["formatter_if"])

        # defines how may x/y points to average over beffore plotting, not important just doing some data processing
        self.averageEvery = 3

        # set title and labels
        self.setlabels(self.graphPane, xlabel="Time [?]", ylabel="Counts [?]", title="Time Profile")

    def getData(self, lastX):
        """
        Read the file `self.dataFile` from the end with a memory buffer size of `self.bufferSize` and 
        return data from lines with a first value greater than `lastX`

        Parameters
        ----------
        lastX : `int`, `float`
            The value of the last x-value plotted. Used to filter out data lines already plotted.

        Returns
        -------
        `tuple` :
            (x, y) The new x and y coordinates to be plots where x>`lastX`.
        """

        # check if the file exists yet, if not return nothing
        if not os.path.exists(self.dataFile):
            return [],[] # empty x, y

        # read the file `self.bufferSize` bytes from the end and extract the lines
        # forward=True: reads buffer from the back but doesn't reverse the data 
        with BackwardsReader(file=self.dataFile, blksize=self.bufferSize, forward=True) as f:
            lines = f.readlines()

        # check we got a sufficient amount of data from the file (need less han 3 because we data[1:-1] later)
        if lines==[] or len(lines)<3:
            return [],[] # empty x, y

        # got the data from file, now format for new_x and new_y
        data = [l.split(b' ') for l in lines]

        # to be sure I have full lines! Think of something better later, buffer size may have cut first/last line
        data = data[1:-1] 
        
        # extract the x and y data into two arrays
        data = np.array(data, dtype=float)
        newXs, newYs = data[:,0], data[:,1]

        # find indices of the x and ys not plotted yet
        mask = (newXs>lastX) if lastX is not None else np.array([True]*len(newXs))

        # if no entries are to be plotted just return nothing
        if (~mask).all():
            return [],[] # empty x, y
        
        # apply mask
        arrx, arry = newXs[mask], newYs[mask]

        # apply some averaging, not important at all
        xs = np.mean(arrx[:(len(arrx)//self.averageEvery)*self.averageEvery].reshape(-1,self.averageEvery), axis=1)
        ys = np.mean(arry[:(len(arry)//self.averageEvery)*self.averageEvery].reshape(-1,self.averageEvery), axis=1)
        
        # return the new x and ys
        return xs.tolist(), ys.tolist()

    def updatePlotData(self):
        """
        Defines how the plot window is updated.
        """
        
        # get already-plotted data and format into a more convenient form
        x, y = self.dataLine.getData()
        x, y = x if x is not None else [], y if y is not None else []
        x, y = np.array(x).squeeze(), np.array(y).squeeze()
        
        # now tray to make it a list, may fail but catch that too
        try:
            x, y = x.tolist(), y.tolist()
        except AttributeError:
            #AttributeError: 'NoneType' object has no attribute 'tolist', this from having nothing plotted originally
            x, y = [], []

        # find the last x-value plotted
        lastX = x[-1] if len(x)>0 else None
        newX, newY = self.getData(lastX)

        # depending on 1 or more new values, add or append into the x and y list
        if type(newX)==list:
            x += newX
            y += newY
        else:  
            x.append(newX)
            y.append(newY)

        # plot the newly updated x and ys
        self.dataLine.setData(np.array(x).squeeze(), np.array(y).squeeze())

class DetectorPlotViewSP(DetectorPlotView1D):
    """
    Detector panel class specifically for spectra.
    """

    def __init__(self, parent=None, name="PLACEHOLDER", **kwargs):
        DetectorPlotView1D.__init__(self, parent, name, configuration=kwargs["configuration"], formatter_if=kwargs["formatter_if"])

        # set title and labels
        self.setlabels(self.graphPane, xlabel="Bin [?]", ylabel="Counts [?]", title="Spectrum")

        # only update bins, so x is fixed and y will be updated
        self.numSpecBins = 50

    def getData(self, lastX):
        """
        Read the file `self.dataFile` from the end with a memory buffer size of `self.bufferSize` and 
        return data from lines with a first value greater than `lastX`

        Parameters
        ----------
        lastX : `int`, `float`
            The value of the last x-value plotted. Used to filter out data lines already plotted.

        Returns
        -------
        `tuple` :
            (x, y) The new x and y coordinates to be plots where x>`lastX`.
        """

        # check if the file exists yet, if not return nothing
        if not os.path.exists(self.dataFile):
            return [],[] # empty x, y

        # read the file `self.bufferSize` bytes from the end and extract the lines
        # forward=True: reads buffer from the back but doesn't reverse the data 
        with BackwardsReader(file=self.dataFile, blksize=self.bufferSize, forward=True) as f:
            lines = f.readlines()

        # check we got a sufficient amount of data from the file (need less han 3 because we data[1:-1] later)
        if lines==[] or len(lines)<3:
            return [],[] # empty x, y

        # got the data from file, now format for new_x and new_y
        data = [l.split(b' ') for l in lines]

        # to be sure I have full lines! Think of something better later, buffer size may have cut first/last line
        data = data[1:-1] 
        
        # extract the x and y data into two arrays
        data = np.array(data, dtype=float)
        newXs, newYs = data[:,0], data[:,1]

        # find indices of the x and ys not plotted yet
        mask = (newXs>lastX) if lastX is not None else np.array([True]*len(newXs))

        # if no entries are to be plotted just return nothing
        if (~mask).all():
            return [],[] # empty x, y
        
        # apply mask
        arrx, arry = newXs[mask], newYs[mask]
        
        # return the new x and ys
        return arrx.tolist(), arry.tolist()

    def updatePlotData(self):
        """
        Defines how the plot window is updated.

        *** Revisit, not finished (obviously). Needs to be smarter. ***
        """

        # get already-plotted data and format into a more convenient form
        x, y = self.dataLine.getData()
        x, y = x if x is not None else [], y if y is not None else []
        x, y = np.array(x).squeeze(), np.array(y).squeeze()
        
        # now tray to make it a list, may fail but catch that too
        try:
            x, y = x.tolist(), y.tolist()
        except AttributeError:
            #AttributeError: 'NoneType' object has no attribute 'tolist', this from having nothing plotted originally
            x, y = [], []

        # find the last x-value plotted
        lastX = x[-1] if len(x)>0 else None
        newX, newY = self.getData(lastX)

        # make new spectrum
        diff = self.numSpecBins-len(newY)
        newY = newY+[0]*diff if diff>0 else newY[:self.numSpecBins]
        

        # plot the newly updated x and ys
        self.dataLine.setData(np.arange(1,self.numSpecBins+1), newY)

class DetectorPlotView2D(DetectorPlotView):
    """
    Detector panel class specifically for 2D data products (e.g., images and spectrograms).
    
    [1] https://stackoverflow.com/questions/60200981/pyqt5-convert-2d-np-array-to-qimage
    [2] https://stackoverflow.com/questions/18020668/how-to-insert-an-image-from-file-into-a-plotwidget-plt1-pg-plotwidgetw
    [3] https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html
    """

    def __init__(self, parent=None, name="PLACEHOLDER", **kwargs):
        DetectorPlotView.__init__(self, parent, name, configuration=kwargs["configuration"], formatter_if=kwargs["formatter_if"])

        # set height and width of image in pixels
        self.detH, self.detW = 100, 100

        # number of frames to fade old counts over
        self.fadeOut = 10

        # set all rgba info (e.g., mode rgb or rgba, indices for red green blue, etc.)
        self.colourMode = "rgba"
        self.channel = {"red":0, "green":1, "blue":2}
        # alpha index
        self.alpha = 3
        # numpy array format (crucial for some reason)
        self.numpyFormat = np.uint8
        # colours range from 0->255 in RGBA
        self.minVal, self.maxVal = 0, 255
        # set self.myArray and self.cformat with zeros and mode, respectively
        self.setImageNdarray() 
        
        # create QImage from numpy array 
        qImage = pg.QtGui.QImage(self.myArray, self.detH, self.detW, self.cformat)

        # send image to fram and add to plot
        self.img = QtWidgets.QGraphicsPixmapItem(pg.QtGui.QPixmap(qImage))
        self.graphPane.addItem(self.img)

    def updateImageDimensions(self, height=-1, width=-1):
        """
        Change image height and width after initialisation.

        Parameters
        ----------
        height, width : `int`
            The new image height and width in pixels.
            Default: -1
        """
        height = height if height!=-1 else self.detH
        width = width if width!=-1 else self.detW

        self.detH, self.detW = height, width
        self.setImageNdarray()

    def updateImageColourFormat(self, colourFormat="rgba"):
        """
        Change image colour format after initialisation.

        Parameters
        ----------
        colourFormat : `str`
            The new image colour format (e.g., rgba or rgb).
            Default: rgba
        """
        self.colourMode = colourFormat
        self.setImageNdarray()
    
    def setImageNdarray(self):
        """
        Set-up the numpy array and define colour format from `self.colourMode`.
        """
        # colours range from 0->255 in RGBA8888 and RGB888
        # do we want alpha channel or not
        if self.colourMode == "rgba":
            self.myArray = np.zeros((self.detH, self.detW, 4))
            self.cformat = pg.QtGui.QImage.Format.Format_RGBA8888
            # for all x and y, turn alpha to max
            self.myArray[:,:,3] = self.maxVal 
        if self.colourMode == "rgb":
            self.myArray = np.zeros((self.detH, self.detW, 3))
            self.cformat = pg.QtGui.QImage.Format.Format_RGB888

        # define array to keep track of the last hit to each pixel
        self.noNewHitsCounterArray = (np.zeros((self.detH, self.detW))).astype(self.numpyFormat)


class DetectorPlotViewIM(DetectorPlotView2D):
    """
    Detector panel class specifically for images.
    """

    def __init__(self, parent=None, name="PLACEHOLDER", **kwargs):
        DetectorPlotView2D.__init__(self, parent, name, configuration=kwargs["configuration"], formatter_if=kwargs["configuration"])

        # set title and labels
        self.setlabels(self.graphPane, xlabel="X", ylabel="Y", title="Image")

    def getData(self, lastT):
        """
        Read the file `self.dataFile` from the end with a memory buffer size of `self.bufferSize` and 
        return data from lines with a first value greater than `lastX`.

        Parameters
        ----------
        lastT : `int`, `float`
            The value of the last time-value plotted. Used to filter out data events already plotted.

        Returns
        -------
        `numpy.ndarray` :
            The image frame made from a histogram of the new data in `self.dataFile`.
        """

        # check if the file exists yet, if not return nothing
        if not os.path.exists(self.dataFile ):
            return [] # empty frame

        # read the file `self.bufferSize` bytes from the end and extract the lines
        # forward=True: reads buffer from the back but doesn't reverse the data 
        with BackwardsReader(file=self.dataFile , blksize=self.bufferSize, forward=True) as f:
            lines = f.readlines()
            
        # check we got a sufficient amount of data from the file (need less han 3 because we data[1:-1] later)
        if lines==[] or len(lines)<3:
            return [] # empty frame

        # got the data from file, now format lines into each event
        data = [l.split(b' ') for l in lines]

        # to be sure I have full lines! Think of something better later, buffer size may have cut first/last line
        data = data[1:-1] 
        
        # extract the events data into arrays
        data = np.array(data, dtype=float)
        newTs, _, newXs, newYs = data[:,0], data[:,1], data[:,2], data[:,3]

        # filter out events already plotted
        mask = (newTs>lastT) if lastT is not None else np.array([True]*len(newXs))

        # since frame doesn't keep this info inherently then keep track of it ourselves
        self.lastTime = newTs[-1]

        # make sure there is new data to plot and mask the data
        if (~mask).all():
            return [] # empty frame
        newXs, newYs = newXs[mask], newYs[mask]
        
        # make a histogram from the events
        frame = np.histogram2d(newXs, newYs, bins=(np.arange(0,self.detH+1), np.arange(0,self.detW+1)))
        
        # return just the image array
        return frame[0]
    
    def updateImage(self, existingFrame, newFrame):
        """
        Add new frame to the current frame while recording the newsest hits in the `newFrame` image. Use 
        the new hits to control the alpha channel via `self.fadeControl` to allow old counts to fade out.
        
        Only using the blue and alpha channels at the moment.

        Parameters
        ----------
        existingFrame : `numpy.ndarray`
            This is the RGB (`self.colourMode='rgb'`) or RGBA (`self.colourMode='rgba'`) array of shape 
            (`self.detW`,`self.detH`,3) or (`self.detW`,`self.detH`,4), respectively.

        newFrame : `numpy.ndarray`
            This is a 2D array of the new image frame created from the latest data of shape (`self.detW`,`self.detH`).
        """

        # if newFrame is a list then it's empty and so no new frame, make all 0s
        if type(newFrame)==list:
            newFrame = np.zeros((self.detH, self.detW))
        
        # what pixels have a brand new hit? (0 = False, not 0 = True)
        new_hits = newFrame.astype(bool) 
        
        # add the new frame to the blue channel values and update the `self.myArray` to be plotted
        self.myArray[:,:,self.channel["blue"]] = existingFrame[:,:,self.channel["blue"]] + newFrame

        # if there is an alpha channel, use to fade out pixels that haven't had a new count
        if self.colourMode == "rgba":
            self.fadeControl(newHitsArray=new_hits)


    def fadeControl(self, newHitsArray):
        """
        Fades out pixels that haven't had a new count in steps of `self.maxVal//self.fadeOut` until a pixel has not had an 
        event for `self.fadeOut` frames. If a pixel has not had a detection in `self.fadeOut` frames then reset the colour 
        channel to zero and the alpha channel back to `self.maxVal`.

        *** Will likely revisit and control fading with decreasing the colour channel value instead with the same maths used to 
          decrease alpha. This would stop bins with previous counts that are almost about to fade out completely coming back in 
           and adding to the next frame. ***

        Parameters
        ----------
        newFrame : `numpy.ndarray`, `bool`
            This is a 2D boolean array of shape (`self.detW`,`self.detH`) which shows True if the pixel has just detected 
            a new count and False if it hasn't.
        """

        # reset counter if pixel has new hit
        self.noNewHitsCounterArray[newHitsArray] = 0

        # add to counter if pixel has no hits
        self.noNewHitsCounterArray += ~newHitsArray

        # set alpha channel, fade by decreasing steadily over `self.fadeOut` steps 
        # (a step for every frame the pixel has not detected an event)
        self.myArray[:,:,self.alpha] = self.maxVal - (self.maxVal//self.fadeOut)*self.noNewHitsCounterArray


        # find where alpha is zero (completely faded)
        turnOffColour = (self.myArray[:,:,self.alpha]==0)

        # now set the colour back to zero and return alhpa to max, ready for new counts
        for k in self.channel.keys():
            self.myArray[:,:,self.channel[k]][turnOffColour] = 0
        # reset alpha
        self.myArray[:,:,self.alpha][turnOffColour] = self.maxVal 
        
    
    def updatePlotData(self):
        """
        Defines how the plot window is updated.
        """

        # see if there was a previous frame with an associated time
        lastT = self.lastTime if hasattr(self, "lastTime") else None

        # get the new frame
        newFrame = self.getData(lastT)

        # update current plotted data with new frame
        self.updateImage(existingFrame=self.myArray, newFrame=newFrame)
        
        # make sure everything is normalised between 0--255
        norm = np.max(self.myArray, axis=(0,1))
        norm[norm==0] = 1 # can't divide by 0
        uf = self.maxVal*self.myArray//norm

        # allow this all to be looked at if need be
        self.qImageDetails = [uf.astype(self.numpyFormat), self.detH, self.detW, self.cformat]

        # new image
        qImage = pg.QtGui.QImage(*self.qImageDetails)#Format.Format_RGBA64

        # faster long term to remove pervious frame and replot new one
        self.graphPane.removeItem(self.img)
        self.img = QtWidgets.QGraphicsPixmapItem(pg.QtGui.QPixmap(qImage))
        self.graphPane.addItem(self.img)
    


class DetectorContainer(QWidget):
    """
    `DetectorContainer` is the interface between `Detector...View`s (frontend) and detector data (backend). This class manages visibility of different detector views in main and focused windows, and persists detector data across view changes.

    :param name: Name for the container.
    :type name: str
    :param label: Label for the container for display.
    :type label: str
    :param formatter_if: Interface object (socket) to the Formatter uplink.
    :type formatter_if: FormatterUDPInterface
    :param plot_view: Detector plot view object.
    :type plot_view: DetectorPlotView
    :param table_view: Detector table view object for strips or pixels.
    :type table_view: DetectorTableView
    :param parameters_view: Detector parameters view object (fields for assorted detector settings).
    :type parameters_view: DetectorParametersView
    :param command_view: Detector command view object for sending uplink commands.
    :type command_view: DetectorCommandView
    :param popout_widget: Reference to the focus window for the container, if it exists.
    :type popout_widget: None | DetectorPopout
    :param all_widgets: List of all widgets aggregated under DetectorContainer (include plot_view, table_view, etc).
    :type all_widgets: list[QWidget]
    :param shown_in_main: List of all widgets which should be shown in main views of many detectors.
    :type shown_in_main: list[QWidget]
    :param shown_in_popout: List of all widgets which should be shown in popout view.
    :type shown_in_popout: list[QWidget]
    """
    def __init__(
        self, parent=None, 
        name="PLACEHOLDER", label="Placeholder", configuration=None, formatter_if=None,
        plot_view=None, table_view=None, parameters_view=None, command_view=None
    ):
        QWidget.__init__(self, parent)

        # handle init args
        self.name = name
        self.label = label
        self.formatter_if = formatter_if
        self.plot_view = plot_view
        self.table_view = table_view
        self.parameters_view = parameters_view
        self.command_view = command_view

        self.popout_widget = None
        
        # define which widgets get seen in which views:
        self.all_widgets = [
            self.plot_view, 
            self.table_view, 
            self.parameters_view, 
            self.command_view
        ]
        self.shown_in_main = [
            self.plot_view
        ]
        self.shown_in_popout = [
            self.plot_view, 
            self.table_view, 
            self.parameters_view, 
            self.command_view
        ]

        # make the layout
        self.layout = QGridLayout()
        self.make_layout()

        # connect DetectorPlotView's Focus button to the popout action. Find a cleaner way of doing this (without reaching all the way into the attribute).
        self.plot_view.popout_button.clicked.connect(self.on_popout_button_clicked)

    def on_popout_button_clicked(self, events):
        """
        Connect this to the button which controls opening the popout window.
        """
        self.pop_out()

    def pop_out(self):
        """
        This method delegates opening the popout to the `DetectorPopout` constructor. 
        """
        # popout button should not be visible from within popout window
        self.plot_view.popout_button.hide()
        self.popout_widget = DetectorPopout(self)

    def pop_in(self):
        """
        This method "pops the container back in" by restoring the `DetectorContainer` main layout, and cleans up the popout window.
        """
        self.make_layout()
        # popout button should reappear now that popout window is closed
        self.plot_view.popout_button.show()
        # clean up popout_widget
        self.popout_widget = None

    def make_layout(self):
        """
        This is a convenience method for laying out the `DetectorContainer` widget. This layout should be used when using a `DetectorContainer` in a main (non-popout) view.
        """
        for i, view in enumerate(self.all_widgets):
            # start by hiding all widgets
            view.hide()

            # add all widgets to some layout
            self.layout.addWidget(view, 0, 1+i, 1, 1)

            # only show widgets which should be shown in main view
            if view in self.shown_in_main:
                view.show()
        
        self.setLayout(self.layout)



class DetectorPopout(QWidget):
    """
    `DetectorPopout` defines the tabbed visual interface for managing all detector parameters and views. This class should be instantiated and fed data from a `DetectorContainer`. Since it has no parent, this object should appear as a free-floating window.

    :param container: The `DetectorContainer` object delegating this popout window.
    :type container: DetectorContainer
    :param tabs: The tab manager object for holding different views within the detector container.
    :type tabs: QTabWidget
    """
    def __init__(self, add_container: DetectorContainer=None):
        QWidget.__init__(self)
        
        # add the widgets
        self.container = add_container
        self.tabs = QTabWidget()

        # make the layout
        self.layout = QGridLayout()
        self.make_layout()
        
    def make_layout(self):
        """
        This is a convenience method for laying out the `DetectorPopout` widget. This layout should be used when viewing a `DetectorContainer` in a focused (popout) view.
        """
        for i, view in enumerate(self.container.all_widgets):
            # first, hide all widgets
            view.hide()

            # then, add tabs and show widgets only for container widgets which should be shown in the popout
            if view in self.container.shown_in_popout:
                self.tabs.addTab(view, view.label)
                view.show()

        # add the tab widget to the global layout
        self.layout.addWidget(self.tabs, 0,0,1,1)
        self.setLayout(self.layout)
        self.show()

    def closeEvent(self, event):
        """
        This method is executed when the window for `DetectorPopout` is closed. It delegates the container back to the original `DetectorContainer`, then closes the window.
        """

        # clean up the DetectorPopout object and restore the main DetectorContainer view
        self.container.pop_in()

        # allow the window to close
        event.accept()



class DetectorArrayDisplay(QWidget):
    """
    A hexagonal tiling of DetectorPlotViews, à la the real FOXSI focal plane assembly.
    """
    def __init__(self, parent=None):
        QWidget.__init__(self,parent)

        # self.H = 800
        # self.W = 1280
        self.H = parent.height() - 100
        self.W = parent.width() - 100

        # todo: a not-terrible way of assigning these.
        detectorNames = ["Timepix", "CdTe3", "CdTe4", "CMOS1", "CMOS2", "CdTe1", "CdTe2"]

        self.setGeometry(10,10,self.W,self.H)

        # making hex geometry
        self.border = 0
        self.center = [0*self.x() + self.width()/2, self.y() + self.height()/2]
        # self.wradius = (self.center[0] - self.border)*2/3
        # self.hradius = (self.center[1] - self.border)*2/3

        # width of a panel within display
        self.panelWidth = 1/3*(self.width() - 2*self.border)
        self.panelHeight = 1/3*(self.height() - 2*self.border)
        # radius from self.center to center of rectangular pane
        self.wradius = self.panelWidth
        self.hradius = self.panelHeight
        self.hexagon = [self.center]
        for i in range(6):
            x = self.center[0] + self.wradius*math.cos(2*math.pi*i/6)
            y = self.center[1] + self.hradius*math.sin(2*math.pi*i/6)
            self.hexagon.append([x,y])

        logging.debug("semiwidth: %s" % self.panelWidth) 
        logging.debug("semiheight: %s" % self.panelHeight)
        logging.debug("hexagon: %s" % self.hexagon)

        # explicitly populate all default DetectorPlotView types
        self.detectorPanels = [
            DetectorPlotViewIM(self, name=detectorNames[0]),
            DetectorPlotViewTP(self, name=detectorNames[1]),
            DetectorPlotViewSP(self, name=detectorNames[2]),
            DetectorPlotView(self, name=detectorNames[3]),
            DetectorPlotView(self, name=detectorNames[4]),
            DetectorPlotView(self, name=detectorNames[5]),
            DetectorPlotView(self, name=detectorNames[6]),
        ]

        self.detectorPanels[0].dataFile = "/Volumes/sd-kris0/fake_foxsi_2d.txt"
        self.detectorPanels[1].dataFile = "/Volumes/sd-kris0/fake_foxsi_1d.txt"
        self.detectorPanels[2].dataFile = "/Volumes/sd-kris0/fake_foxsi_1d.txt"

        # putting rectangles in hexagon
        # rects = [QtCore.QRect(
        #     self.center[0] - self.panelWidth/2, 
        #     self.center[1] - self.panelHeight/2,
        #     self.panelWidth,
        #     self.panelHeight
        #     )]

        xs = []
        ys = []
        widths = []
        heights = []
        rects = []
        for i in range(7):
            xs.append(self.hexagon[i][0] - self.panelWidth/2)
            ys.append(self.hexagon[i][1] - self.panelHeight/2)
            widths.append(self.panelWidth)
            heights.append(self.panelHeight)

            rects.append(QtCore.QRectF(
                self.hexagon[i][0] - self.panelWidth/2,
                self.hexagon[i][1] - self.panelHeight/2,
                self.panelWidth,
                self.panelHeight
            ))

        grids = self.fitToGrid(rects, 20, 20, 1)
        intersections = self._rectsIntersect(grids[0], grids[1], grids[2], grids[3])
        intersectionsF = self._rectsIntersectF(xs, ys, widths, heights)

        # layouting
        self.layout = QGridLayout()
        for i in range(7):
            self.layout.addWidget(
                self.detectorPanels[i],
                grids[1][i], grids[0][i], grids[3][i], grids[2][i],
                # alignment=QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
        self.setLayout(self.layout)
        # self.setFixedSize(self.layout.sizeHint())
    
    def fitToGrid(self, rects, nrow, ncol, gridpad):
        minx = np.Inf
        maxx = -np.Inf
        miny = np.Inf
        maxy = -np.Inf

        #  get corner coords for each  rect
        N = len(rects)
        xl = [rect.x() for rect in rects]
        yl = [rect.y() for rect in rects]
        xh = [rect.x() + rect.width() for rect in rects]
        yh = [rect.y() + rect.height() for rect in rects]

        # get available rows, cols for rects by removing the padding
        rows = nrow - 2*gridpad
        cols = ncol - 2*gridpad
        if rows <= 0 or cols <= 0:
            raise Exception("too much pad or too little rows/cols")
        
        # scale factor from source space to grid
        xscale = rows/(max(xl) - min(xl))
        yscale = cols/(max(yl) - min(yl))

        # scale all rects into grid space
        xli = [gridpad + xscale*(xl[i] - min(xl)) for i in range(N)]
        yli = [gridpad + yscale*(yl[i] - min(yl)) for i in range(N)]
        xhi = [gridpad + xscale*(xh[i] - min(xl)) for i in range(N)]
        yhi = [gridpad + yscale*(yh[i] - min(yl)) for i in range(N)]

        # scale widths/heights to grid space and round to grid
        widths = [round(xhi[i] - xli[i]) for i in range(N)]
        heights = [round(yhi[i] - yli[i]) for i in range(N)]
        # round root corner of grid-space rects to grid
        xs = [round(xli[i]) for i in range(N)]
        ys = [round(yli[i]) for i in range(N)]

        return (xs, ys, widths, heights)

    def _rectsIntersect(self, xs, ys, widths, heights):
        N = len(xs)
        rects = []
        for i in range(N):
            rects.append(QtCore.QRect(xs[i], ys[i], widths[i], heights[i]))

        indexIntersect = []
        for i in range(N):
            for j in range(N):
                if i != j:
                    indexIntersect.append(rects[i].intersects(rects[j]))
        
        return indexIntersect

    def _rectsIntersectF(self, xs, ys, widths, heights):
        N = len(xs)
        rects = []
        for i in range(N):
            rects.append(QtCore.QRectF(xs[i], ys[i], widths[i], heights[i]))

        indexIntersect = []
        for i in range(N):
            for j in range(N):
                if i != j:
                    indexIntersect.append(rects[i].intersects(rects[j]))
        
        return indexIntersect



class DetectorGridDisplay(QWidget):
    """
    A gridded tiling of DetectorPlotViews, maybe more legible that `DetectorArrayDisplay`.
    """

    def __init__(self, parent=None, configuration=None, formatter_if=None):
        QWidget.__init__(self, parent)

        # self.H = 800
        # self.W = 1280
        self.H = parent.height() - 100
        self.W = parent.width() - 100

        # todo: a not-terrible way of assigning these.
        detector_names = ["Timepix", "CdTe3", "CdTe4", "CMOS1", "CMOS2", "CdTe1", "CdTe2"]

        self.setGeometry(10,10,self.W,self.H)

        self.settings_panel = config.SettingsPanel(self, name="Settings", settings_file="./config/settings.json", system_configuration=configuration)

        # explicitly populate all default DetectorPlotView types. NOTE: these are different than in DetectorArrayDisplay.
        self.detector_panels = [
            DetectorPlotViewIM(self, name=detector_names[0], configuration=configuration, formatter_if=formatter_if),
            DetectorPlotViewTP(self, name=detector_names[1], configuration=configuration, formatter_if=formatter_if),
            DetectorPlotViewSP(self, name=detector_names[2], configuration=configuration, formatter_if=formatter_if),
            DetectorPlotView(self, name=detector_names[3], configuration=configuration, formatter_if=formatter_if),
            DetectorPlotView(self, name=detector_names[4], configuration=configuration, formatter_if=formatter_if),
            DetectorPlotView(self, name=detector_names[5], configuration=configuration, formatter_if=formatter_if),
            DetectorPlotView(self, name=detector_names[6], configuration=configuration, formatter_if=formatter_if),
        ]

        self.detector_panels[0].dataFile = "/Volumes/sd-kris0/fake_foxsi_2d.txt"
        self.detector_panels[1].dataFile = "/Volumes/sd-kris0/fake_foxsi_1d.txt"
        self.detector_panels[2].dataFile = "/Volumes/sd-kris0/fake_foxsi_1d.txt"

        self.detector_containers = []
        for panel in self.detector_panels:
            self.detector_containers.append(DetectorContainer(
                self, name=panel.name, label=panel.label, configuration=configuration, formatter_if=formatter_if, 
                plot_view=panel, 
                table_view=DetectorTableView(self, "table"), 
                parameters_view=DetectorParametersView(self, "parameters"), 
                command_view=DetectorCommandView(self, "commands")
            ))

        # add commanding panel
        self.command_panel = GlobalCommandPanel(self, name="Command", configuration=configuration, formatter_if=formatter_if)

        self.grid_layout = QGridLayout()

        # add everything to the grid layout (based on .name attribute)
        for container in self.detector_containers:
            self._add_to_layout(container)
        
        self._add_to_layout(self.command_panel)
        self._add_to_layout(self.settings_panel)

        for container in self.detector_containers:
            container.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        
        # self.gridLayout.setRowStretch(self.gridLayout.rowCount(),1)
        for i in range(self.grid_layout.columnCount()):
            self.grid_layout.setColumnStretch(i,0)
        # self.gridLayout.setColumnStretch(self.gridLayout.columnCount(),1)

    def _add_to_layout(self, widget):
        if widget.name == "Timepix":
            self.grid_layout.addWidget(
                widget, 1,1,1,2
            )
        elif widget.name == "CMOS1":
            self.grid_layout.addWidget(
                widget, 2,1,1,2
            )
        elif widget.name == "CMOS2":
            self.grid_layout.addWidget(
                widget, 2,3,1,2
            )
        elif widget.name == "CdTe1":
            self.grid_layout.addWidget(
                widget, 3,1,1,1
            )
        elif widget.name == "CdTe2":
            self.grid_layout.addWidget(
                widget, 3,2,1,1
            )
        elif widget.name == "CdTe3":
            self.grid_layout.addWidget(
                widget, 3,3,1,1
            )
        elif widget.name == "CdTe4":
            self.grid_layout.addWidget(
                widget, 3,4,1,1
            )
        elif widget.name == "Command":
            self.grid_layout.addWidget(
                widget, 1,4,1,1
            )
        elif widget.name == "Settings":
            self.grid_layout.addWidget(
                widget, 1,3,1,1
            )
        else:
            raise Warning("widget name not found!")
        
        self.setLayout(self.grid_layout)
        widget.show()