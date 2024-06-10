"""
A demo to walk through a CMOS QL raw file.
"""
from copy import copy
from matplotlib.colors import LogNorm, Normalize, LinearSegmentedColormap
import numpy as np

from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout

from FoGSE.telemetry_tools.collections.CMOSQLCollection import det_ql_arcminutes, CMOS_QL_MASK_ARRAY
from FoGSE.readers.CMOSQLReader import CMOSQLReader
from FoGSE.windows.base_windows.BaseWindow import BaseWindow
from FoGSE.windows.base_windows.ImageWindow import Image

class CMOSQLWindow(BaseWindow):
    """
    An individual window to display CMOS data read from a file.

    Parameters
    ----------
    data_file : `str` 
        The file to be passed to `FoGSE.readers.CMOSQLReader.CMOSQLReader()`.
        If given, takes priority over `reader` input.
        Default: None

    reader : instance of `FoGSE.readers.CMOSQLReader.BaseReader()`
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
        return CMOSQLReader
    
    def base_essential_get_name(self):
        """ Define a custom way to get the name. Can be used as a label. """
        _pos = self.name_to_position(self.name)
        self.name = self.name+f": QL pos#{_pos}"
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

        self.base_2d_image_settings()

        self.min_val, self.max_val = 0, 4095

        self.detw, self.deth = 512, 480
        self.base_update_aspect(aspect_ratio=self.detw/self.deth)
        cmap = LinearSegmentedColormap.from_list("cmos", ("black", "white"), N=255)
        # vmin needs to be <=vmax
        norm = LogNorm(vmin=1e-2, vmax=1) if "cmos1" in self.name else Normalize(vmin=1e-2, vmax=1)
        self.graphPane = Image(imshow={"data_matrix":np.zeros((self.deth, self.detw))}, 
                               rotation=self.image_angle, 
                               keep_aspect=True,
                               custom_plotting_kwargs={"aspect":self.aspect_ratio,
                                                       "extent":det_ql_arcminutes(),
                                                       "norm":norm,
                                                       "cmap":cmap},
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

        _new_im = new_im[:,:,self.channel[self.image_colour]]
        if "cmos1" in self.name:
            vmin = np.min(_new_im[_new_im>0])
            _new_im[_new_im<vmin] = vmin
        else: 
            vmin = 0
        vmax = np.quantile(_new_im, 0.99998)

        self.graphPane.im_obj.set_clim(vmin=vmin, vmax=vmax)

        self.graphPane.add_plot_data(_new_im)

        self.my_array[:,:,self.channel[self.image_colour]] += self.ave_background_frame

    def add_pc_region(self, **kwargs):
        """ A rectangle to indicate the size of the PC region. """
        if self.plotting_product=="image":
            self.draw_pc_rect(**kwargs)

    def remove_pc_region(self):
        """ Removes rectangle indicating the size of the PC region. """
        if hasattr(self,"pc_box") and (self.plotting_product=="image"):
            self.remove_pc_rect()

    def draw_pc_rect(self, **kwargs):
        """ Draw a box for the photon counting region. """
        # from bottom left xs = np.array([160, 352, 352, 160, 160]) # pixels 
        # from bottom left ys = np.array([192, 192, 288, 288, 192]) # pixels

        x_pix_halfwidth, y_pix_halfwidth = (352-160)/2, (288-192)/2
        xs = np.array([-x_pix_halfwidth, x_pix_halfwidth, x_pix_halfwidth, -x_pix_halfwidth, -x_pix_halfwidth]) # pixels, from centre
        ys = np.array([-y_pix_halfwidth, -y_pix_halfwidth, y_pix_halfwidth, y_pix_halfwidth, -y_pix_halfwidth]) # pixels, from centre

        arcsec_per_pix = 4 # binned
        xs *= arcsec_per_pix/60
        ys *= arcsec_per_pix/60

        _plotting_kwargs = {"transform":self.graphPane.affine_transform, "color":"w", "alpha":0.6} | kwargs

        self.pc_box = self.graphPane.im_obj.axes.plot(xs, ys, **_plotting_kwargs)
        self.graphPane.graphPane.fig.canvas.draw()

    def remove_pc_rect(self):
        """ If the photon counting region box is there, remove it. """
        if hasattr(self, "pc_box"):
            line = self.pc_box.pop(0)
            line.remove()
            del self.pc_box
            self.graphPane.graphPane.fig.canvas.draw()

    def add_rotate_frame(self, **kwargs):
        """ A rectangle to indicate image rotation. """
        if self.plotting_product!="image":
            return
        
        self.rect = self.graphPane.draw_extent(**kwargs)

    def add_arc_distances(self, **kwargs):
        """ A rectangle to indicate the size of the PC region. """
        if self.plotting_product=="image":
            cmos_x_fov, cmos_y_fov = 34.1333333, 32
            arc_distance_list = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
            self.graphPane.draw_arc_distances(arc_distance_list, **kwargs)
            self.has_arc_distances = True

    def remove_arc_distances(self):
        """ Removes rectangle indicating the size of the PC region. """
        if hasattr(self,"has_arc_distances") and (self.plotting_product=="image"):
            self.graphPane.remove_arc_distances()
            del self.has_arc_distances

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
        """ Defines how the plot window is updated. """
        self.update_product(self.plotting_product)()

        self.update()

    def process_image_data(self):
        """
        An extra processing step for the data before it is plotted.
        """

        # make sure everything is normalised between 0--1
        # norm = np.max(self.my_array, axis=(0,1))
        # norm = np.quantile(self.my_array, 0.99, axis=(0,1))
        # norm[norm==0] = 1 # can't divide by 0
        uf = copy(self.my_array)#/norm
        uf[uf>self.max_val] = self.max_val

        uf[:,:,self.channel[self.image_colour]] *= CMOS_QL_MASK_ARRAY

        # allow this all to be looked at if need be
        return uf


if __name__=="__main__":
    app = QApplication([])

    # different data files to try
    
    import os
    FILE_DIR = os.path.dirname(os.path.realpath(__file__))
    datafile = FILE_DIR+"/../data/test_berk_20230728_det05_00007_001"
    datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example2/cmos_ql.log"
    datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/pfrr/March 23 2024/run12/23-3-2024_16-37-22/cmos1_ql.log"
    # datafile = ""

    # `datafile = FILE_DIR+"/../data/cdte.log"`
    reader = CMOSQLReader(datafile)

    f0 = CMOSQLWindow(reader=reader, plotting_product="image")
    f1 = CMOSQLWindow(reader=reader, plotting_product="image", image_angle=-10)

    w = QWidget()
    lay = QGridLayout(w)
    lay.addWidget(f0, 0, 0)
    lay.addWidget(f1, 0, 1)
    w.resize(1200,500)
    w.show()
    app.exec()