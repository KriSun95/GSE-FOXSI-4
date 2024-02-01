# GSE Live Demo Folder

For live plotting of general FOXSI detectors run:
* `python ./live_demos/demo_foxsi_dets.py <det> <file> <det> <file>`
* E.g.,
`python FoGSE/demos/live_demos/demo_foxsi_dets.py cdte_ped cdte.log cmos_pc cmos.log` will display two windows, one for the CdTe pedestal and one on the CMOS photon counting data.

For live plotting of predefined FOXSI detectors run:
* E.g.,
`python FoGSE/demos/live_demos/demo_auto_foxsi_dets.py` will display the images+pedestals from any CdTe file and QL+PC data from any CMOS files.