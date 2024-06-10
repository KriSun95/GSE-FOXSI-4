"""
A demo to walk through an existing CdTe raw file.
"""

import numpy as np

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication

from FoGSE.telemetry_tools.collections.CdTeCollection import CDTE_STRIP_EDGES_ARCMINUTES
from FoGSE.demos.readRawToRefined_single_cdte import CdTeFileReader
from FoGSE.readers.CdTePCReader import CdTePCReader
from FoGSE.windows.base_windows.BaseWindow import BaseWindow
from FoGSE.windows.base_windows.ImageWindow import Image
from FoGSE.windows.base_windows.LightCurveWindow import LightCurveTwinX

class CdTeWindow(BaseWindow):
    """
    An individual window to display CdTe data read from a file.

    Parameters
    ----------
    data_file : `str` 
        The file to be passed to `FoGSE.readers.CdTePCReader.CdTePCReader()`.
        If given, takes priority over `reader` input.
        Default: None

    reader : instance of `FoGSE.readers.CdTePCReader.BaseReader()`
        The reader already given a file.
        Default: None

    plotting_product : `str`
        String to determine whether an "image", "spectrogram", or "lightcurve" 
        should be shown.
        Default: \"image\"

    image_angle : `int`, `float`, etc.
        The angle of roation for the plot. Positive is anti-clockwise and 
        negative is clockwise.
        Default: 0
    
    update_method : `str`
        Indicates whether the frames (if that is relevant `plotting_product`)
        should be summed continously, unless told otherwise.
        Default: \"integrate\"
    
    name : `str`
        A useful string that can be used as a label.
        Default: \"CdTe\"
        
    colour : `str`
        The colour channel used, if used for the `plotting_product`. 
        Likely from [\"red\", \"green\", \"blue\"].
        Default: \"green\"
    """

    add_box_signal = QtCore.pyqtSignal()
    remove_box_signal = QtCore.pyqtSignal()

    def __init__(self, data_file=None, reader=None, plotting_product="image", image_angle=0, update_method="integrate", name="CdTe", colour="green", colour_twin="red", parent=None):
        
        self.colour_twin = colour_twin

        BaseWindow.__init__(self, 
                            data_file=data_file, 
                            reader=reader, 
                            plotting_product=plotting_product, 
                            image_angle=image_angle, 
                            update_method=update_method, 
                            name=name, 
                            colour=colour, 
                            parent=parent)

    def base_essential_get_reader(self):
        """ Return default reader here. """
        return CdTePCReader
    
    def base_essential_get_name(self):
        """ Define a custom way to get the name. Can be used as a label. """
        _pos = self.name_to_position(self.name)
        self.name = self.name+f": pos#{_pos}"
        self.name = self.name+f": {self.update_method}"
        return self.name
    
    def name_to_position(self, data_file):
        """ CdTe detector focal plane position from file name. """
        for key, item in self.det_and_pos_mapping().items():
            if key in data_file:
                return item
        return "??"
    
    def det_and_pos_mapping(self):
        """ CdTe detectors and their focal plane position mapping. """
        return {"cdte1":5, "cdte2":3, "cdte3":4, "cdte4":2}
    
    def products(self):
        """ Define the products for the class. """
        return {"image":None, "spectrogram":None, "lightcurve":None}
        
    def base_essential_setup_product(self, product):
        """ 
        Given a plotting product (e.g., image, etc.), return a function 
        to set up that product.
        """
        product_setup_map = self.products()

        product_setup_map["image"] = self.image_setup
        product_setup_map["spectrogram"] = self.spectrogram_setup
        product_setup_map["lightcurve"] = self.lightcurve_setup

        return product_setup_map.get(product, None)
    
    def update_product(self, product):
        """ 
        Given a plotting product (e.g., image, etc.), return a function 
        to update that product.
        """
        product_update_map = self.products()

        product_update_map["image"] = self.image_update
        product_update_map["spectrogram"] = self.spectrogram_update
        product_update_map["lightcurve"] = self.lightcurve_update

        return product_update_map.get(product, None)
    
    def image_setup(self):
        """ Sets up the class for an image product. """
        
        self.base_2d_image_settings()

        _cdte_strip_edges = CDTE_STRIP_EDGES_ARCMINUTES
        _no_of_strips = len(_cdte_strip_edges)-1
        self.graphPane = Image(pcolormesh={"x_bins":_cdte_strip_edges, 
                                            "y_bins":_cdte_strip_edges, 
                                            "data_matrix":np.zeros((_no_of_strips, _no_of_strips))}, 
                                rotation=self.image_angle, 
                                keep_aspect=True,
                                custom_plotting_kwargs={"vmin":self.min_val, 
                                                        "vmax":self.max_val, 
                                                        "linewidth":0, 
                                                        "antialiased":True},
                                figure_kwargs={"facecolor":(0.612, 0.671, 0.737, 1)})
        self.add_rotate_frame(color="w", alpha=0.5)

        self.graphPane.add_label((0.0, 0.0), self.name, size=7, color="w", alpha=0.75)

        self.detw, self.deth = _no_of_strips, _no_of_strips
        self.base_update_aspect(aspect_ratio=self.detw/self.deth)

        # set title and labels
        self.graphPane.set_labels(xlabel="", ylabel="", title="")
        
        self.base_2d_image_handling()

    def image_update(self):
        """ Define how the image product should updated. """
        new_frame = self.reader.collection.image_array(area_correction=False)[:,::-1]
        # self.update_method = "fade"
    
        # self.update_method = "integrate" if self.integrate else self.update_method

        self.base_apply_update_style(existing_frame=self.my_array, new_frame=new_frame)
        
        new_im = self.process_image_data()
        self.graphPane.add_plot_data(new_im)

    def spectrogram_setup(self):
        """ Sets up the class for a spectrogram product. """

        self.base_2d_image_settings()

        self.detw, self.deth = 256, 1024
        self.graphPane = Image(imshow={"data_matrix":np.zeros((self.detw, self.deth))}, 
                                custom_plotting_kwargs={"vmin":self.min_val, 
                                                        "vmax":self.max_val, 
                                                        "aspect":2},
                                figure_kwargs={"facecolor":(0.612, 0.671, 0.737, 1)})
        self.base_update_aspect(aspect_ratio=2)
        self.graphPane.update_aspect(aspect_ratio=2)

        self.graphPane.set_labels(xlabel="Strips [Pt:0-127, Al:127-255]", 
                                  ylabel="ADC/Energy", 
                                  title="", 
                                  xlabel_kwargs={"size":7}, 
                                  ylabel_kwargs={"size":7}, 
                                  title_kwargs={"size":0})

        self.base_2d_image_handling()

    def spectrogram_update(self):
        """ Define how the spectrogram product should updated. """
        
        new_frame = self.reader.collection.spectrogram_array(remap=True, 
                                                            nan_zeros=False, 
                                                            cmn_sub=False).T
        print("Min/max CdTe frame1",np.min(new_frame),np.max(new_frame))
        _new_frame_gt0 = new_frame[new_frame>0]
        _new_frame_cap = np.median(_new_frame_gt0) + 2*np.std(_new_frame_gt0)
        new_frame[new_frame>_new_frame_cap] = _new_frame_cap
        print("New Min/max CdTe frame2",np.min(new_frame),np.max(new_frame))
        # self.update_method = "replace"

        # self.update_method = "integrate" if self.integrate else self.update_method

        # update current plotted data with new frame
        self.base_apply_update_style(existing_frame=self.my_array, new_frame=new_frame)
        new_im = self.process_image_data()
        self.graphPane.add_plot_data(new_im)

    def lightcurve_setup(self):
        """ Sets up the class for a time profile product. """
        self.graphPane = LightCurveTwinX(colour=self.colour, colour_twin=self.colour_twin, ylim_twin=[0,1])
        self.layoutMain.addWidget(self.graphPane)
        self.graphPane.set_labels_twin(xlabel="Unixtime", ylabel="Counts", title="",
                                       ylabel_twin="Livetime Frac.", ylabel_twin_kwargs={"size":5}, tick_twin_kwargs={"labelsize":4}, offsetsize_twin=1, 
                                       xlabel_kwargs={"size":5}, ylabel_kwargs={"size":5}, title_kwargs={"size":0}, tick_kwargs={"labelsize":4}, 
                                       offsetsize=1)
        self.graphPane.detw, self.graphPane.deth = 2, 1
        self.graphPane.aspect_ratio = self.graphPane.detw/self.graphPane.deth
        self.detw, self.deth = 256, 1024
        self.base_update_aspect(aspect_ratio=2)

        # some info we'll want later
        self.total_counts = []
        self.frame_livetimes = []

    def lightcurve_update(self):
        """ Define how the time profile product should updated. """
        # defined how to add/append onto the new data arrays
        if self.reader.collection is None:
            return
        self.graphPane.add_plot_data_twin(self.reader.collection.total_counts(),
                                          self.reader.collection.get_frame_fraction_livetime(), 
                                          new_data_x=self.reader.collection.mean_unixtime(), 
                                          replace={"this":[0], "with":[np.nan]})

        self.total_counts.append(self.reader.collection.total_counts())
        self.frame_livetimes.append(self.reader.collection.get_frame_seconds_livetime())

        _l = -len(self.graphPane.plot_data_ys)
        _keep = 1+_l if self.graphPane.plot_data_ys[0]==0 else _l
        self.total_counts = self.total_counts[_keep:]
        self.frame_livetimes = self.frame_livetimes[_keep:]

        # plot the newly updated x and ys
        self.graphPane.manage_plotting_ranges_twin()

    def add_arc_distances(self, **kwargs):
        """ A rectangle to indicate the size of the PC region. """
        if self.plotting_product=="image":
            # cdte_fov = 18.7
            arc_distance_list = [2, 4, 6, 8, 10]
            self.graphPane.draw_arc_distances(arc_distance_list, **kwargs)
            self.has_arc_distances = True

    def remove_arc_distances(self):
        """ Removes rectangle indicating the size of the PC region. """
        if hasattr(self,"has_arc_distances") and (self.plotting_product=="image"):
            self.graphPane.remove_arc_distances()
            del self.has_arc_distances
        
    def add_rotate_frame(self, **kwargs):
        """ A rectangle to indicate image rotation. """
        if self.plotting_product!="image":
            return
        
        self.rect = self.graphPane.draw_extent(**kwargs)

    def remove_rotate_frame(self):
        """ Removes rectangle indicating the image rotation. """
        if hasattr(self,"rect") and (self.plotting_product=="image"):
            self.graphPane.remove_extent()

    def update_rotation(self, image_angle):
        """ Allow the image rotation to be updated whenever. """
        if self.plotting_product!="image":
            return 
        im_array = self.graphPane.im_obj.get_array()
        self.layoutMain.removeWidget(self.graphPane)
        del self.graphPane
        self.image_angle = image_angle
        self.base_essential_setup_product(self.plotting_product)()
        self.graphPane.add_plot_data(im_array)

    def update_background(self, colour):
        """ 
        Update the background image colour. 
        
        E.g., colour=(10,40,80,100))
              colour=\"white\"
              etc.
        """
        self.graphPane.graphPane.axes.set_facecolor(colour)

    def base_essential_update_plot(self):
        """Defines how the plot window is updated. """
        self.update_product(self.plotting_product)()

        self.update()

    def process_image_data(self):
        """
        An extra processing step for the data before it is plotted.
        """
    
        # make sure every colour (axis=2) is normalised between 0--1
        norm = np.quantile(self.my_array, 0.99, axis=(0,1))
        norm[norm==0] = 1 # can't divide by 0
        uf = self.max_val*self.my_array/norm
        uf[uf>self.max_val] = self.max_val

        # allow this all to be looked at if need be
        return uf/np.nanmax(uf)


if __name__=="__main__":
    app = QApplication([])

    # different data files to try
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/CdTeImages/no2022_03/NiFoilAm241/10min/test_20230609a_det03_00012_001"
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/berkeley/prototype_vibe_test/fromBerkeley_postVibeCheckFiles/Am241/test_berk_20230803_proto_Am241_1min_postvibe2_00006_001"
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/berkeley/prototype_vibe_test/fromBerkeley_postVibeCheckFiles/Fe55/test_berk_20230803_proto_Fe55_1min__postvibe2_00008_001"
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/CdTeImages/no2021_05/Am241/1min/test_berk_20230728_det05_00005_001"
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/CdTeImages/no2021_05/Fe55/1min/test_berk_20230728_det05_00006_001"
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/CdTeImages/no2021_05/Cr51/1min/test_berk_20230728_det05_00007_001"
    # datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/berkeley/prototype_vibe_test/vibetest_presinez_berk_20230802_proto_00012_001"
    
    import os
    FILE_DIR = os.path.dirname(os.path.realpath(__file__))
    datafile = FILE_DIR+"/../data/test_berk_20230728_det05_00007_001"
    datafile = "/Users/kris/Downloads/16-2-2024_15-9-8/"
    reader1 = CdTeFileReader(datafile)
    reader2 = CdTePCReader(datafile)

    f0 = CdTeWindow(reader=reader1, plotting_product="spectrogram")
    f1 = CdTeWindow(reader=reader2, plotting_product="image")
    # print(R.collections)
    f0.show()
    f1.show()
    app.exec()
