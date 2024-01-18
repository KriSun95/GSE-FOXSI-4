"""
CMOS collection to handle the read-in CMOS data.
"""

import numpy as np
import matplotlib.pyplot as plt


class QLCMOSCollection:
    """
    A container for CMOS data after being parsed.
    
    Can be used to generate spectrograms or images.
    
    Paramters
    ---------
    parsed_data : `tuple`, length 4
            Contains `linetime`, `gain`, `exposure_pc`, and `pc_images` as 
            returned from the parser.

    old_data_time : `int`, `float`
            The last time of the last data point previously extracted and 
            used. Default is `0` and so should take all data.
            Default: 0
            
    Example
    -------
    with BackwardsReader(file=self.data_file, blksize=self.buffer_size, forward=True) as f:
        data = f.read_block()
        linetime, gain, exposure_pc, pc_image = QLimageData(raw_data)
        
    qlcmos_data = QLCMOSCollection((linetime, gain, exposure_ql, ql_image))
    
    plt.figure(figsize=(12,8))
    qlcmos_data.plot_image()
    plt.show()
    """
    
    def __init__(self, parsed_data, old_data_time=0):
        # bring in the parsed data
        self.linetime, _, _, self._image = parsed_data
        
        # used in the filter to only consider data with times > than this
        self.last_data_time = old_data_time

        if not self.new_array():
            self._image = self.empty()

    def empty(self):
        """ Define what an empty return should be. """
        return np.zeros((480,512))
    
    def new_array(self):
        """ Check if the array is new or a repeat. """
        if self.linetime>self.last_data_time:
            return True
        return False
    
    def image_array(self):
        """
        Method to return the image array of the parser output.

        Returns
        -------
        `np.ndarray` :
            The image array.
        """
        return self._image
    
    def plot_image(self):
        """
        Method to plot the image of the CMOS file.

        Returns
        -------
        `matplotlib.pyplot.imshow`:
            The object which holds the plot.
        """

        i = plt.imshow(self.image_array(), 
                       rasterized=True, 
                       origin="lower")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title("CMOS Image")
        
        return i