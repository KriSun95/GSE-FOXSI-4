"""
RTD collection to handle the read-in RTD data.
"""

import numpy as np

from FoGSE.parsers.RTDparser import numpy_struct


class RTDCollection:
    """
    A container for RTD data after being parsed.
    
    Can be used to generate time series plots.
    
    Paramters
    ---------
    parsed_data : `tuple`, length 2
            Contains `df_values, `df_errors` as returned from the parser.

   old_data_time : `int`, `float`
            The last time of the last data point previously extracted and 
            used. Default is `0` and so should take all data.
            Default: 0
            
    Example
    -------
    ...
    """
    
    def __init__(self, parsed_data, old_data_time=0):
        # bring in the parsed data
        self.event, _ = parsed_data

        # filter data to only include the new stuff
        self.last_data_time = old_data_time
        self.new_entries = self.event['ti']>self.last_data_time
        self.last_data_time = self.event['ti'][-1]

        # collect new data
        self.new_data = self.event.filter(self.new_entries) 