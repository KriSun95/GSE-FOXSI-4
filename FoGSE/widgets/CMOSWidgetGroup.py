"""
A widget to show off CMOS data.
"""
import os

import numpy as np
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,QBoxLayout

from FoGSE.telemetry_tools.collections.CMOSPCCollection import CMOS1_PC_AVE_BACKGROUND, CMOS2_PC_AVE_BACKGROUND
from FoGSE.telemetry_tools.collections.CMOSQLCollection import CMOS1_QL_AVE_BACKGROUND, CMOS2_QL_AVE_BACKGROUND
from FoGSE.widgets.CMOSWidget import CMOSWidget
from FoGSE.widgets.layout_tools.stretch import unifrom_layout_stretch


class AllCMOSView(QWidget):
    def __init__(self, cmos_pc0, cmos_ql0, cmos_pc1, cmos_ql1, cmos_hk0=None, cmos_hk1=None):
        super().__init__()     
        
        # self.setGeometry(100,100,2000,350)
        self.detw, self.deth = 2000,500
        self.setGeometry(100,100,self.detw, self.deth)
        self.setMinimumSize(600,150)
        self.setWindowTitle("All CdTe View")
        self.aspect_ratio = self.detw/self.deth

        # data_file_pc = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example1/cmos.log"
        # data_file_ql = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example2/cmos_ql.log" #QL

        _reflection = -180 # degrees

        cmos_widget = self.get_cmos_widget()
        
        self.f0 = cmos_widget(data_file_pc=cmos_pc0, data_file_ql=cmos_ql0, data_file_hk=cmos_hk0, name=os.path.basename(cmos_pc0), image_angle=180+_reflection, ave_background_frame={"pc":CMOS1_PC_AVE_BACKGROUND, "ql":CMOS1_QL_AVE_BACKGROUND})
        # f0.resize(QtCore.QSize(150, 190))
        _f0 =QHBoxLayout()
        _f0.addWidget(self.f0)

        self.f1 = cmos_widget(data_file_pc=cmos_pc1, data_file_ql=cmos_ql1, data_file_hk=cmos_hk1, name=os.path.basename(cmos_pc1), image_angle=180+_reflection, ave_background_frame={"pc":CMOS2_PC_AVE_BACKGROUND, "ql":CMOS2_QL_AVE_BACKGROUND})
        # f1.resize(QtCore.QSize(150, 150))
        _f1 =QGridLayout()
        _f1.addWidget(self.f1, 0, 0)

        lay = QGridLayout(spacing=0)
        # w.setStyleSheet("border-width: 2px; border-style: outset; border-radius: 10px; border-color: white; background-color: white;")

        lay.addLayout(_f0, 0, 0, 1, 1)
        lay.addLayout(_f1, 0, 1, 1, 1)

        unifrom_layout_stretch(lay, grid=True)

        lay.setContentsMargins(1, 1, 1, 1) # left, top, right, bottom
        lay.setHorizontalSpacing(0)
        lay.setVerticalSpacing(0)
        self.setStyleSheet("border-width: 2px; border-style: outset; border-radius: 10px; border-color: white; background-color: rgba(238, 186, 125, 150);")

        self.setLayout(lay)

        self.f0.ql.base_qwidget_entered_signal.connect(self.f0.ql.add_pc_region)
        self.f0.ql.base_qwidget_entered_signal.connect(self.f1.ql.add_pc_region)
        # f0.ql.add_box_signal.connect(f1.ql.add_rotate_frame)
        
        self.f0.ql.base_qwidget_left_signal.connect(self.f0.ql.remove_pc_region)
        self.f0.ql.base_qwidget_left_signal.connect(self.f1.ql.remove_pc_region)
        # f0.ql.remove_box_signal.connect(f1.ql.remove_rotate_frame)

        self.f1.ql.base_qwidget_entered_signal.connect(self.f0.ql.add_pc_region)
        self.f1.ql.base_qwidget_entered_signal.connect(self.f1.ql.add_pc_region)
        # f1.ql.add_box_signal.connect(f0.ql.add_pc_region)
        # f1.ql.add_box_signal.connect(f0.ql.add_rotate_frame)

        self.f1.ql.base_qwidget_left_signal.connect(self.f0.ql.remove_pc_region)
        self.f1.ql.base_qwidget_left_signal.connect(self.f1.ql.remove_pc_region)
        #f1.ql.remove_box_signal.connect(f0.ql.remove_pc_region)
        # f1.ql.remove_box_signal.connect(f0.ql.remove_rotate_frame)

    def get_cmos_widget(self):
        """ A way the class can be inherited from but use different parsers. """
        return CMOSWidget

    def resizeEvent(self,event):
        """ Define how the widget can be resized and keep the same apsect ratio. """
        super().resizeEvent(event)
        # Create a square base size of 10x10 and scale it to the new size
        # maintaining aspect ratio.
        # image_resize = QtCore.QSize(int(event.size().width()*0.6), int(event.size().height()*0.6))
        # self.image.resize(image_resize)
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
        self.f0.closeEvent(event)
        self.f1.closeEvent(event)
        self.deleteLater()

if __name__=="__main__":
    app = QApplication([])
    
    
    cmos_pc0 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example1/cmos.log"
    cmos_ql0 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example2/cmos_ql.log" #QL
    cmos_pc1 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example1/cmos.log"
    cmos_ql1 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example2/cmos_ql.log" #QL

    
    cmos_pc0 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/feb3/run22/gse/cmos1_pc.log"
    cmos_ql0 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/feb3/run22/gse/cmos1_ql.log"
    cmos_pc1 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/feb3/run22/gse/cmos2_pc.log"
    cmos_ql1 = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/feb3/run22/gse/cmos2_ql.log"
    
    # cmos_pc0 = "/Users/kris/Downloads/PC_check_downlink_new.dat"
    # cmos_ql0 = "/Users/kris/Downloads/QL_check_downlink_new.dat"
    # cmos_pc1 = "/Users/kris/Downloads/PC_check_downlink_new.dat"
    # cmos_ql1 = "/Users/kris/Downloads/QL_check_downlink_new.dat"
    
    
    # w.resize(1000,500)
    w = AllCMOSView(cmos_pc0, cmos_ql0, cmos_pc1, cmos_ql1, cmos_hk0="", cmos_hk1="")
    # w = CMOSWidget(data_file_pc=data_file_pc, data_file_ql=data_file_ql)
    
    w.show()
    app.exec()