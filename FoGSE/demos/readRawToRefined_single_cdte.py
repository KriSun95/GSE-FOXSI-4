"""
Reader for an existing raw CdTe data file.
"""

import struct

from FoGSE.demos.CdTerawalldata2parser_existingFile import CdTerawalldata2parser_existingFile
from FoGSE.parsers.CdTeframeparser import CdTerawdataframe2parser
from FoGSE.parsers.CdTeparser import CdTerawalldata2parser
from FoGSE.demos.readRawToRefined_single_det import Reader
from FoGSE.read_raw_to_refined.readRawToRefinedBase import ReaderBase
from FoGSE.collections.CdTeCollection import CdTeCollection
    

class CdTeFileReader(ReaderBase):
    """ A reader for a CdTe data file already obtained. """
    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """
        
        ReaderBase.__init__(self, datafile, parent)
        self.define_buffer_size(size=25_000)
        self._read_counter = 0#28983837-self.buffer_size#-0

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

        This just reads in the whole file but then iterates through the file.

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
                    iterative_unpack=struct.iter_unpack("<I",f.read())
                self.data_unpack = []
                for i,data in enumerate(iterative_unpack):
                    self.data_unpack.append(data[0])
                self.data_len = i
            except FileNotFoundError:
                return self.return_empty() 
        
        if self._read_counter>self.data_len:
            return self.return_empty() 
        
        if (self._read_counter+self.buffer_size)<=self.data_len:
            datalist = self.data_unpack[self._read_counter:(self._read_counter+self.buffer_size)]
        else:
            datalist = self.data_unpack[self._read_counter:]

        # pretend 50% of the buffer size has been written since last read
        self._read_counter += int(self.buffer_size*0.5) 
        print(datalist)
        return datalist
    
    def raw_2_parsed(self, raw_data):
        """ 
        Since `extract_raw_data_cdte` is re-defined then this points 
        to a _slightly_ different parser that will not break if half an 
        event/trigger is in raw data. 
        """
        # return or set human readable data
        # do stuff with the raw data and return nice, human readable data
        try:
            flags, event_df, all_hkdicts =CdTerawdataframe2parser(raw_data)#  CdTerawalldata2parser(raw_data)#CdTerawalldata2parser_existingFile(raw_data)# 
            # print(event_df)
        except ValueError:
            # no data from parser so pass nothing on with a time of -1
            print("No data from parser.")
            flags, event_df, all_hkdicts = (None,{'ti':-1},None)
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
        `FoGSE.detector_collections.CdTeCollection.CdTeCollection` :
            The CdTe collection.
        """
        # take human readable and convert and set to 
        # CdTeCollection(), TimePixCollection(), CMOSCollection()
        col = CdTeCollection(parsed_data, self.old_data_time)
        self.old_data_time = col.last_data_time
        return col
    
    def file_modified_check(self):
        return True
    
