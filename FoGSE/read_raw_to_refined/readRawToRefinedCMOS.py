"""
Create a class that will read the LOG file containing raw binary data received from 
FOXSI and parse the data to be readyfor the GUI plotting windows. 

Can read:
    * CMOS
"""

from FoGSE.read_raw_to_refined.readRawToRefinedBase import ReaderBase

from FoGSE.readBackwards import BackwardsReader
from FoGSE.parsers.CMOSparser import PCimageData
from FoGSE.collections.CMOSCollection import CMOSCollection


class CMOSReader(ReaderBase):
    """
    Reader for the FOXSI CMOS instrument.
    """

    def __init__(self, datafile, parent=None):
        """
        Raw : binary
        Parsed : human readable
        Collected : organised by intrumentation
        """
        ReaderBase.__init__(self, datafile, parent)
        # The magic number for CMOS PC data is 590,848. The magic number for CMOS QL data is 492,544.
        self.define_buffer_size(size=590_848)
        self.call_interval(1000)

    def extract_raw_data(self):
        """
        Method to extract the data from `self.data_file` and return the 
        desired data.

        Returns
        -------
        `list` :
            Data read from `self.data_file`.
        """
        return self.extract_raw_data_cmos()
    
    def extract_raw_data_cmos(self):
        """
        Method to extract the CMOS data from `self.data_file` and return the 
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
            Output from the CMOS parser.
        """
        # return or set human readable data
        # do stuff with the raw data and return nice, human readable data
        try:
            linetime, gain, exposure_pc, pc_image = PCimageData(raw_data)
        except ValueError:
            # no data from parser so pass nothing on with a time of -1
            print("No data from parser.")
            linetime, gain, exposure_pc, pc_image = (-1,None,None,None)
        return linetime, gain, exposure_pc, pc_image

    def parsed_2_collection(self, parsed_data):
        """
        Method to move the parsed data to the relevant collection.

        Parameters
        ----------
        parsed_data : `tuple`
            Output from the CMOS parser.

        Returns
        -------
        `FoGSE.detector_collections.CMOSCollection.CMOSCollection` :
            The CMOS collection.
        """
        # take human readable and convert and set to 
        # CdTeCollection(), TimePixCollection(), CMOSCollection()
        col = CMOSCollection(parsed_data, self.old_data_time)
        if col.last_data_time>self.old_data_time:
            self.old_data_time = col.last_data_time
        return col