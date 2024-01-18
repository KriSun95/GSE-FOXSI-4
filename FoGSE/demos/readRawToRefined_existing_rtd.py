"""
Create a class that will read the LOG file containing raw binary data received from 
the RTDs
"""

from PyQt6 import QtCore

from FoGSE.readBackwards import BackwardsReader
from FoGSE.parsers.RTDparser import rtdparser
from FoGSE.collections.RTDCollection import RTDCollection
from FoGSE.demos.readRawToRefined_single_det import Reader


class RTDFileReader(Reader):
    """
    Reader for the RTD readout.
    """

    # need to be class variable to connect
    value_changed_collections = QtCore.pyqtSignal()

    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """
        Reader.__init__(self, datafile, parent)
        self.define_buffer_size(size=2_000)
        self.call_interval(1000)
        self._read_counter = 0

    def extract_raw_data(self):
        """
        Method to extract the data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `tuple` :
            (x, y) The new x and y coordinates read from `self.data_file`.
        """
        return self.extract_raw_data_rtd()
    
    def extract_raw_data_rtd(self):
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
        if not hasattr(self,"data_unpack"):
            try:
                with open(self.data_file, 'rb') as f:
                    self.data_unpack = f.read()
            except FileNotFoundError:
                return self.return_empty() 
            
        datalist = self.data_unpack[self._read_counter:(self._read_counter+self.buffer_size)]

        # pretend 50% of the buffer size has been written since last read
        self._read_counter += int(self.buffer_size*0.5) 

        if self._old_data==datalist:
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
        data, errors = rtdparser(file_raw=raw_data)
        return data, errors

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
        col = RTDCollection(parsed_data, self.old_data_time)
        self.old_data_time = col.last_data_time
        if not hasattr(self,"data_start_time"):
            self.data_start_time = col.event['ti'][0]
        return col