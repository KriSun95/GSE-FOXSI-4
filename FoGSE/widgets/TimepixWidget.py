"""
A widget to show off CdTe data.
"""

import numpy as np
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,QBoxLayout

from FoGSE.telemetry_tools.parsers.Timepixparser import FLAG_MESSAGES
from FoGSE.readers.TimepixReader import TimepixReader
from FoGSE.windows.TimepixWindow import TimepixWindow
from FoGSE.widgets.QValueWidget import QValueRangeWidget, QValueCheckWidget, QValueMultiRangeWidget, QValueListWidget
from FoGSE.widgets.layout_tools.stretch import unifrom_layout_stretch
from FoGSE.widgets.layout_tools.spacing import set_all_spacings


class TimepixWidget(QWidget):
    """
    An individual window to display Timepix data read from a file.

    Parameters
    ----------
    data_file : `str` 
        The file to be passed to `FoGSE.readers.TimepixReader.TimepixReader()`.
        Default: None
    """
    def __init__(self, data_file=None, name="Timepix", image_angle=0, parent=None):

        QWidget.__init__(self, parent)
        timepix_parser = self.get_timepix_parsers()
        reader = timepix_parser(datafile=data_file)

        self._default_qvaluewidget_value = "<span>&#129418;</span>" #fox

        self.setWindowTitle(f"{name}")
        self.setStyleSheet("border-width: 2px; border-style: outset; border-radius: 10px; border-color: white; background-color: white;")
        self.detw, self.deth = 198, 100
        self.setGeometry(100,100,self.detw, self.deth)
        # self.setMinimumSize(self.detw, self.deth) # stops the panel from stretching and squeezing when changing times
        self.aspect_ratio = self.detw/self.deth

        # define main layouts for the status window, LED, buttons, times, and plot
        lc_layout = QtWidgets.QGridLayout()

        self.panels = dict() # for all the background panels

        timepix_window = self.get_timepix_windows()
        
        ## for Timepix light curve
        # widget for displaying the automated recommendation
        self._lc_layout = self.layout_bkg(main_layout=lc_layout, 
                                             panel_name="lc_panel", 
                                             style_sheet_string=self._layout_style("white", "white"), grid=True)
        self.lc = timepix_window(reader=reader, name=name)
        self.lc.setStyleSheet("border-width: 0px;")
        self._lc_layout.addWidget(self.lc)

        # need to groupd some of these for the layout
        first_layout = QtWidgets.QGridLayout()
        first_layout_colour = "rgb(53, 108, 117)"
        self._first_layout = self.layout_bkg(main_layout=first_layout, 
                                             panel_name="first_panel", 
                                             style_sheet_string=self._layout_style("white", "white"), grid=True)
        
        bt1 = {"too_low":-np.inf, "nom_low":27-15, "nom_high":27+15, "too_high":np.inf}
        self.bt1 = QValueMultiRangeWidget(name="Board T1", 
                                          value=self._default_qvaluewidget_value, 
                                          condition={"range1":[bt1["nom_low"],bt1["nom_high"],"white"],
                                                     "range2":[bt1["nom_high"],bt1["too_high"],"red"],
                                                     "other":"orange",
                                                     "error":"orange"}, 
                                          border_colour=first_layout_colour,
                                          tool_tip_values={"Board T1":self._default_qvaluewidget_value, "Board T2":self._default_qvaluewidget_value},
                                          name_plus="<sup>*</sup>")
        
        asic0_i = {"too_low":40-10, "too_high":40+10}
        asic_v = {"too_low":-np.inf, "nom_low":1500-300, "nom_high":1500+300, "too_high":np.inf}
        asic_v_cond = {"range1":[asic_v["nom_low"],asic_v["nom_high"],"white"], "range2":[asic_v["nom_high"],asic_v["too_high"],"red"], "other":"orange", "error":"orange"}
        asic0_v_name, asic1_v_name, asic2_v_name, asic3_v_name = "ASIC0 V", "ASIC1 V", "ASIC2 V", "ASIC3 V"
        self.asic0_i = QValueRangeWidget(name="ASIC0 I", value=self._default_qvaluewidget_value, 
                                         condition={"low":asic0_i["too_low"],"high":asic0_i["too_high"]}, 
                                         border_colour=first_layout_colour,
                                         tool_tip_values={"ASIC0 I":self._default_qvaluewidget_value, asic0_v_name:QValueMultiRangeWidget(name=asic0_v_name, value=self._default_qvaluewidget_value, condition=asic_v_cond), 
                                                          "ASIC1 I":self._default_qvaluewidget_value, asic1_v_name:QValueMultiRangeWidget(name=asic1_v_name, value=self._default_qvaluewidget_value, condition=asic_v_cond), 
                                                          "ASIC2 I":self._default_qvaluewidget_value, asic2_v_name:QValueMultiRangeWidget(name=asic2_v_name, value=self._default_qvaluewidget_value, condition=asic_v_cond), 
                                                          "ASIC3 I":self._default_qvaluewidget_value, asic3_v_name:QValueMultiRangeWidget(name=asic3_v_name, value=self._default_qvaluewidget_value, condition=asic_v_cond)},
                                         name_plus="<sup>*</sup>")

        fpga_v1 = {"too_low":-np.inf, "nom_low":3000-500, "nom_high":3000+500, "too_high":np.inf}
        fpga_v2 = {"too_low":-np.inf, "nom_low":2500-500, "nom_high":2500+500, "too_high":np.inf}
        fpga_v2_cond = {"range1":[fpga_v2["nom_low"],fpga_v2["nom_high"],"white"], "range2":[fpga_v2["nom_high"],fpga_v2["too_high"],"red"], "other":"orange", "error":"orange"}
        fpga_v2_name = "FPGA V2"
        self.fpga_v1 = QValueMultiRangeWidget(name="FPGA V1", 
                                              value=self._default_qvaluewidget_value, 
                                              condition={"range1":[fpga_v1["nom_low"],fpga_v1["nom_high"],"white"],
                                                         "range2":[fpga_v1["nom_high"],fpga_v1["too_high"],"red"],
                                                         "other":"orange",
                                                         "error":"orange"}, 
                                              border_colour=first_layout_colour,
                                              tool_tip_values={"FPGA V1":self._default_qvaluewidget_value, fpga_v2_name:QValueMultiRangeWidget(name=fpga_v2_name, value=self._default_qvaluewidget_value, condition=fpga_v2_cond)},
                                              name_plus="<sup>*</sup>")
        
        fpga_t = {"too_low":-np.inf, "nom_low":30-10, "nom_high":30+10, "too_high":np.inf}
        self.fpga_t = QValueMultiRangeWidget(name="FPGA T", 
                                              value=self._default_qvaluewidget_value, 
                                              condition={"range1":[fpga_t["nom_low"],fpga_t["nom_high"],"white"],
                                                         "range2":[fpga_t["nom_high"],fpga_t["too_high"],"red"],
                                                         "other":"orange",
                                                         "error":"orange"}, 
                                              border_colour=first_layout_colour)

        self.mtot = QValueRangeWidget(name="Mean ToT", 
                                      value=self._default_qvaluewidget_value, 
                                      condition={"low":0,"high":np.inf}, 
                                      border_colour=first_layout_colour,
                                      tool_tip_values={"Mean ToT Now":self._default_qvaluewidget_value, "Mean ToT Mean":self._default_qvaluewidget_value, "Mean ToT Median":self._default_qvaluewidget_value, "Mean ToT Max.":self._default_qvaluewidget_value, "Mean ToT Min.":self._default_qvaluewidget_value},
                                      name_plus="<sup>*</sup>")
        self.flx = QValueRangeWidget(name="Flux", 
                                     value=self._default_qvaluewidget_value, 
                                     condition={"low":0,"high":np.inf}, 
                                     border_colour=first_layout_colour,
                                     tool_tip_values={"Flux Now":self._default_qvaluewidget_value, "Flux Mean":self._default_qvaluewidget_value, "Flux Median":self._default_qvaluewidget_value, "Flux Max.":self._default_qvaluewidget_value, "Flux Min.":self._default_qvaluewidget_value},
                                     name_plus="<sup>*</sup>")
        
        _flg_msgs = FLAG_MESSAGES
        _flg_msgs.pop(1, None)
        self.flgs = QValueCheckWidget(name="Flags", 
                                      value=self._default_qvaluewidget_value, 
                                      condition={"acceptable":[([], "white")]}, 
                                      border_colour=first_layout_colour,
                                      tool_tip_values=_flg_msgs,
                                      name_plus="<sup>*</sup>")

        storage = {"too_low":0, "nom_low":1000, "nom_high":3000, "too_high":np.inf}
        storage_cond = {"range1":[storage["nom_low"],storage["nom_high"],"white"], "range2":[storage["too_low"],storage["nom_low"],"red"], "other":"orange", "error":"orange"}
        storage_name = "RPi Remaining Storage"
        self.health = QValueCheckWidget(name="HVPS", 
                                        value=self._default_qvaluewidget_value, 
                                        condition={"acceptable":[("on", "white"), ("off", "red")]}, 
                                        border_colour=first_layout_colour,
                                        tool_tip_values={"HVPS":self._default_qvaluewidget_value, storage_name:QValueMultiRangeWidget(name=storage_name, value=self._default_qvaluewidget_value, condition=storage_cond)},
                                        name_plus="<sup>*</sup>")
        self._first_layout.addWidget(self.bt1, 0, 0, 1, 2) 
        self._first_layout.addWidget(self.asic0_i, 1, 0, 1, 2) 
        self._first_layout.addWidget(self.fpga_v1, 2, 0, 1, 2) 
        self._first_layout.addWidget(self.fpga_t, 3, 0, 1, 2) 
        self._first_layout.addWidget(self.mtot, 4, 0, 1, 2) 
        self._first_layout.addWidget(self.flx, 5, 0, 1, 2) 
        self._first_layout.addWidget(self.flgs, 6, 0, 1, 2) 
        self._first_layout.addWidget(self.health, 7, 0, 1, 2) 
        
        set_all_spacings(self._first_layout)
        # set_all_spacings(self._second_layout)

        self.lc.reader.value_changed_collection.connect(self.all_fields)

        ## all widgets together
        # lc
        global_layout = QGridLayout()
        # global_layout.addWidget(self.lc, 0, 0, 4, 4)
        global_layout.addLayout(lc_layout, 0, 0, 6, 7)

        global_layout.addLayout(first_layout, 0, 7, 6, 3)#,
        # global_layout.addLayout(second_layout, 6, 0, 1, 9)#,

        unifrom_layout_stretch(global_layout, grid=True)
        unifrom_layout_stretch(self._first_layout, grid=True)
        # unifrom_layout_stretch(self._second_layout, grid=True)

        # lc_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom
        self._lc_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom
        self._first_layout.setContentsMargins(0, 0, 0, 0)
        # self._second_layout.setContentsMargins(0, 0, 0, 0)
        # self._second_layout.setSpacing(6)

        # asic_layout.setSpacing(0)
        first_layout.setSpacing(0)
        # second_layout.setSpacing(0)
        # ping_layout.setSpacing(0)
        global_layout.setHorizontalSpacing(0)
        global_layout.setVerticalSpacing(0)
        global_layout.setContentsMargins(0, 0, 0, 0)

        # actually display the layout
        self.setLayout(global_layout)

    def get_timepix_parsers(self):
        """ A way the class can be inherited from but use different parsers. """
        return TimepixReader
    
    def get_timepix_windows(self):
        """ A way the class can be inherited from but use different parsers. """
        return TimepixWindow

    def all_fields(self):
        """ Update the QValueWidgets. """
        t1 = self.lc.reader.collection.get_board_t1()
        self.bt1.update_label(t1)
        self.bt1.update_tool_tip({"Board T1":t1, 
                                  "Board T2":self.lc.reader.collection.get_board_t2()})

        # need to update all keys
        ai = self.lc.reader.collection.get_asic_currents()
        av = self.lc.reader.collection.get_asic_voltages()
        self.asic0_i.update_label(ai[0])
        self.asic0_i.update_tool_tip({"ASIC0 I":ai[0], 
                                      "ASIC0 V":av[0], 
                                      "ASIC1 I":ai[1], 
                                      "ASIC1 V":av[1], 
                                      "ASIC2 I":ai[2], 
                                      "ASIC2 V":av[2], 
                                      "ASIC3 I":ai[3], 
                                      "ASIC3 V":av[3]})

        fv = self.lc.reader.collection.get_fpga_voltages()
        self.fpga_v1.update_label(fv[0])
        self.fpga_v1.update_tool_tip({"FPGA V1":fv[0], "FPGA V2":fv[1]})

        self.fpga_t.update_label(self.lc.reader.collection.get_fpga_temp())

        hvps = self.lc.reader.collection.get_hvps_status()
        self.health.update_label(hvps)
        self.health.update_tool_tip({"HVPS":hvps, 
                                     "RPi Remaining Storage":self.lc.reader.collection.get_storage_fill})

        mtot = self.lc.reader.collection.get_mean_tot()
        mtot_extra = self._get_lc_info(self.lc.mean_tot)
        self.mtot.update_label(mtot)
        self.mtot.update_tool_tip({"Mean ToT Now":mtot, 
                                   "Mean ToT Mean":round(mtot_extra["Mean"], 1), 
                                   "Mean ToT Median":round(mtot_extra["Median"], 1), 
                                   "Mean ToT Max.":mtot_extra["Max."], 
                                   "Mean ToT Min.":mtot_extra["Min."]})

        flx = self.lc.reader.collection.get_flux()
        flx_extra = self._get_lc_info(self.lc.flux)
        self.flx.update_label(flx)
        self.flx.update_tool_tip({"Flux Now":flx, 
                                  "Flux Mean":round(flx_extra["Mean"], 1), 
                                  "Flux Median":round(flx_extra["Median"], 1), 
                                  "Flux Max.":flx_extra["Max."], 
                                  "Flux Min.":flx_extra["Min."]})

        self.flgs.update_label(self.lc.reader.collection.get_flags())

    def _get_lc_info(self, lc_plot):
        """ To update certain fields, we look to the lightcurve information. """
        if len(lc_plot.plot_data_ys)<2:
            return {"Mean":self._default_qvaluewidget_value,
                    "Median":self._default_qvaluewidget_value, 
                    "Max.":self._default_qvaluewidget_value, 
                    "Min.":self._default_qvaluewidget_value}
        elif len(lc_plot.plot_data_ys)==2:
            lc_data = lc_plot.plot_data_ys[1:] 
        else:
            lc_data = lc_plot.plot_data_ys

        return {"Mean":np.nanmean(lc_data),
                "Median":np.nanmedian(lc_data), 
                "Max.":np.nanmax(lc_data), 
                "Min.":np.nanmin(lc_data)}

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
        """ Update the lc aspect ratio (width/height). """
        self.aspect_ratio = aspect_ratio

    def resizeEvent(self,event):
        """ Define how the widget can be resized and keep the same apsect ratio. """
        super().resizeEvent(event)
        # Create a square base size of 10x10 and scale it to the new size
        # maintaining aspect ratio.
        # lc_resize = QtCore.QSize(int(event.size().width()*0.6), int(event.size().height()*0.6))
        # self.lc.resize(lc_resize)
        # ped_resize = QtCore.QSize(int(event.size().width()*0.6), int(event.size().height()*0.4))
        # self.ped.resize(ped_resize)
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
        self.lc.closeEvent(event)
        self.deleteLater()

class  QValueWidgetTest(QWidget):
    """ 
    A test widget class to use QValueWidget. 
    
    Can use this to test any of the ValueWidgets used elsewhere as a 
    testing ground.
    """
    def __init__(self, parent=None):
        """ Initialise a grid on a widget and add different iterations of the QValueWidget widget. """
        QWidget.__init__(self,parent)

        # define layout
        l = QGridLayout()

        # create value widget and add it to the layout
        bt1 = {"too_low":-np.inf, "nom_low":27-15, "nom_hi":27+15, "too_hi":np.inf}
        self.mtot = QValueMultiRangeWidget(name="Board T1", value=np.nan, condition={"range1":[bt1["nom_low"],bt1["nom_hi"],"white"],
                                                                        "range2":[bt1["nom_hi"],bt1["too_hi"],"red"],
                                                                        "other":"orange"})
        l.addWidget(self.mtot, 0, 0) # widget, -y, x
        self.value1 = QValueRangeWidget(name="That", value=6, condition={"low":2,"high":15})
        l.addWidget(self.value1, 0, 1) # widget, -y, x
        self.value2 = QValueListWidget(name="Other", value=9, condition={"acceptable":[1,2,3,4,5,6,7,8,9,10],"unacceptable":[0,11,12,13,14,15,16]})
        l.addWidget(self.value2, 1, 0) # widget, -y, x
        self.value3 = QValueMultiRangeWidget(name="Another", value=50, condition={"range1":[100,3_000,"green"],"range2":[-100,100,"white"],"other":"orange"})
        l.addWidget(self.value3, 1, 1) # widget, -y, x

        # actually display the layout
        self.setLayout(l)

        # test the changing values
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000) # fastest is every millisecond here
        self.timer.timeout.connect(self.cycle_values) # call self.update_plot_data every cycle
        self.timer.start()

    def cycle_values(self):
        """ Add new data, update widget."""
        r0 = np.random.randint(-50,100, size=1)
        r1 = np.random.randint(-50,100, size=1)
        r2 = np.random.randint(-50,100, size=1)
        r3 = np.random.randint(-150,4_000, size=1)
        self.mtot.update_label(r0[0])
        self.value1.update_label(r1[1])
        self.value2.update_label(r2[2])
        self.value3.update_label(r3[0])


if __name__=="__main__":
    app = QApplication([])

    datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/timepix/for_Kris/fake_data_for_parser/example_timepix_frame.bin"
    datafile = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/timepix/for_Kris/fake_data_for_parser/example_timepix_frame_writing.bin"
    
    # w.resize(1000,500)
    w = TimepixWidget(data_file=datafile)
    # w = QValueWidgetTest()
    w.show()
    app.exec()