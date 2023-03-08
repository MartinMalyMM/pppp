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

Developed by Martin Maly, `martin.maly@soton.ac.uk <mailto:martin.maly@soton.ac.uk>`_ , (University of Southampton and Diamond Light Source and CCP4]
