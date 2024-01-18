"""
Create a class that will read the LOG file containing raw binary data received from 
the RTDs
"""

# `from PyQt6 import QtCore`

from FoGSE.read_raw_to_refined.readRawToRefinedBase import ReaderBase

from FoGSE.readBackwards import BackwardsReader
from FoGSE.parsers.RTDparser import rtdparser
from FoGSE.collections.RTDCollection import RTDCollection


class RTDReader(ReaderBase):
    """
    Reader for the RTD readout.
    """

    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """
        ReaderBase.__init__(self, datafile, parent)

        self.define_buffer_size(size=84)
        self.call_interval(1_000)

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
        try:
            with BackwardsReader(file=self.data_file, blksize=self.buffer_size, forward=True) as f:
                datalist = f.read_block()

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
        data, errors = rtdparser(file_raw=raw_data)
        return data, errors

    def parsed_2_collection(self, parsed_data):
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
        if col.last_data_time>self.old_data_time:
            self.old_data_time = col.last_data_time
        if not hasattr(self,"data_start_time"):
            self.data_start_time = col.event['ti'][0]
        return col