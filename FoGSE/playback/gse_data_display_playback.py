"""
First go at a full GSE (data viewing only).
"""
from PyQt6.QtWidgets import QApplication

from FoGSE.playback.widgets.CdTePlaybackWidgetGroup import AllPlaybackCdTeView
from FoGSE.playback.widgets.CMOSPlaybackWidgetGroup import AllPlaybackCMOSView
from FoGSE.playback.widgets.TimepixPlaybackWidget import TimepixPlaybackWidget
from FoGSE.playback.widgets.DisplayCommandPlaybackWidget import DisplayCommandPlaybackWidget
from FoGSE.playback.widgets.CatchPlaybackWidget import CatchPlaybackWidget

from FoGSE.io.newest_data import newest_data_dir

from FoGSE.gse_data_display import GSEDataDisplay


class GSEPlaybackDataDisplay(GSEDataDisplay):
    def __init__(self, window_alert=False, parent=None):

        GSEDataDisplay.__init__(self, window_alert=window_alert, parent=parent)

    def get_all_detector_views(self):
        """ A way the class can be inherited from but use different views. """
        return AllPlaybackCdTeView, AllPlaybackCMOSView, TimepixPlaybackWidget, DisplayCommandPlaybackWidget, CatchPlaybackWidget
    
    def get_data_dir(self):
        """ A way the class can be inherited from but use different folders. """
        # return newest_data_dir() 
        # return "/Users/kris/Downloads/March 20 2024/mar20/run10/20-3-2024_17-42-30/"
        # return "/Users/kris/Downloads/feb17_no_cmos/run22/17-2-2024_21-2-23/"
        # return "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/pfrr/March 20 2024/mar20/run5/20-3-2024_16-58-14/"
        # return "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/pfrr/March 20 2024/mar20/run1/20-3-2024_15-50-53/"
        # return "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/pfrr/March 23 2024/run12/23-3-2024_16-37-22/"
        # return "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/usingGSECodeForDetAnalysis/pfrr/March 23 2024/run13/23-3-2024_17-53-39/"
        return "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/launch-campaign/launch-campaign-day8-launch/apr17-launch/run2/17-4-2024_11-41-21/"

if __name__=="__main__":
    import time
    app = QApplication([])

    w = GSEPlaybackDataDisplay(window_alert=True)

    _s = 122
    w.setGeometry(0,0, 12*_s, 8*_s) # 12 to 8
    w.setStyleSheet("border-width: 2px; border-style: outset; border-radius: 10px; border-color: white; background-color: rgba(238, 186, 125, 150);")

    w.show()
    
    app.exec()