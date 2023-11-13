pppp - Pump and Probe Processing Pipeline
=========================================

Two scripts for serial macromolecular crystallography.
Split pump and probe diffraction images according average total scattered intensity.

Requirements: GNU/Linux, Python 3 (e.g. dials.python), qsub, DIALS or CrystFEL.

Before you run
--------------

Open both scripts and set commands in the section 'IMPORTANT SETTING' which can load DIALS and CRYSTFEL on your system - using the variables SOURCE_DIALS and SOURCE_CRYSTFEL.
The default setting works well at Diamond Light Source.

How to use
----------

Example of usage: Open command line, create an empty directory, locate there, load DIALS and execute a command similar to this:

.. code ::

   $ dials.python pppp.py --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ \
                          --files 133451 133452 133453 \
                          --geom /path/to/geometry_refinement/refined.expt \
                          --geom_crystfel /path/to/geometry1.geom

Average total scattered intensity will be calculated using dials.radial_average, it will take several minutes even using a computational cluster.
After finish, you should be able to see a file average_intensity_all.csv with calculated average intensities and histogram average_intensity_all.png. Based on the result, decide what intensity will be your threshold - a value that divides pump and probe data - typically it is around an intensity of 30.
If you specified a geometry file for CrystFEL, you should also see events.lst.

.. image:: README_images/example_gui.gif

Thus, now the data splitting can be actually performed - run the second script while specifying a threshold value:

.. code ::

   $ dials.python pppp2.py --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ \
                          --files 133451 133452 133453 \
                          --geom /path/to/geometry_refinement/refined.expt \
                          --threshold 30

This script will create several files that specify pump and probe groups of diffraction images. Subsequently, they can be then used to run xia2.ssx, CrystFEL or dials.stills_process.

For CrystFEL: events_pump.lst and events_probe.lst

For xia2.ssx: run_xia2.sh that links to run_xia2.phil that links to run_xia2.yml that link to individual metadata .h5 files in subfolders (e.g. /path/to/133451-2/133451-0_dose_point.h5). So specify any other required parameters in run_xia2.phil and you are ready to run using run_xia2.sh

For dials.stills_process: individual files in folders e.g. /path/to/133451-2/probe/run_dials.sh and /path/to/133451-2/probe/run_dials.phil

It is also possible to run automatically xia2.ssx and/or dials.stills_process when other parameters are specified and arguments --xia2 and/or --dials are used:

.. code ::

   $ dials.python pppp2.py --geom /path/to/geometry_refinement/refined.expt \
                           --mask /path/to/mask/pixels3.mask \
                           --pdb /path/to/reference.pdb \
                           --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ \
                           --files 133451 133452 133453 \
                           --spacegroup P21 --cell 50.0 60.0 70.0 90.0 90.0 90.0 --d_min 1.6 \
                           --threshold 30 \
                           --xia2 --dials

All available options can be listed using :code:`--help`:

.. code ::

   $ dials.python pppp.py --help
   usage: pppp.py [-h] --dir PATH --files FILES [FILES ...] --geom GEOM [--sim]

   pppp - Pump and Probe Processing Pipeline - 1st script

   optional arguments:
     -h, --help            show this help message and exit
     --dir PATH, --path PATH
                           Absolute path to the directory with data
     --files FILES [FILES ...]
                           Names of files to be involved in processing
     --geom GEOM           Absolute path to a geometry file for DIALS or xia2
     --geom_crystfel GEOM_CRYSTFEL
                        Absolute path to a geometry file for CrystFEL
     --sim, --simulate     Simulate: create files but not execute qsub jobs


.. code ::

   $ python3 pppp2.py --help
   usage: pppp2.py [-h] --threshold threshold_low [threshold_high ...] --dir PATH [--files FILES [FILES ...]] [--events EVENTS] [--xia2] [--dials] [--geom GEOM] [--pdb PDB] [--mask MASK] [--skip-splitting] [--d_min D_MIN]
                   [--spacegroup spacegroup] [--cell cell_a cell_b cell_c cell_alpha cell_beta cell_gamma] [--sim]

   pppp - Pump and Probe Processing Pipeline - 2nd script - split diffraction images according to the threshold - average total scattered intensity

   options:
     -h, --help            show this help message and exit
     --threshold threshold_low [threshold_high ...]
                           Threshold that divides pump and probe data
     --dir PATH, --path PATH
                           Absolute path to the directory with data
     --files FILES [FILES ...]
                           Names of files to be involved in processing
     --events EVENTS       Absolute path to an events.lst file from CrystFEL - required for generating of pump and probe event.lst files
     --xia2                After splitting the data, run xia2.ssx for data processing
     --dials               After splitting the data, run dials.stills_process and xia2.ssx_reduce for data processing
     --geom GEOM           Absolute path to a geometry file for DIALS and xia2
     --pdb PDB             Absolute path to a reference PDB file
     --mask MASK           Absolute path to a mask file
     --skip-splitting      Skip data splitting, assuming the data have been split already
    --d_min D_MIN, --highres D_MIN
                           High-resolution cutoff
     --spacegroup spacegroup
                           Specify space group
     --cell cell_a cell_b cell_c cell_alpha cell_beta cell_gamma
                           Specify unit cell parameters divided by spaces, e.g. 60 50 40 90 90 90
     --sim, --simulate     Simulate: create files but not execute qsub jobs



   $ dials.python pppp2.py --help
   usage: pppp2.py [-h] --dir PATH --files FILES [FILES ...] [--pdb PDB]
                   [--geom GEOM] [--mask MASK] --threshold threshold_low
                   [threshold_high ...] [--sim] [--just-split] [--just-xia2]
                   [--d_min D_MIN] --spacegroup spacegroup --cell cell_a cell_b
                   cell_c cell_alpha cell_beta cell_gamma

   pppp - Pump and Probe Processing Pipeline - 2nd script

   optional arguments:
     -h, --help            show this help message and exit
     --dir PATH, --path PATH
                           Path to the directory with data
     --files FILES [FILES ...]
                           Names of files to be involved in processing
     --pdb PDB             Reference PDB file
     --geom GEOM           Path to a geometry file
     --mask MASK           Path to a mask file
     --threshold threshold_low [threshold_high ...]
                           Threshold that divides pump and probe data
     --sim, --simulate     Simulate: create files but not execute qsub jobs
     --just-split          Just split the data to groups and not run xia2.ssx
     --just-xia2           Just run xia2.ssx, assuming data have been split
                           already
     --d_min D_MIN, --highres D_MIN
                           High-resolution cutoff
     --spacegroup spacegroup
                           Specify space group
     --cell cell_a cell_b cell_c cell_alpha cell_beta cell_gamma
                           Specify unit cell parameters divided by spaces, e.g.
                           60 50 40 90 90 90


Developed by Martin Maly, `martin.maly@soton.ac.uk <mailto:martin.maly@soton.ac.uk>`_ , (University of Southampton and Diamond Light Source and CCP4]
