"""
Create a class that will read the LOG file containing raw binary data received from 
FOXSI and parse the data to be readyfor the GUI plotting windows. 

Can read:
    * CdTe
"""

import struct
import numpy as np
import os

from FoGSE.readers.BaseReader import BaseReader

from FoGSE.readBackwards import BackwardsReader
from FoGSE.telemetry_tools.parsers.CdTeparser import CdTerawalldata2parser
from FoGSE.telemetry_tools.parsers.CdTeframeparser import CdTerawdataframe2parser
from FoGSE.telemetry_tools.collections.CdTeCollection import CdTeCollection
from FoGSE.utils import get_frame_size, get_system_value

class CdTePCReader(BaseReader):
    """
    Reader for the FOXSI CdTe instrument.
    """

    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """
        BaseReader.__init__(self, datafile, parent)
        
        self.define_buffer_size(size=get_frame_size("cdte1", "pc")) # 32_780 bytes
        self.call_interval(get_system_value("gse", "display_settings", "cdte", "pc", "readers", "read_interval"))

    def extract_raw_data(self):
        """
        Method to extract the data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `list` :
            Data read from `self.data_file`.
        """
        return self.extract_raw_data_cdte()
    
    def extract_raw_data_cdte(self):
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
            flags, event_df, all_hkdicts = CdTerawdataframe2parser(raw_data) #CdTerawalldata2parser(raw_data)# 
        except ValueError:
            # no data from parser so pass nothing on with a time of -1
            print("No data from parser.")
            flags, event_df, all_hkdicts = (None,
                                            {'ti':np.array([-1]), 
                                             'unixtime':np.array([-1]), 
                                             'hitnum_al':np.array([-1]), 
                                             'hitnum_pt':np.array([-1]), 
                                             'pseudo_counter':np.array([-1]),
                                             'livetime':np.array([-1])},
                                             None)
        return flags, event_df, all_hkdicts

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
        if parsed_data[1]['ti'][0]==-1:
            return 
        # take human readable and convert and set to 
        # CdTeCollection(), TimePixCollection(), CMOSCollection()
        col = CdTeCollection(parsed_data, 0)#self.old_data_time) #replace the old datat time with 0 to allow even old data trhough if it gets to this stage (come back to this!)
        # print("Old data time: ",self.old_data_time)
        # print("Newest data time:",col.last_data_time)
        if col.latest_data_time>self.old_data_time:
            self.old_data_time = col.latest_data_time
        return col
    
