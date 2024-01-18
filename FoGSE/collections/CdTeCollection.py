"""
CdTe collection to handle the read-in CdTe data.
"""

from copy import copy 

import numpy as np
import matplotlib.pyplot as plt


class CdTeCollection:
    """
    A container for CdTe data after being parsed.
    
    Can be used to generate spectrograms or images.
    
    Paramters
    ---------
    parsed_data : `tuple`, length 3
            Contains `Flags`, `event_df`, `all_hkdicts` as returned from 
            the parser.

    old_data_time : `int`, `float`
            The last time of the last data point previously extracted and 
            used. Default is `0` and so should take all data.
            Default: 0
            
    Example
    -------
    with readBackwards.BackwardsReader(file=directory+raw_file, blksize=20_000_000, forward=True) as f:
        iterative_unpack=struct.iter_unpack("<I",f.read_block())
        datalist=[]
        for ndata,data in enumerate(iterative_unpack):
            datalist.append(data[0])
        Flags, event_df, all_hkdicts = CdTeparser.CdTerawalldata2parser(datalist)
        
    cdte_data = CdTeCollection((Flags, event_df, all_hkdicts))
    
    plt.figure(figsize=(12,8))
    cdte_data.plot_spectrogram(v=210, remap=True, cmn_sub=True)
    plt.show()
    
    plt.figure(figsize=(8,8))
    cdte_data.plot_image(remap=True, area_correction=True, true_pixel_size=True)
    plt.show()
    """
    
    def __init__(self, parsed_data, old_data_time=0):
        # bring in the parsed data
        _, self.event_dataframe, _ = parsed_data
        
        # define all the strip sizes in CdTe detectors
        self.strip_bins, self.side_strip_bins, self.adc_bins = self.channel_bins()
        
        # for easy remapping of channels
        self.channel_map = self.remap_strip_dict()

        # used in the filter to only consider data with times > than this
        # self.last_data_time = old_data_time
        self.new_entries = self.event_dataframe['ti']>old_data_time
        self.last_data_time = self.event_dataframe['ti'][-1]

        # filter the counts somehow, go for crude single strip right now
        self.f_data = self.filter_counts(event_dataframe=self.event_dataframe)
        
        # get more physical information about detector geometry
        self.strip_width_edges = self.strip_widths()
        self.pixel_area = self.pixel_areas()

    def single_event(self, adc_values_pt, adc_values_al, style:str="simple1"):
        """
        Hosts a number of ways to filter the data and get single count 
        events.

        Paramters
        ---------
        adc_values_pt, adc_values_al : `np.ndarray`, `np.ndarray`
                Contains `Flags`, `event_df`, `all_hkdicts` as returned 
                from the parser.
                
        style : `str`
                Sets the style to be used to obtain single count events.
                Default: 'simple1'

        Returns
        -------
        `tuple`:
            (pt_lower,al_lower), ADC values greater than these entries 
            will be considered for single event selection.
        """
        
        if style=="simple0":
            # not great :(
            pt_min_adc = np.min(adc_values_pt, axis=0)
            al_min_adc = np.min(adc_values_al, axis=0)
            filter_scalar = 0.9
            return filter_scalar*abs(pt_min_adc), filter_scalar*abs(al_min_adc)
        elif style=="simple1":
            # seems to work well and is probably the normal way to do it
            pos_pt = adc_values_pt[adc_values_pt>0]
            pt_min_adc = np.median(pos_pt) + np.std(pos_pt)
            pos_al = adc_values_al[adc_values_al>0]
            al_min_adc = np.median(pos_al) + np.std(pos_al)
            return pt_min_adc, al_min_adc
        elif style=="simple2":
            # takes ages for some reason
            pt_min_adc = np.std(adc_values_pt[adc_values_pt])
            al_min_adc = np.std(adc_values_al[adc_values_al])
            return pt_min_adc, al_min_adc
        elif style=="simple3":
            # same as oldest selection
            return self.get_pt_cmn(), self.get_al_cmn()
        else:
            return 0, 0

    def filter_counts(self, event_dataframe):
        """
        Function to filer the count data.

        Paramters
        ---------
        event_dataframe : numpy structured array
                The numpy structured array returned from the parser 
                containing the CdTe data.

        Returns
        -------
        `dict`:
            Dictionary of the times, adc value, and strip number of all 
            filtered data.
        """

        new = self.new_entries #event_dataframe['ti']>self.last_data_time
        
        if np.all(~new):
            return {'times':self.empty(), 
                    'pt_strip_adc':self.empty(), 
                    'al_strip_adc':self.empty(), 
                    'pt_strips':self.empty(), 
                    'al_strips':self.empty()}

        trig_times = event_dataframe['ti'][new]
        pt = event_dataframe['index_pt'][new]
        al = event_dataframe['index_al'][new]+128
        pt_adc = event_dataframe['adc_cmn_pt'][new]
        al_adc = event_dataframe['adc_cmn_al'][new]

        pt_min_adc, al_min_adc = self.single_event(pt_adc, al_adc, style="simple1")
    
        pt_selection = ((pt<59) | (pt>68)) & (pt_adc>pt_min_adc) & (pt_adc<800)
        al_selection = ((al>131) & (al<252)) & (al_adc>al_min_adc) & (al_adc<800)
        
        # choose single strip events
        single = [True if np.sum(pts)==np.sum(als)==1 else False for pts,als in zip(pt_selection,al_selection)]
        single_trig_times = trig_times[single]
        single = np.array(single)[:,None]

        pt_strip = pt[pt_selection & single]
        al_strip = al[al_selection & single]
        pt_value = pt_adc[pt_selection & single]
        al_value = al_adc[al_selection & single]
        
        # self.last_data_time = event_dataframe['ti'][-1]
        return {'times':single_trig_times, 
                'pt_strip_adc':pt_value, 
                'al_strip_adc':al_value, 
                'pt_strips':pt_strip, 
                'al_strips':al_strip-128}
    
    def channel_bins(self):
        """ Define the strip and ADC bins. """
        strip_bins = np.arange(257)-0.5
        side_strip_bins = np.arange(129)-0.5
        adc_bins = np.arange(1025)-0.5

        return strip_bins, side_strip_bins, adc_bins

    def get_pt_cmn(self):
        """ 
        Put all common modes for the Pt side into the same structure as 
        the ADC-cmn values.
        
        E.g., the cmn are all 'per ASIC' (so 2 for Al for every event) 
        but want structure to give the common mode for each ADC value.
        """
        ptcmn = self.event_dataframe['cmn_pt']
        num = len(ptcmn[:,0])
        return np.concatenate((np.resize(ptcmn[:,0],(64,num)),np.resize(ptcmn[:,1],(64,num))), axis=0).T
    
    def get_al_cmn(self):
        """ 
        Put all common modes for the Al side into the same structure as 
        the ADC-cmn values.
        
        E.g., the cmn are all 'per ASIC' (so 2 for Al for every event) 
        but want structure to give the common mode for each ADC value.
        """
        alcmn = self.event_dataframe['cmn_al']
        num = len(alcmn[:,0])
        return np.concatenate((np.resize(alcmn[:,0],(64,num)),np.resize(alcmn[:,1],(64,num))), axis=0).T

    def add_cmn(self, new_events_index):
        """ 
        The ADC values from the parser where the common mode has been 
        added back in for reference.
        """
        cmn01 = self.get_pt_cmn()
        
        cmn23 = self.get_al_cmn()
        
        add_cmn_pt = self.event_dataframe['adc_cmn_pt']+cmn01
        add_cmn_al = self.event_dataframe['adc_cmn_al']+cmn23
        
        return np.ndarray.flatten(add_cmn_pt[new_events_index]), np.ndarray.flatten(add_cmn_al[new_events_index])
    
    def empty(self):
        """ Define what an empty return should be. """
        return np.array([])
    
    def spectrogram(self, cmn_sub:bool=False):
        """ 
        Spectrogram? 
        
        In space, not time though. Don't think that matters but will 
        someone get annoyed though? 
        
        Parameters
        ----------
            
        cmn_sub : `bool`
            Defines whether the common mode subtraction should be done 
            for the ADC values.
            Default: False

        Returns
        -------
        `np.ndarray`, _, _ :
            Array of the binned histogram.
        """

        new = self.new_entries

        if np.all(~new):
            self.adc_counts_arr, _, _ = np.zeros((len(self.strip_bins)-1, len(self.adc_bins)-1)), self.strip_bins, self.adc_bins
            return

        pt_strips = np.ndarray.flatten(self.event_dataframe['index_pt'][new])
        al_strips = np.ndarray.flatten(self.event_dataframe['index_al'][new])+128
        all_strips = np.concatenate((pt_strips, al_strips))
        
        if cmn_sub:
            pt_adc = np.ndarray.flatten(self.event_dataframe['adc_cmn_pt'][new])
            al_adc = np.ndarray.flatten(self.event_dataframe['adc_cmn_al'][new])
        else:
            pt_adc, al_adc = self.add_cmn(new)
        all_adc = np.concatenate((pt_adc, al_adc))

        #**********************************************************************
        # ******** remove default strip values for quickness just now *********
        default_strip_inds = (all_strips==0) | (all_strips==64) | (all_strips==128) | (all_strips==192)
        all_strips = all_strips[~default_strip_inds]
        all_adc = all_adc[~default_strip_inds]
        #**********************************************************************
        
        self.adc_counts_arr, _, _ = np.histogram2d(all_strips, all_adc, 
                                                   bins=[self.strip_bins,
                                                         self.adc_bins])
        
    def spectrogram_array(self, remap:bool=False, nan_zeros:bool=False, cmn_sub:bool=False):
        """
        Method to get the spectrogram array of the CdTe file.

        Parameters
        ----------
        remap : `bool`
            Set to `True` to remap the strip channels to their physical 
            orientation.
            Default: False
            
        nan_zeros : `bool`
            Defines whether zeros should be replaced with NaNs.
            Default: False
            
        cmn_sub : `bool`
            Defines whether the common mode subtraction should be done 
            for the ADC values.
            Default: False

        Returns
        -------
        `numpy.ndarray` :
            The spectrogram array.
        """
        self.spectrogram(cmn_sub=cmn_sub)
        
        counts = self.remap_strips(counts=self.adc_counts_arr) if remap else self.adc_counts_arr
        
        counts[counts<=0] = np.nan if nan_zeros else counts[counts<=0]

        return counts
        
    def plot_spectrogram(self, v:(float,int)=None, remap:bool=False, nan_zeros:bool=False, cmn_sub:bool=False):
        """
        Method to plot the spectrogram of the CdTe file.

        Parameters
        ----------
        v : `float`, `int`
            Maximum value for the histrogram colourbar.
            
        remap : `bool`
            Set to `True` to remap the strip channels to their physical 
            orientation.
            Default: False
            
        nan_zeros : `bool`
            Defines whether zeros should be replaced with NaNs.
            Default: False
            
        cmn_sub : `bool`
            Defines whether the common mode subtraction should be done 
            for the ADC values.
            Default: False

        Returns
        -------
        `matplotlib.collections.QuadMesh` :
            The object which hold the plot.
        """

        counts = self.spectrogram_array(remap=remap, nan_zeros=nan_zeros, cmn_sub=cmn_sub)
        
        v = 0.8*np.max(counts) if v is None else v
        
        pc = plt.pcolormesh(self.strip_bins, 
                            self.adc_bins, 
                            counts.T, 
                            vmin=0, 
                            vmax=v)
        plt.ylabel("ADC [common mode subtracted]")
        plt.xlabel("Strip [Pt: 0-127, Al: 128-255]")
        plt.colorbar(label="Counts")
        plt.title(f"Spectrogram: CMN Subtracted, Re-map={remap}")
        
        return pc
    
    def image(self, remap:bool=True):
        """
        Method to return the image array of the parser output.

        Parameters
        ----------
        remap : `bool`
            Set to `True` to remap the strip channels to their physical 
            orientation.
            Default: True

        Returns
        -------
        `np.ndarray` :
            The image array.
        """
        
        pt_strips = self.f_data.get('pt_strips', None)
        al_strips = self.f_data.get('al_strips', None)
        
        if remap:
            pt_strips, al_strips = self._remap_strip_values(pt_strips, al_strips)
        
        im, _, _ = np.histogram2d(pt_strips, 
                                  al_strips, 
                                  bins=[self.side_strip_bins,
                                        self.side_strip_bins])
        
        return im
    
    def _remap_strip_values(self, pt_strips, al_strips):
        """ Remap the strip values to their physical location. """
        rpt_strips, ral_strips = [],[]
        for c in range(len(pt_strips)):
            rpt_strips.append(self.channel_map[pt_strips[c]])
            ral_strips.append(self.channel_map[al_strips[c]+128])
        return np.array(rpt_strips), np.array(ral_strips)-128
    
    def _area_correction(self, image):
        """ 
        Correct the image counts array for strip-pixel collecting 
        area. 
        """
        image /= self.pixel_area
        return image
    
    def image_array(self, remap:bool=True, area_correction:bool=True):
        """ obtain the image array with the wanted corrections. """
        im = self.image(remap=remap)
        if area_correction:
            return self._area_correction(im)
        return im
    
    def plot_image(self, remap:bool=True, area_correction:bool=True, true_pixel_size:bool=True):
        """
        Method to plot the image of the CdTe file.

        Parameters
        ----------
            
        remap : `bool`
            Set to `True` to remap the strip channels to their physical 
            orientation.
            Default: True
            
        area_correction : `bool`
            Defines whether the map is corrected for the true, 
            non-uniform strip-pixel collection areas.
            Default: True
            
        true_pixel_size : `bool`
            Defines whether 'pixels' are plotted uniformly (False) or 
            non-uniformly (True).
            Default: True

        Returns
        -------
        `matplotlib.collections.QuadMesh` or `matplotlib.pyplot.imshow`:
            The object which holds the plot depending if 
            `true_pixel_size=True` or `False`, respectivley.
        """

        im = self.image_array(remap=remap, area_correction=area_correction)
        
        if true_pixel_size:
            i = plt.pcolormesh(self.strip_width_edges, 
                               self.strip_width_edges, 
                               im, 
                               rasterized=True)
            u = " [$\mu$m]"
        else:
            i = plt.imshow(im, 
                           rasterized=True, 
                           origin="lower")
            u = " [strip]"
        plt.xlabel("Al"+u)
        plt.ylabel("Pt"+u)
        plt.title(f"Image: Counts, Re-map={remap}")
        
        return i
    
    def remap_strip_dict(self):
        """ 
        Define dictionary for easy remapping of channels to physical 
        location. 
        """
        original_channels = np.arange(256)

        new_channels = copy(original_channels)

        asic0_inds = original_channels<64
        asic1_inds = (64<=original_channels)&(original_channels<128)
        asic2_inds = (128<=original_channels)&(original_channels<192)
        asic3_inds = 192<=original_channels

        new_channels[asic0_inds] = original_channels[asic0_inds][::-1]
        new_channels[asic1_inds] = original_channels[asic1_inds][::-1]
        new_channels[asic2_inds] = original_channels[asic3_inds][::-1]
        new_channels[asic3_inds] = original_channels[asic2_inds][::-1]

        return dict(zip(original_channels, new_channels))
    
    def reverse_rows(self, arr):
        """ Reverse the rows of a 2D numpy array. """
        return arr[::-1,:]

    def remap_strips(self, counts):
        """ Remap a 2D numpy array of the strip data. """

        if np.array_equal(counts, self.empty()):
            return self.empty()
        
        asic0 = counts[:64,:]
        asic1 = counts[64:128,:]
        asic2 = counts[128:192,:]
        asic3 = counts[192:,:]

        asic0_rmap = self.reverse_rows(asic0)
        asic1_rmap = self.reverse_rows(asic1)
        asic2_rmap = self.reverse_rows(asic2)
        asic3_rmap = self.reverse_rows(asic3)

        return np.concatenate((asic0_rmap, asic1_rmap, asic3_rmap, asic2_rmap), axis=0)
    
    def strip_widths(self):
        """ 
        Function to define the physical sizes of the different pitch 
        widths and what to do as they transition. 
        
        Pitch widths are 100, 80, 60 um and the spaced between are 90 
        and 70 um (100/2+80/2 and 80/2+60/2, respectively).
        """
        C = np.arange(29)*100 # ignore channel 28 just now

        B = np.arange(20)*80 

        A = np.arange(16)*60
        
        new_b = B + C[-1] + 50 + 40 # add last value from (C) then half a bin in (C) and half one in (B)
        
        new_a = A + new_b[-1] + 40 + 30
        
        right_a = A[:-1] + new_a[-1] + 60
        right_b = B + right_a[-1] + 30 + 40
        right_c = C + right_b[-1] + 40 + 50
        
        edges = np.concatenate((C,new_b,new_a,right_a,right_b,right_c))
        
        return edges
    
    def pixel_areas(self):
        """ From the pitch widths, get the strip-pixel areas. """
        return np.diff(self.strip_width_edges)[:,None]@np.diff(self.strip_width_edges)[None,:]
    