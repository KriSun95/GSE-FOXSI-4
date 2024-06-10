"""
A demo to walk through a CMOS PC raw file.
"""
from copy import copy
import numpy as np

from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout

from FoGSE.telemetry_tools.collections.CMOSPCCollection import det_pc_arcminutes
from FoGSE.readers.CMOSPCReader import CMOSPCReader
from FoGSE.windows.base_windows.BaseWindow import BaseWindow
from FoGSE.windows.base_windows.ImageWindow import Image


class CMOSPCWindow(BaseWindow):
    """
    An individual window to display CMOS data read from a file.

    Parameters
    ----------
    data_file : `str` 
        The file to be passed to `FoGSE.readers.CMOSPCReader.CMOSPCReader()`.
        If given, takes priority over `reader` input.
        Default: None

    reader : instance of `FoGSE.readers.CMOSPCReader.BaseReader()`
        The reader already given a file.
        Default: None

    plotting_product : `str`
        String to determine whether an "image" and or <something else> should be shown.
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
        Default: \"CMOS\"
        
    colour : `str`
        The colour channel used, if used for the `plotting_product`. 
        Likely from [\"red\", \"green\", \"blue\"].
        Default: \"green\"
    """

    def __init__(self, data_file=None, reader=None, plotting_product="image", image_angle=0, update_method="integrate", name="CMOS", colour="green", parent=None, ave_background_frame=0):

        BaseWindow.__init__(self, 
                            data_file=data_file, 
                            reader=reader, 
                            plotting_product=plotting_product, 
                            image_angle=image_angle, 
                            update_method=update_method, 
                            name=name, 
                            colour=colour, 
                            parent=parent)
        
        self.ave_background_frame = ave_background_frame

    def base_essential_get_reader(self):
        """ Return default reader here. """
        return CMOSPCReader
    
    def base_essential_get_name(self):
        """ Define a custom way to get the name. Can be used as a label. """
        _pos = self.name_to_position(self.name)
        self.name = self.name+f": PC pos#{_pos}"
        self.name = self.name+f": {self.update_method}"
        return self.name

    def name_to_position(self, data_file):
        """ CMOS detector focal plane position from name. """
        for key, item in self.det_and_pos_mapping().items():
            if key in data_file:
                return item
        return "??"
    
    def det_and_pos_mapping(self):
        """ CMOS detectors and their focal plane position mapping. """
        return {"cmos1":0, "cmos2":1}
    
    def products(self):
        """ Define the products for the class. """
        return {"image":None}
    
    def base_essential_setup_product(self, product):
        """ 
        Given a plotting product (e.g., image, etc.), return a function 
        to set up that product.
        """
        product_setup_map = self.products()

        product_setup_map["image"] = self.image_setup

        return product_setup_map.get(product, None)
    
    def update_product(self, product):
        """ 
        Given a plotting product (e.g., image, etc.), return a function 
        to update that product.
        """
        product_update_map = self.products()

        product_update_map["image"] = self.image_update

        return product_update_map.get(product, None)
    
    def image_setup(self):
        """ Sets up the class for an image product. """

        self.threshold = 60

        self.base_2d_image_settings()

        self.min_val, self.max_val = 0, 4095

        self.detw, self.deth = 768, 384
        self.base_update_aspect(aspect_ratio=self.detw/self.deth)
        self.graphPane = Image(imshow={"data_matrix":np.zeros((self.deth, self.detw))}, 
                               rotation=self.image_angle, 
                               keep_aspect=True,
                               custom_plotting_kwargs={"vmin":0,
                                                       "vmax":1,
                                                       "aspect":self.aspect_ratio,
                                                       "extent":det_pc_arcminutes()},
                                figure_kwargs={"facecolor":(0.612, 0.671, 0.737, 1)})
        self.add_rotate_frame(alpha=0.3)

        self.graphPane.add_label((0.0, 0.0), self.name, size=7, color="w", alpha=0.75)

        self.graphPane.update_aspect(aspect_ratio=self.aspect_ratio)

        self.graphPane.set_labels(xlabel="", ylabel="", title="")

        self.base_2d_image_handling()

    def image_update(self):
        """ Define how the image product should updated. """
        # get the new frame
        new_frame = self.reader.collection.image_array()
        
        # self.update_method = "replace"
        
        # self.update_method = "integrate" if self.integrate else self.update_method

        # update current plotted data with new frame
        self.base_apply_update_style(existing_frame=self.my_array, new_frame=new_frame)

        self.my_array[:,:,self.channel[self.image_colour]] -= self.ave_background_frame
        
        # define self.qImageDetails for this particular image product
        new_im = self.process_image_data()

        self.graphPane.add_plot_data(new_im)

        self.my_array[:,:,self.channel[self.image_colour]] += self.ave_background_frame

    def add_arc_distances(self, **kwargs):
        """ A rectangle to indicate the size of the PC region. """
        if self.plotting_product=="image":
            cmos_x_fov, cmos_y_fov = 12.8, 6.4
            arc_distance_list = [cmos_x_fov/4*1.5, cmos_y_fov/2, cmos_y_fov/4]
            self.graphPane.draw_arc_distances(arc_distance_list, label_pos="left", **kwargs)
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
        
        E.g., colour=(10,40,80,100)
              colour=\"white\"
              etc.
        """
        self.graphPane.graphPane.axes.set_facecolor(colour)

    def base_essential_update_plot(self):
        """ Defines how the plot window is updated. """
        self.update_product(self.plotting_product)()

        self.update()

    def process_image_data(self):
        """
        An extra processing step for the data before it is plotted.
        """

        # make sure everything is normalised between 0--1
        # norm = np.max(self.my_array, axis=(0,1))
        # norm[norm==0] = 1 # can't divide by 0
        uf = copy(self.my_array)
        uf[uf>self.max_val] = self.max_val

        uf[:,:,self.channel[self.image_colour]][uf[:,:,self.channel[self.image_colour]]<self.threshold] = 0
        uf[:,:,self.channel[self.image_colour]][uf[:,:,self.channel[self.image_colour]]>=self.threshold] = 1

        # allow this all to be looked at if need be
        return uf


if __name__=="__main__":
    app = QApplication([])

    # different data files to try
    
    import os
    FILE_DIR = os.path.dirname(os.path.realpath(__file__))
    datafile = FILE_DIR+"/../data/test_berk_20230728_det05_00007_001"
    datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example1/cmos.log"
    # datafile = ""
    datafile ="/Users/kris/Documents/umnPostdoc/general/notes/Obsidian Vault/PC_check_downlink_new.dat"

    # `datafile = FILE_DIR+"/../data/cdte.log"`
    reader = CMOSPCReader(datafile)

    f0 = CMOSPCWindow(reader=reader, plotting_product="image")
    f1 = CMOSPCWindow(reader=reader, plotting_product="image", image_angle=-1)

    w = QWidget()
    lay = QGridLayout(w)
    lay.addWidget(f0, 0, 0)
    lay.addWidget(f1, 0, 1)
    w.resize(1200,500)
    w.show()
    app.exec()