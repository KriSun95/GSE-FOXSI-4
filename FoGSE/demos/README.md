# GSE Demo Folder

For live plotting of general FOXSI detectors run:
* `python ./live_demos/demo_foxsi_dets.py <det> <file> <det> <file>`
* E.g.,
`python FoGSE/demos/live_demos/demo_foxsi_dets.py cdte_ped cdte.log cmos_pc cmos.log` will display two windows, one for the CdTe pedestal and one on the CMOS photon counting data.

* The `<det>`s supported are: `cdte_ped`, `cdte_im`, `cmos_pc`, `cmos_ql`, `rtd`

This specific folder contains demos for the FOXSI-4 GSE:

* Run `python demo_single_existing_cdte.py` to step through an existing CdTe detector data file and display images and spectrograms.
* Run `python demo_single_live_cdte.py` to read from a currently writing CdTe detector data file and display images and spectrograms.
* Run `python demo_fake_rtd.py` to generate fake RTD data while plotting the new data being written to the generated file.
* Run `python demo_existing_rtd.py` to step through an existing RTD data file and display time profiles.
* Run `python demo_live_rtd.py` to read from a currently writing RTD data file and display time profiles.

This folder contains stand-alone demo examples of the basic GUI creation for each data source expected for FOXSI-4 that will be combined for the full GSE.