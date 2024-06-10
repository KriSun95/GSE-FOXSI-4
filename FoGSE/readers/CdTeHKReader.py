"""
Create a class that will read the LOG file containing raw binary data received from 
FOXSI and parse the data to be readyfor the GUI plotting windows. 

Can read:
    * CdTe
"""

import struct
import numpy as np

from FoGSE.readers.BaseReader import BaseReader

from FoGSE.readBackwards import BackwardsReader
from FoGSE.telemetry_tools.parsers.CdTeparser import CdTecanisterhkparser
# from FoGSE.telemetry_tools.parsers.CdTeframeparser import CdTerawdataframe2parser
from FoGSE.telemetry_tools.collections.CdTeHKCollection import CdTeHKCollection
from FoGSE.utils import get_frame_size, get_system_value

class CdTeHKReader(BaseReader):
    """
    Reader for the FOXSI CdTe instrument.
    """

    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """

        if datafile is None:
            return

        BaseReader.__init__(self, datafile, parent)

        self.define_buffer_size(size=get_frame_size("cdte1", "hk")) # 796 bytes
        self.call_interval(get_system_value("gse", "display_settings", "cdte", "hk", "readers", "read_interval"))

    def extract_raw_data(self):
        """
        Method to extract the data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `list` :
            Data read from `self.data_file`.
        """
        return self.extract_raw_data_cdtehk()
    
    def extract_raw_data_cdtehk(self):
        """
        Method to extract the CdTe data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `list` :
            Data read from `self.data_file`.
        """
        # read the file `self.bufferSize` bytes from the end and extract the lines
        # forward=True: reads buffer from the back but doesn't reverse the data 
        try:
            with BackwardsReader(file=self.data_file, blksize=self.buffer_size, forward=True) as f:
                data = f.read_block()
            if self._old_data==data:
                return self.return_empty() 
        except FileNotFoundError:
            return self.return_empty() 
        
        self._old_data = data
        return data

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
            parsed_data, error_flag = CdTecanisterhkparser(raw_data) #CdTerawalldata2parser(raw_data)# 
        except ValueError:
            # no data from parser so pass nothing on with a time of -1
            print("No data from parser.")
            parsed_data, error_flag = ({"status": "N/A","hv_set": "N/A", "write_pointer":"N/A","frame_count": "N/A", "unread_can_frame_count":"N/A"},None)
        return parsed_data, error_flag

    def parsed_2_collection(self, parsed_data):
        """
        Method to move the parsed data to the relevant collection.

        Parameters
        ----------
        parsed_data : `tuple`
            Output from the CdTe parser.

        Returns
        -------
        `FoGSE.telemetry_tools.collections.CdTeCollection.CdTeCollection` :
            The CdTe collection.
        """
        # take human readable and convert and set to 
        # CdTeCollection(), TimePixCollection(), CMOSCollection()
        col = CdTeHKCollection(parsed_data, 0)#self.old_data_time) #replace the old datat time with 0 to allow even old data trhough if it gets to this stage (come back to this!)
        # print("Old data time: ",self.old_data_time)
        # print("Newest data time:",col.last_data_time)
        if col.latest_data_time>self.old_data_time:
            self.old_data_time = col.latest_data_time
        return col