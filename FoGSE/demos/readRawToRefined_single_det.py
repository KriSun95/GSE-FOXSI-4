"""
Create a class that will read the LOG file containing raw binary data received from 
FOXSI and parse the data to be readyfor the GUI plotting windows. 

There will be two main operations of this class with the class managing the communication 
between them.

1. The class will read the LOG file with the raw binary data collected from FOXSI and pass 
the raw data to the instrument parsers which return the data as physical units in a human 
readable format.

2. Take the human readable data format (event lists, arrays, etc.) and organise the data 
into general instrument collections (i.e., one for all CdTe data, one for TimePix, one for 
CMOS). Individual GUI display windows, to which this class will be passed to, will monitor 
their relevant collections (being connected through `QtCore.pyqtSignal`) and request these 
collection objects to be displayed.

One class is assigned to do both jobs since (at this time) we will always want to go from raw
binary data to a collected, human readable form for investigation and analysis.

At present (10/10/2023)
Can read:
    * CdTe

Cannot Read:
    * CMOS
    * Timepix
"""

import time
import struct

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget

from FoGSE.readBackwards import BackwardsReader
from FoGSE.parsers.CdTeparser import CdTerawalldata2parser
from FoGSE.collections.CdTeCollection import CdTeCollection


class Reader(QWidget):
    """
    Reader for the FOXSI instruments.

    Only support CdTe files (10/10/2023).
    """

    # need to be class variable to connect
    value_changed_collection = QtCore.pyqtSignal()

    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """
        QWidget.__init__(self, parent)

        self._collection = []

        # stand-in log file
        self.data_file = datafile
        self._old_data = 0
        self.old_data_time = 0

        # for timing tests
        self.start = time.time()

        # default is update plot every 100 ms
        self.call_interval()
        # read 50,000 bytes from the end of `self.data_file` at a time
        self.define_buffer_size(size=25_000)

        self.setup_and_start_timer()

    def define_buffer_size(self, size):
        """
        Method to set or change the file buffer size.

        Parameters
        ----------
        size : `int`, `float
            Buffer size in bytes.
        """
        if size%4!=0:
            new_size = int(int(size/4)*4)
            print(f"Buffer size must be divisable by 4 for parser code, changing to {new_size}.")
            self.buffer_size = new_size
        self.buffer_size = size

    def call_interval(self, call_interval=1000):
        """
        Define how often to attempt to read the data file.

        Parameters
        ----------
        call_interval : int
            Check the file every `call_interval` milliseconds.
            Default: 1000
        """
        self._call_interval = call_interval
        if hasattr(self,"timer"):
            self.timer.stop()
        self.setup_and_start_timer()

    def setup_and_start_timer(self):
        """ Control the start and stop of the timer. """
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self._call_interval) # fastest is every millisecond here, with a value of 1
        self.timer.timeout.connect(self.raw_2_collected) # call self.update_plot_data every cycle
        self.timer.start()

    @property
    def collection(self):
        """ 
        Property
        --------

        Property to return the data instrument collections created 
        by the reader. 
        """
        return self._collection

    @collection.setter
    def collection(self, new_collection):
        """ 
        Setter
        ------
        
        Used to set a new collection to previous ones and emit a call 
        via `self.value_changed_collections.emit()`.

        ** This only handles one collection right now. Will be converted 
        to list.
        """
        self._collection = new_collection
        self.value_changed_collection.emit()

    def check_enough_data(self, lines):
        """
        Method to check if there is enough data in the file to continue.

        Parameters
        ----------
        lines : list of strings
            The lines from the content of `self.data_file` obtained using 
            `FoGSE.readBackwards.BackwardsReader`.

        Returns
        -------
        `bool` :
            Boolean where True means there is enough data to plot and False 
            means there is not.
        """
        if (lines==[]) or (len(lines)<3):
            return False # empty x, y
        return True

    def return_empty(self):
        """
        Define what should take the place of the data if the file is either 
        empty or doesn't have anything new to plot.
        """
        return []

    def extract_raw_data(self):
        """
        Method to extract the data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `tuple` :
            (x, y) The new x and y coordinates read from `self.data_file`.
        """
        return self.extract_raw_data_cdte()
    
    def extract_raw_data_cdte(self):
        """
        Method to extract the CdTe data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `tuple` :
            (x, y) The new x and y coordinates read from `self.data_file`.
        """
        # read the file `self.bufferSize` bytes from the end and extract the lines
        # forward=True: reads buffer from the back but doesn't reverse the data 
        try:
            with BackwardsReader(file=self.data_file, blksize=self.buffer_size, forward=True) as f:
                iterative_unpack=struct.iter_unpack("<I",f.read_block())
                datalist=[]
                for _,data in enumerate(iterative_unpack):

                    datalist.append(data[0])
            if self._old_data==datalist:
                return self.return_empty() 
        except FileNotFoundError:
            return self.return_empty() 
        
        self._old_data = datalist
        return datalist

    def raw_2_parsed(self, raw_data):
        """
        Method to check if there is enough data in the file to continue.

        Parameters
        ----------
        raw_data : list of strings
            The lines from the content of `self.data_file` obtained using 
            `FoGSE.readBackwards.BackwardsReader`.

        Returns
        -------
        `tuple` :
            Output from the CdTe parser.
        """
        # return or set human readable data
        # do stuff with the raw data and return nice, human readable data
        try:
            flags, event_df, all_hkdicts = CdTerawalldata2parser(raw_data)
        except ValueError:
            # no data from parser so pass nothing on with a time of -1
            print("No data from parser.")
            flags, event_df, all_hkdicts = (None,{'ti':-1},None)
        return flags, event_df, all_hkdicts

    def parsed_2_collections(self, parsed_data):
        """
        Method to move the parsed data to the relevant collection.

        Parameters
        ----------
        parsed_data : `tuple`
            Output from the CdTe parser.

        Returns
        -------
        `FoGSE.detector_collections.CdTeCollection.CdTeCollection` :
            The CdTe collection.
        """
        # take human readable and convert and set to 
        # CdTeCollection(), TimePixCollection(), CMOSCollection()
        col = CdTeCollection(parsed_data, self.old_data_time)
        self.old_data_time = col.last_data_time
        return col

    def raw_2_collected(self):
        """ 
        Method to control the flow from raw data to parsed to 
        collected. 

        Sets the `collections` attribute.
        """
        raw = self.extract_raw_data()

        # might need in future: `if raw!=self.return_empty():``
        parsed = self.raw_2_parsed(raw)

        # assign the collected data and trigger the `emit`
        self.collections = self.parsed_2_collections(parsed)