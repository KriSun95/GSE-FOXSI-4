"""
A demo to walk through an existing CdTe raw file.
"""
import os

from PyQt6.QtWidgets import QApplication

from FoGSE.demos.readRawToRefined_fake_rtd import RTDFileReader
from FoGSE.windows.RTDwindow import RTDWindow

    
# package top-level
DATAFILE = os.path.dirname(os.path.realpath(__file__)) + "/../../../fake_temperatures.txt"

def initiate_gui():
    app = QApplication([])

    R = RTDFileReader(DATAFILE)

    f0 = RTDWindow(reader=R)

    f0.show()
    app.exec()

def initiate_fake_rtds():
    from FoGSE.fake_foxsi.fake_rtds import fake_rtds

    # generate fake data and save to `datafile`
    fake_rtds(DATAFILE, loops=1_000_000)

if __name__=="__main__":

    from multiprocessing import Process

    # fake temps
    p1 = Process(target = initiate_fake_rtds)
    p1.start()
    # live plot
    p2 = Process(target = initiate_gui)
    p2.start()
    p2.join()