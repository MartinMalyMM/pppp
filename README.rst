pppp - Pump and Probe Processing Pipeline
=========================================

Split pump and probe serial MX data (according intensity radial average) and process them using xia2.ssx

Requirements: GNU/Linux, Python 3 (e.g. dials.python), qsub, module load dials/nightly

Example of usage:

.. code ::

   $ dials.python pppp.py --geom /path/to/geometry_refinement/refined.expt \
                          --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ \
                          --files 133451-0 133451-1 133451-2
   $ dials.python pppp2.py --geom /path/to/geometry_refinement/refined.expt \
                           --mask /path/to/mask/pixels3.mask \
                           --pdb /path/to/reference.pdb \
                           --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ \
                           --files 133357-0 133357-1 133357-2 133358-0 133358-1 133358-2 133359-0 133359-1 133359-2 \
                           --spacegroup P21 --cell 50.0 60.0 70.0 90.0 90.0 90.0 --d_min 1.6 \
                           --threshold 30

Other options can be listed using :code:`--help`:

.. code ::

   $ dials.python pppp.py --help
   usage: pppp.py [-h] --dir PATH --files FILES [FILES ...] --geom GEOM [--sim]

   pppp - Pump and Probe Processing Pipeline - 1st script

   optional arguments:
     -h, --help            show this help message and exit
     --dir PATH, --path PATH
                           Path to the directory with data
     --files FILES [FILES ...]
                           Names of files to be involved in processing
     --geom GEOM           Path to a geometry file
     --sim, --simulate     Simulate: create files but not execute qsub jobs


.. code ::

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

Customised installation of DIALS
--------------------------------

Sometimes a current nightly build of DIALS does not support all the required features. Then it is needed to source your customised DIALS installation. To do so, replace in pppp2.py these lines 205-206:

.. code ::

   module load dials/nightly
   $ source /dls/science/users/FedID/dials/dials

with these lines:

.. code ::

   # module load dials/nightly
   source /path/to/your/dials/dials

Developed by Martin Maly, `martin.maly@soton.ac.uk <mailto:martin.maly@soton.ac.uk>`_ , (University of Southampton and Diamond Light Source and CCP4]
