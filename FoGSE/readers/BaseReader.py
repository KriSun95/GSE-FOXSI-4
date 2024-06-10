"""
Create a class that will read the LOG file containing raw binary data received from 
FOXSI and parse the data to be readyfor the GUI plotting windows. 

There will be two main operations of this class with the class managing the communication 
between them.

1. The class will read the LOG file with the raw binary data collected from FOXSI and pass 
the raw data to the instrument parser which return the data as physical units in a human 
readable format.

2. Take the human readable data format (event lists, arrays, etc.) and organise the data 
into general instrument collections (i.e., one for CdTe data, one for TimePix, one for 
CMOS). Individual GUI display windows, to which this class will be passed to, will monitor 
their relevant collections (being connected through `QtCore.pyqtSignal`) and request these 
collection objects to be displayed.

One class is assigned to do both jobs since (at this time) we will always want to go from raw
binary data to a collected, human readable form for investigation and analysis.
"""

import os

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget

# import parser for `extract_raw_data` and `extract_raw_data_<det>`
# import collection for `parsed_2_collections`
# for example `from FoGSE.telemetry_tools.parsers.CdTeparser import CdTerawalldata2parser`
# for example from `FoGSE.telemetry_tools.collections.CdTeCollection import CdTeCollection`

class BaseReader(QWidget):
    """
    General reader for the FOXSI instruments.

    Created such that only four (although only really three) methods need 
    to be defined for a given instrument. These are:
    * extract_raw_data() [only to return the output of the next method]
    * extract_raw_data_<det>()
    * raw_2_parsed()
    * parsed_2_collection()
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

        # sttr used to track whether self.data_file is modified
        self._cached_stamp = 0

        # default is update plot every 100 ms
        self.call_interval()
        # read 25,000 bytes from the end of `self.data_file` at a time
        self.define_buffer_size(size=25_000)

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
            print(f"Buffer size might need to be divisable by 4 for (CdTe) parser code, maybe try {new_size}?")
            # self.buffer_size = new_size
        self.buffer_size = size

    def call_interval(self, call_interval=100):
        """
        Define how often to attempt to read the data file.

        Parameters
        ----------
        call_interval : int
            Check the file every `call_interval` milliseconds.
            Default: 100
        """
        self._call_interval = call_interval
        if hasattr(self,"timer"):
            self.timer.stop()
            del self.timer
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
    def collection(self, new_collections):
        """ 
        Setter
        ------
        
        Used to set a new collection to previous ones and emit a call 
        via `self.value_changed_collections.emit()`.

        ** This only handles one collection right now. Will be converted 
        to list.
        """
        self._collection = new_collections
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
        # for example `return self.extract_raw_data_<det>()`

    def raw_2_parsed(self, raw_data):
        """
        Method to check if there is enough data in the file to continue.

        Should return parsed data in the correct format for the instrument 
        collection.

        Parameters
        ----------
        raw_data : list of strings
            The lines from the content of `self.data_file` obtained using 
            `FoGSE.readBackwards.BackwardsReader`.

        Returns
        -------
        `tuple` :
            Output from the <det> parser.
        """
        # return or set human readable data ready for <det> collection
        # do stuff with the raw data and return nice, human readable data

    def parsed_2_collection(self, parsed_data):
        """
        Method to move the parsed data to the relevant collection.

        Should also set `old_data_time` attribute from the colection 
        object.

        Parameters
        ----------
        parsed_data : `tuple`
            Output from the CdTe parser.

        Returns
        -------
        `FoGSE.detector_collections.CdTeCollection.CdTeCollection` :
            The CdTe collection.
        """
        # take human readable and convert and set to <det>Collection() e.g.,
        # CdTeCollection(), TimePixCollection(), or CMOSCollection()

        # for example
        # `col = CdTeCollection(parsed_data, self.old_data_time)`
        # `self.old_data_time = col.last_data_time`
        # `return col`

    def file_modified_check(self):
        """ 
        Check if the data file has been modified since the last time 
        it was read.
        """
        if os.path.exists(self.data_file):
            stamp = os.stat(self.data_file).st_mtime
        else:
            print(f"File: {self.data_file} does not exist.")
            return False
        
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            return True
        return False

    def raw_2_collected(self):
        """ 
        Method to control the flow from raw data to parsed to 
        collected. 

        Sets the `collections` attribute.
        """
        if not self.file_modified_check():
            return
        
        raw = self.extract_raw_data()

        # might need in future: `if raw!=self.return_empty():``
        parsed = self.raw_2_parsed(raw)

        # assign the collected data and trigger the `emit`
        self.collection = self.parsed_2_collection(parsed)