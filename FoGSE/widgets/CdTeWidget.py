"""
A widget to show off CdTe data.
"""
import os

import numpy as np
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,QBoxLayout

from FoGSE.readers.CdTePCReader import CdTePCReader
from FoGSE.readers.CdTeHKReader import CdTeHKReader
from FoGSE.readers.DEReader import DEReader
from FoGSE.windows.CdTeWindow import CdTeWindow
from FoGSE.widgets.QValueWidget import QValueRangeWidget, QValueWidget, QValueTimeWidget, QValueCheckWidget, QValueMultiRangeWidget
from FoGSE.widgets.layout_tools.stretch import unifrom_layout_stretch
from FoGSE.widgets.layout_tools.spacing import set_all_spacings


class CdTeWidget(QWidget):
    """
    An individual window to display CdTe data read from a file.

    Parameters
    ----------
    data_file_pc : `str` 
        The file to be passed to `FoGSE.readers.CdTePCReader.CdTePCReader()`.
        Default: None

    plotting_product : `str`
        String to determine whether an "image" and or "spectrogram" should be shown.
        Default: "image"
    """
    def __init__(self, data_file_pc=None, data_file_hk=None, data_file_de=None, name="CdTe", image_angle=0, parent=None):

        QWidget.__init__(self, parent)
        pc_parser, hk_parser, de_parser = self.get_cdte_parsers()
        reader = pc_parser(datafile=data_file_pc)
        self.reader_hk = hk_parser(datafile=data_file_hk)
        self.reader_de = de_parser(datafile=data_file_de)

        self._default_qvaluewidget_value = "<span>&#129418;</span>" #fox

        self.setWindowTitle(f"{name}")
        self.setStyleSheet("border-width: 2px; border-style: outset; border-radius: 10px; border-color: white; background-color: white;")
        self.detw, self.deth = 50, 50
        self.setMinimumSize(self.detw, self.deth) # stops the panel from stretching and squeezing when changing times
        self.aspect_ratio = self.detw/self.deth

        # define main layouts for the status window, LED, buttons, times, and plot
        image_layout = QtWidgets.QGridLayout()
        ped_layout = QtWidgets.QGridLayout()
        value_layout = QtWidgets.QGridLayout()

        self.panels = dict() # for all the background panels

        cdte_window = self.get_cdte_windows()
        
        ## for CdTe image
        # widget for displaying the automated recommendation
        self._image_layout = self.layout_bkg(main_layout=image_layout, 
                                             panel_name="image_panel", 
                                             style_sheet_string=self._layout_style("white", "white"), grid=True)
        self.image = cdte_window(reader=reader, plotting_product="image", name=name, image_angle=image_angle)
        self.image.setStyleSheet("border-width: 0px;")
        self._image_layout.addWidget(self.image)

        ## for CdTe pedestal
        # widget for displaying the automated recommendation
        self._ped_layout = self.layout_bkg(main_layout=ped_layout, 
                                             panel_name="ped_panel", 
                                             style_sheet_string=self._layout_style("white", "white"), grid=True)
        self.ped = cdte_window(reader=reader, plotting_product="spectrogram", name="", image_angle=image_angle)
        self.lc = cdte_window(reader=reader, plotting_product="lightcurve", name="")
        self.ped.setStyleSheet("border-width: 0px;")
        self._ped_layout.addWidget(self.ped) 
        self.ped_layout = ped_layout

        # status values
        self._value_layout = self.layout_bkg(main_layout=value_layout, 
                                             panel_name="value_panel", 
                                             style_sheet_string=self._layout_style("white", "white"), grid=True)
        # de
        de_layout = QtWidgets.QGridLayout()
        de_layout_colour = "rgb(53, 108, 117)"
        self.de_mode = QValueRangeWidget(name="DE mode", value=self._default_qvaluewidget_value, condition={"low":0,"high":np.inf}, border_colour=de_layout_colour)
        self.de_unixtime = QValueRangeWidget(name="Unixtime", value=self._default_qvaluewidget_value, condition={"low":0,"high":np.inf}, border_colour=de_layout_colour)
        self.canister_mode = QValueTimeWidget(name="Can. Mode", 
                                              value=self._default_qvaluewidget_value, 
                                              time=4000, 
                                              condition=[int, float, np.int64, str], 
                                              border_colour=de_layout_colour,
                                              tool_tip_values={"ASIC VTH":QValueWidget(name="ASIC VTH", value=self._default_qvaluewidget_value), 
                                                               "ASIC DTH":QValueWidget(name="ASIC DTH", value=self._default_qvaluewidget_value), 
                                                               "ASIC Load":QValueWidget(name="ASIC Load", value=self._default_qvaluewidget_value)},
                                              name_plus="<sup>*</sup>")
        self.ping = QValueWidget(name="Ping", value=self._default_qvaluewidget_value, condition={"acceptable":[("", "white")]}, border_colour=de_layout_colour)
        self.hv = QValueCheckWidget(name="HV", value=self._default_qvaluewidget_value, condition={"acceptable":[("0 V","white"), ("60 V","rgb(209, 229, 255)"), ("100 V","rgb(149, 200, 255)"), ("200 V","rgb(90, 170, 255)")]}, border_colour=de_layout_colour)
        de_layout.addWidget(self.de_mode, 0, 0, 1, 2) 
        de_layout.addWidget(self.de_unixtime, 1, 0, 1, 2) 
        de_layout.addWidget(self.canister_mode, 2, 0, 1, 2) 
        de_layout.addWidget(self.ping, 3, 0, 1, 2) 
        de_layout.addWidget(self.hv, 4, 0, 1, 2) 
        # counts
        cts_layout = QtWidgets.QGridLayout()
        cts_layout_colour = "rgb(141, 141, 134)"
        self.cts = QValueRangeWidget(name="<span>&#931;</span> Ct", 
                                     value=self._default_qvaluewidget_value, 
                                     condition={"low":0,"high":np.inf}, 
                                     border_colour=cts_layout_colour,
                                     tool_tip_values={"Ct Now":self._default_qvaluewidget_value, 
                                                      "Ct Mean":self._default_qvaluewidget_value, 
                                                      "Ct Median":self._default_qvaluewidget_value, 
                                                      "Ct Max.":self._default_qvaluewidget_value, 
                                                      "Ct Min.":self._default_qvaluewidget_value},
                                     name_plus="<sup>*</sup>")
        self.ctr = QValueRangeWidget(name="<span>&#931;</span> Ct/s", 
                                     value=self._default_qvaluewidget_value, 
                                     condition={"low":0,"high":np.inf}, 
                                     border_colour=cts_layout_colour,
                                     tool_tip_values={"Ct/s Now":self._default_qvaluewidget_value, 
                                                      "Ct/s Mean":self._default_qvaluewidget_value, 
                                                      "Ct/s Median":self._default_qvaluewidget_value, 
                                                      "Ct/s Max.":self._default_qvaluewidget_value, 
                                                      "Ct/s Min.":self._default_qvaluewidget_value},
                                     name_plus="<sup>*</sup>")
        cts_layout.addWidget(self.cts, 0, 0, 1, 2) 
        cts_layout.addWidget(self.ctr, 1, 0, 1, 2) 
        # strips
        strips_layout = QtWidgets.QGridLayout()
        strips_layout_colour = "rgb(213, 105, 48)"
        self.strips = QValueWidget(name="Mean # det. strips", value="", separator="", border_colour=strips_layout_colour)
        self.strips_al = QValueWidget(name="Pt", value=self._default_qvaluewidget_value, border_colour=strips_layout_colour)
        self.strips_pt = QValueWidget(name="Al", value=self._default_qvaluewidget_value, border_colour=strips_layout_colour)
        strips_layout.addWidget(self.strips, 0, 0, 1, 2) 
        strips_layout.addWidget(self.strips_pt, 1, 0, 1, 2) 
        strips_layout.addWidget(self.strips_al, 2, 0, 1, 2) 
        # frames
        frames_layout = QtWidgets.QGridLayout()
        frames_layout_colour = "rgb(66, 120, 139)"
        self.frames = QValueWidget(name="Time to read [sec]:", value="", separator="", border_colour=frames_layout_colour)
        t_cond = {"range1":[-np.inf,45,"rgb(100,149,237)"], "range2":[45,90,"yellow"], "range3":[90,np.inf,"red"], "other":"orange", "error":"orange"}
        self.frames_t = QValueMultiRangeWidget(name="t", value=self._default_qvaluewidget_value, condition=t_cond, border_colour=frames_layout_colour)
        self.frames_tm1 = QValueMultiRangeWidget(name="t-1", value=self._default_qvaluewidget_value, condition=t_cond, border_colour=frames_layout_colour)
        self._frame_count_value = 0
        frames_layout.addWidget(self.frames, 0, 0, 1, 2) 
        frames_layout.addWidget(self.frames_t, 1, 0, 1, 2) 
        frames_layout.addWidget(self.frames_tm1, 2, 0, 1, 2)
        
        self._value_layout.addLayout(de_layout, 0, 0 , 4, 1) 

        self._value_layout.addLayout(cts_layout, 4, 0, 2, 1) 
        
        self._value_layout.addLayout(strips_layout, 6, 0, 3, 1) 
        self._value_layout.addLayout(frames_layout, 9, 0, 3, 1)
        set_all_spacings(self._value_layout)

        ## all widgets together
        # image
        global_layout = QGridLayout()
        global_layout.addLayout(image_layout, 0, 0, 4, 4)
        global_layout.addLayout(ped_layout, 4, 0, 2, 4)
        global_layout.addLayout(value_layout, 0, 4, 6, 2)

        unifrom_layout_stretch(global_layout, grid=True)

        self._image_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom
        self._ped_layout.setContentsMargins(0, 0, 0, 0)
        self._value_layout.setContentsMargins(0, 0, 0, 0)
        self._value_layout.setSpacing(6)
        strips_layout.setSpacing(0)
        frames_layout.setSpacing(0)
        de_layout.setSpacing(0)
        cts_layout.setSpacing(0)
        global_layout.setHorizontalSpacing(0)
        global_layout.setVerticalSpacing(0)
        global_layout.setContentsMargins(0, 0, 0, 0)

        # actually display the layout
        self.setLayout(global_layout)

        self.image.base_qwidget_entered_signal.connect(self.image.add_arc_distances)
        self.image.base_qwidget_left_signal.connect(self.image.remove_arc_distances)
        # self.ped.mousePressEvent = self._switch2lc # with pure PyQt6 widgets, this works, but...
        self.ped.graphPane.mpl_click_signal.connect(self._switch2lc)
        self.lc.graphPane.mpl_click_signal.connect(self._switch2ped) # with plt, need to be more invlolved
        self.image.reader.value_changed_collection.connect(self.all_fields_from_data)
        self.reader_hk.value_changed_collection.connect(self.all_fields_from_hk)
        self.reader_de.value_changed_collection.connect(self.all_fields_from_de)

    def get_cdte_parsers(self):
        """ A way the class can be inherited from but use different parsers. """
        return CdTePCReader, CdTeHKReader, DEReader
    
    def get_cdte_windows(self):
        """ A way the class can be inherited from but use different parsers. """
        return CdTeWindow

    def all_fields_from_data(self):
        """ 
        Update the:
        * count rate field, 
        """
        # self.canister_mode.update_label(...)
        # self.canister_mode.update_tool_tip({"ASIC VTH":..., 
        #                                     "ASIC DTH":..., 
        #                                     "ASIC Load":...})
        if self.image.reader.collection is None:
            return

        total_counts = self.image.reader.collection.total_counts()
        self.cts.update_label(total_counts)
        _lc_count_info = self._get_lc_count_info()
        self.cts.update_tool_tip({"Ct Now":total_counts, 
                                  "Ct Mean":round(_lc_count_info["Ct Mean"], 1), 
                                  "Ct Median":round(_lc_count_info["Ct Median"], 1), 
                                  "Ct Max.":_lc_count_info["Ct Max."], 
                                  "Ct Min.":_lc_count_info["Ct Min."]})
        
        # delta_time = self.image.reader.collection.delta_time()
        _lc_count_rate_info = self._get_lc_count_rate_info()
        total_count_rate = self.image.reader.collection.total_count_rate()
        self.ctr.update_label(round(total_count_rate, 1))
        self.ctr.update_tool_tip({"Ct/s Now":round(total_count_rate, 1), 
                                  "Ct/s Mean":round(_lc_count_rate_info["Ct/s Mean"], 1), 
                                  "Ct/s Median":round(_lc_count_rate_info["Ct/s Median"], 1), 
                                  "Ct/s Max.":round(_lc_count_rate_info["Ct/s Max."], 1), 
                                  "Ct/s Min.":round(_lc_count_rate_info["Ct/s Min."], 1)})

        self.strips_al.update_label(round(self.image.reader.collection.mean_num_of_al_strips(),1))
        self.strips_pt.update_label(round(self.image.reader.collection.mean_num_of_pt_strips(),1))

        _frame_count = self.image.reader.collection.get_unread_can_frame_count()
        self._frame_count_value = self._frame_count_value+_frame_count if (self._frame_count_value>0) or (_frame_count>0) else self._frame_count_value
        self._frame_count_value = 0 if (self._frame_count_value<0) else self._frame_count_value
        self.frames_t.update_label(self._frame_count_value)
        if hasattr(self, "_old_frames_t"):
            self.frames_tm1.update_label(self._old_frames_t)
        self._old_frames_t = self._frame_count_value
        
    def all_fields_from_hk(self):
        """ 
        Update the:
        * count rate field, 
        """
        # ... = self.reader_hk.collection.something()
        # ... = self.reader_de.collection.something()
        # self.canister_mode.update_label(self.reader_hk.collection.get_status())
        # self.canister_mode.update_tool_tip({"ASIC VTH":..., 
        #                                     "ASIC DTH":..., 
        #                                     "ASIC Load":...})
        self.de_mode.update_label(self.reader_hk.collection.get_status())
        # self.ping.update_label(...)
        self.hv.update_label(self.reader_hk.collection.get_hv_set()) #get_hv_exec

        # _frame_count = self.reader_hk.collection.get_unread_can_frame_count()
        # self.frames_t.update_label(_frame_count)
        # if hasattr(self, "_old_frames_t"):
        #     self.frames_tm1.update_label(self._old_frames_t)
        # self._old_frames_t = _frame_count

    def all_fields_from_de(self):
        """ 
        Update the:
        * count rate field, 
        """
        self.canister_mode.update_label(self.reader_de.collection.get_status())
        # self.canister_mode.update_tool_tip({"ASIC VTH":..., 
        #                                     "ASIC DTH":..., 
        #                                     "ASIC Load":...})
        # self.de_mode.update_label(...)
        self.ping.update_label(self.reader_de.collection.get_ping())
        self.de_unixtime.update_label(str(self.reader_de.collection.get_unixtime())[-6:])
    
        # self.reader_de.collection. methods
        # get_temp(self): get_cpu(self): get_df_gb(self): get_unixtime(self):
        
    def _get_lc_count_info(self):
        """ To update certain fields, we look to the lightcurve information. """
        if len(self.lc.total_counts)==0:
            return {"Ct Mean":self._default_qvaluewidget_value,
                    "Ct Median":self._default_qvaluewidget_value, 
                    "Ct Max.":self._default_qvaluewidget_value, 
                    "Ct Min.":self._default_qvaluewidget_value}
        return {"Ct Mean":np.nanmean(self.lc.total_counts),
                "Ct Median":np.nanmedian(self.lc.total_counts), 
                "Ct Max.":np.nanmax(self.lc.total_counts), 
                "Ct Min.":np.nanmin(self.lc.total_counts)}
    
    def _get_lc_count_rate_info(self):
        """ To update certain fields, we look to the lightcurve information. """
        if len(self.lc.total_counts)==0:
            return {"Ct/s Mean":self._default_qvaluewidget_value,
                    "Ct/s Median":self._default_qvaluewidget_value, 
                    "Ct/s Max.":self._default_qvaluewidget_value, 
                    "Ct/s Min.":self._default_qvaluewidget_value}
        return {"Ct/s Mean":np.nanmean(self.lc.total_counts)/np.nanmean(self.lc.frame_livetimes),
                "Ct/s Median":np.nanmedian(self.lc.total_counts)/np.nanmean(self.lc.frame_livetimes), 
                "Ct/s Max.":np.nanmax(self.lc.total_counts)/np.nanmean(self.lc.frame_livetimes), 
                "Ct/s Min.":np.nanmin(self.lc.total_counts)/np.nanmean(self.lc.frame_livetimes)}
        
    def _switch2lc(self, event=None):
        """ Switch from pedestal to lightcurve. """
        self._ped_layout.removeWidget(self.ped) 
        self.ped_layout.removeWidget(self.ped) 
        self._ped_layout.addWidget(self.lc) 
        self.ped_layout.addWidget(self.lc) 
        self.lc.setStyleSheet("border-width: 0px;")

    def _switch2ped(self, event=None):
        """ Switch from lightcurve to pedestal. """
        self._ped_layout.removeWidget(self.lc) 
        self.ped_layout.removeWidget(self.lc) 
        self._ped_layout.addWidget(self.ped) 
        self.ped_layout.addWidget(self.ped) 
        self.ped.setStyleSheet("border-width: 0px;")

    def layout_bkg(self, main_layout, panel_name, style_sheet_string, grid=False):
        """ Adds a background widget (panel) to a main layout so border, colours, etc. can be controlled. """
        # create panel widget
        self.panels[panel_name] = QtWidgets.QWidget()

        # make the panel take up the main layout 
        main_layout.addWidget(self.panels[panel_name])

        # edit the main layout widget however you like
        self.panels[panel_name].setStyleSheet(style_sheet_string)

        # now return a new, child layout that inherits from the panel widget
        if grid:
            return QtWidgets.QGridLayout(self.panels[panel_name])
        else:
            return QtWidgets.QVBoxLayout(self.panels[panel_name])

    def _layout_style(self, border_colour, background_colour):
        """ Define a global layout style. """
        # return f"border-width: 2px; border-style: outset; border-radius: 10px; border-color: {border_colour}; background-color: {background_colour};"
        return f"border-width: 2px; border-style: outset; border-radius: 0px; border-color: {border_colour}; background-color: {background_colour};"
    
    def update_aspect(self, aspect_ratio):
        """ Update the image aspect ratio (width/height). """
        self.aspect_ratio = aspect_ratio

    def resizeEvent(self,event):
        """ Define how the widget can be resized and keep the same apsect ratio. """
        super().resizeEvent(event)
        if event is None:
            return 
        
        new_size = QtCore.QSize(self.detw, int(self.detw / self.aspect_ratio)) #width, height/(width/height)
        new_size.scale(event.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        self.resize(new_size)

    def closeEvent(self, event):
        """ 
        Runs when widget is close and ensure the `reader` attribute's 
        `QTimer` is stopped so it can be deleted properly. 
        """
        self.image.closeEvent(event)
        self.ped.closeEvent(event)
        self.lc.closeEvent(event)
        self.deleteLater()

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
    
    # import os
    # FILE_DIR = os.path.dirname(os.path.realpath(__file__))
    # datafile = FILE_DIR+"/../data/test_berk_20230728_det05_00007_001"
    # datafile = "/Users/kris/Desktop/test_230306_00001_001_nohk"
    # datafile="/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/calibration/j-sideRootData/usingDAQ/raw2root/backgrounds-20230331-newGrounding/20230331_bkg_00001_001"
    # # datafile = "/Users/kris/Desktop/cdte_20231030.log"
    # # datafile = "/Users/kris/Desktop/cdte_20231030_postsend.log"
    # # datafile = "/Users/kris/Desktop/cdte_20231030_presend.log"
    # datafile = "/Users/kris/Desktop/cdte_20231030_fullread.log"
    # datafile = "/Users/kris/Desktop/cdte_src_mod.log"
    # datafile = "/Users/kris/Desktop/gse_mod.log"
    # datafile = "/Users/kris/Desktop/from_de.log"
    # # datafile = "/Users/kris/Desktop/from_gse.log"
    datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/CdTeTrialsOfParser-20231102/cdte.log"
    # # datafile = ""

    # # `datafile = FILE_DIR+"/../data/cdte.log"`
    # reader = CdTeFileReader(datafile)#CdTeReader(data_file_pc)
    # # reader = CdTeReader(datafile)
    
    # f0 = CdTeWidget(data_file_pc=datafile)
    # _f0 =QGridLayout()
    # _f0.addWidget(f0, 0, 0)

    # f1 = CdTeWidget(data_file_pc=datafile)
    # _f1 =QGridLayout()
    # _f1.addWidget(f1, 0, 0)

    # f2 = CdTeWidget(data_file_pc=datafile)
    # _f2 =QGridLayout()
    # _f2.addWidget(f2, 0, 0)

    # f3 = CdTeWidget(data_file_pc=datafile)
    # _f3 =QGridLayout()
    # _f3.addWidget(f3, 0, 0)
    
    # w = QWidget()
    # lay = QGridLayout(w)
    # w.setStyleSheet("border-width: 2px; border-style: outset; border-radius: 10px; border-color: white; background-color: white;")

    # # lay.addWidget(f0, 0, 0, 1, 1)
    # # lay.addWidget(f1, 0, 1, 1, 1)
    # lay.addLayout(_f0, 0, 0, 1, 1)
    # lay.addLayout(_f1, 0, 1, 1, 1)
    # lay.addLayout(_f2, 0, 2, 1, 1)
    # lay.addLayout(_f3, 0, 3, 1, 1)

    cdte0 = ("/Users/kris/Downloads/16-2-2024_15-9-8/cdte1_pc.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdte1_hk.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdte1_pc.log")
    cdte1 = ("/Users/kris/Downloads/16-2-2024_15-9-8/cdtede_hk.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdte2_hk.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdtede_hk.log")
    cdte2 = ("/Users/kris/Downloads/16-2-2024_15-9-8/cdte3_pc.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdte3_hk.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdtede_hk.log")
    cdte3 = ("/Users/kris/Downloads/16-2-2024_15-9-8/cdte4_pc.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdte4_hk.log", 
             "/Users/kris/Downloads/16-2-2024_15-9-8/cdtede_hk.log")
    
    # w.resize(1000,500)
    w = CdTeWidget(data_file_pc=cdte1[0], data_file_hk=cdte1[1], data_file_de=cdte1[2], name=os.path.basename(cdte1[0]), image_angle=30)
    
    w.show()
    app.exec()