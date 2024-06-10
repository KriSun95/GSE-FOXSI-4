"""
Create a class that will read the LOG file containing raw binary data received from 
FOXSI and parse the data to be readyfor the GUI plotting windows. 

Can read:
    * CMOS PC
"""

from FoGSE.readers.BaseReader import BaseReader

from FoGSE.readBackwards import BackwardsReader
import FoGSE.telemetry_tools.parsers.CMOSparser as cmosp
from FoGSE.telemetry_tools.collections.CMOSHKCollection import CMOSHKCollection
from FoGSE.utils import get_frame_size, get_system_value

class CMOSHKReader(BaseReader):
    """
    Reader for the FOXSI CMOS instrument.
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
        
        self.define_buffer_size(size=get_frame_size("cmos1", "hk")) # 536 bytes
        self.call_interval(get_system_value("gse", "display_settings", "cmos", "hk", "readers", "read_interval"))

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
            # gain_mode, exposureQL, exposurePC, repeat_N, repeat_n, gain_even, gain_odd, ncapture = cmosp.exposureParameters(raw_data)
            cmos_init, cmos_training, cmos_setting, cmos_start, cmos_stop = cmosp.operateCMOS(raw_data)
            # ping = cmosp.ping(raw_data)
            # enable_double_command, remove_all_data, reboot, shutdown = cmosp.discreteCommands(raw_data)
            line_time, line_time_at_pps = cmosp.time(raw_data)
            cpu_load_average = cmosp.cpu(raw_data)
            remaining_disk_size = cmosp.disk(raw_data)
            software_status, error_time, error_flag, error_training, data_validity = cmosp.softFpgaStatus(raw_data)
            sensor_temp, fpga_temp = cmosp.temperature(raw_data)
            gain_mode, exposureQL, exposurePC, repeat_N, repeat_n, gain_even, gain_odd, ncapture = cmosp.currentExposureParameters(raw_data)
            write_pointer_position_store_data, read_pointer_position_QL, data_size_QL, read_pointer_position_PC, data_size_PC = cmosp.downlinkData(raw_data)

        except ValueError:
            # no data from parser so pass nothing on with a time of -1
            print("No data from parser.")
            cmos_init, cmos_training, cmos_setting, cmos_start, cmos_stop = None, None, None, None, None
            line_time, line_time_at_pps = None, None
            cpu_load_average = None
            remaining_disk_size = None
            software_status, error_time, error_flag, error_training, data_validity = None, None, None, None, None
            sensor_temp, fpga_temp = None, None
            gain_mode, exposureQL, exposurePC, repeat_N, repeat_n, gain_even, gain_odd, ncapture = None, None, None, None, None, None, None, None
            write_pointer_position_store_data, read_pointer_position_QL, data_size_QL, read_pointer_position_PC, data_size_PC = None, None, None, None, None
        return {"cmos_init":cmos_init, "cmos_training":cmos_training, "cmos_setting":cmos_setting, "cmos_start":cmos_start, "cmos_stop":cmos_stop,
                "line_time": line_time, "line_time_at_pps": line_time_at_pps, 
                "cpu_load_average":cpu_load_average, 
                "remaining_disk_size":remaining_disk_size,
                "software_status":software_status, "error_time":error_time, "error_flag":error_flag, "error_training":error_training, "data_validity":data_validity,
                "sensor_temp":sensor_temp, "fpga_temp":fpga_temp,
                "gain_mode":gain_mode, "exposureQL":exposureQL, "exposurePC":exposurePC, "repeat_N":repeat_N, "repeat_n":repeat_n, "gain_even":gain_even, "gain_odd":gain_odd, "ncapture":ncapture,
                "write_pointer_position_store_data":write_pointer_position_store_data, "read_pointer_position_QL":read_pointer_position_QL, "data_size_QL":data_size_QL, "read_pointer_position_PC":read_pointer_position_PC, "data_size_PC":data_size_PC}

    def parsed_2_collection(self, parsed_data):
        """
        Method to move the parsed data to the relevant collection.

        Parameters
        ----------
        parsed_data : `tuple`
            Output from the CMOS parser.

        Returns
        -------
        `FoGSE.telemetry_tools.collections.CMOSPCCollection.CMOSPCCollection` :
            The CMOS collection.
        """
        # take human readable and convert and set to 
        # CdTeCollection(), TimePixCollection(), CMOSCollection()
        col = CMOSHKCollection(parsed_data, self.old_data_time)
        if col.last_data_time>self.old_data_time:
            self.old_data_time = col.last_data_time
        return col
