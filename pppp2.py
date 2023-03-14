import argparse
import os
import sys
from pathlib import Path
import subprocess
import time
import numpy as np
import h5py

# ----------------------------------------------------------------------
# EXAMPLE USAGE
# dials.python pppp2.py --geom /path/to/geometry_refinement/refined.expt \
#     --mask /path/to/mask/pixels3.mask \
#     --pdb /path/to/reference.pdb \
#     --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ \
#     --files 133357-0 133357-1 133357-2 133358-0 133358-1 133358-2 133359-0 133359-1 133359-2 \
#     --spacegroup P21 --cell 50.0 60.0 70.0 90.0 90.0 90.0 --d_min 1.6 \
#     --threshold 30
# ----------------------------------------------------------------------


# https://stackoverflow.com/questions/2785821/is-there-an-easy-way-in-python-to-wait-until-certain-condition-is-true
def wait_until_qjob_finished(job_id, period=5):
    first_cycle = True
    while True:
        p = subprocess.Popen(
            ['qstat', '-j', str(job_id)],# stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8")  # shell=settings["sh"])
        output, err = p.communicate()
        if "Following jobs do not exist or permissions are not sufficient:" in str(output) or "Following jobs do not exist or permissions are not sufficient:" in str(err):
            print("")
            print("Job finished: " + str(job_id))
            return True
        if first_cycle:
            print("")
            print("Still waiting for job  " + str(job_id), end="")
            first_cycle = False
        else:
            print(".", end="")
        time.sleep(period)
    return False


def create_dose_point_h5(threshold_low, threshold_high=None):
    if not threshold_high:
        threshold_high = threshold_low
    with open("radial_average.csv", "r") as f:
        lines = f.readlines()
    if len(lines) == 1:
        lines = lines[0].split()
    if os.path.isfile("pump.txt"): os.remove("pump.txt")
    if os.path.isfile("probe.txt"): os.remove("probe.txt")
    a = np.array([], dtype='i')
    for i, l in enumerate(lines):
        if lines[i].strip() == "":
            continue
        line = lines[i].strip().split(",")
        run = line[0]
        rad_average = float(line[1])
        if rad_average < threshold_low:
            a = np.append(a, 0)
            with open("pump.txt", "a+") as f:
                f.write(run + "\n")
        elif rad_average >= threshold_high:
            a = np.append(a, 1)
            with open("probe.txt", "a+") as f:
                f.write(run + "\n")
        else:
            a = np.append(a, 2)
            with open("not_assigned.txt", "a+") as f:
                f.write(run + "\n")
    print(f"File created: {os.path.basename(os.getcwd())}/pump.txt")
    print(f"File created: {os.path.basename(os.getcwd())}/probe.txt")
    if os.path.isfile("not_assigned.txt"): print(f"File created: {os.path.basename(os.getcwd())}/not_assigned.txt")
    f = h5py.File(os.path.basename(os.getcwd()) + '_dose_point.h5', 'w')
    f.create_dataset("dose_point", data=a)
    f.close()
    print(f"File created: {os.path.basename(os.getcwd())}/{os.path.basename(os.getcwd())}_dose_point.h5")
    return


def run():
    parser = argparse.ArgumentParser(
        description="pppp - Pump and Probe Processing Pipeline - 2nd script"
    )
    parser.add_argument(
        "--dir", "--path",
        help="Path to the directory with data",
        type=str,
        required=True,
        dest="path"
    )
    parser.add_argument(
        "--files",
        help="Names of files to be involved in processing",
        type=str,
        required=True,
        nargs="+"
    )
    parser.add_argument(
        "--pdb",
        help="Reference PDB file",
        type=str,
        #required=True,
    )
    parser.add_argument(
        "--geom",
        help="Path to a geometry file",
        type=str,
        #required=True,
    )
    parser.add_argument(
        "--mask",
        help="Path to a mask file",
        type=str,
        #required=True,
    )
    parser.add_argument(
        "--threshold",
        type=float,
        help="Threshold that divides pump and probe data",
        required=True,
        nargs='+',
        metavar=('threshold_low', 'threshold_high'),
    )
    parser.add_argument(
        "--sim", "--simulate",
        help="Simulate: create files but not execute qsub jobs",
        action="store_true",
        dest="sim",
    )
    parser.add_argument(
        "--just-split",
        help="Just split the data to groups and not run xia2.ssx",
        action="store_true",
        dest="just_split",
    )
    parser.add_argument(
        "--just-xia2",
        help="Just run xia2.ssx, assuming data have been split already",
        action="store_true",
        dest="just_xia2",
    )
    parser.add_argument(
        "--xia2",
        help="Use xia2.ssx for data processing",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--dials",
        help="Use dials.still_process and xia2.ssx_reduce for data processing",
        action="store_true",
    )
    parser.add_argument(
        "--d_min", "--highres",
        type=float,
        help="High-resolution cutoff",
        default=0,
        dest='d_min',
    )
    parser.add_argument(
        "--spacegroup",
        type=str,
        help="Specify space group",
        metavar="spacegroup",
        required=True
    )
    parser.add_argument(
        "--cell",
        type=float,
        nargs=6,
        help="Specify unit cell parameters divided by spaces, e.g. 60 50 40 90 90 90",
        metavar=("cell_a", "cell_b", "cell_c", "cell_alpha", "cell_beta", "cell_gamma"),
        required=True
    )
    args = parser.parse_args()
    if len(args.threshold) == 1:
        threshold_low = args.threshold[0]
        threshold_high = args.threshold[0]
    elif len(args.threshold) == 2:
        threshold_low = args.threshold[0]
        threshold_high = args.threshold[1]
    elif len(args.threshold) > 2:
        sys.exit('Argument --threshold takes one or two values')
    # TO DO     if not args.just_split and not ...

    print("PPPP Pump & Probe Processing Pipeline - step 2")
    cwd = os.getcwd()
    print(f"Working directory: {cwd}")
    print("")

    if not args.just_xia2:
        print(f"Separating images to group using a threshold: {str(threshold_low)} {str(threshold_high)}...")
        for i, f in enumerate(args.files):
            os.chdir(f)
            create_dose_point_h5(threshold_low, threshold_high)
            os.chdir("..")
    if args.just_split:
        print("Done.")
        return

    if args.path[-1] == "/":
        args.path = args.path[:-1]
    f_list = []
    for i, f in enumerate(args.files):
        f_list.append(f"{f}/run{f}")
    f_str = ",".join(f_list)

    if args.xia2:
        #
        # run_xia2.sh
        #
        with open("run_xia2.sh", "w") as r:
            r.write(f"""module load dials/nightly
# source /dls/science/users/FedID/dials/dials
xia2.ssx run_xia2.phil image={args.path}/""" + "{" + f_str + "}.h5")

        #
        # run_xia2.phil
        #
        cell_str = str(args.cell[0]) + " " + str(args.cell[1]) + " " + str(args.cell[2]) + " " + str(args.cell[3]) + " " + str(args.cell[4]) + " " + str(args.cell[5])
        cell_str_comma = str(args.cell[0]) + ", " + str(args.cell[1]) + ", " + str(args.cell[2]) + ", " + str(args.cell[3]) + ", " + str(args.cell[4]) + ", " + str(args.cell[5])
        with open("run_xia2.phil", "w") as r:
            r.write(f"""reference_geometry={args.geom}
mask={args.mask}
spotfinding.min_spot_size=2
spotfinding.max_spot_size=10
space_group={args.spacegroup}
indexing.unit_cell={cell_str}
reference={args.pdb}
grouping=run_xia2.yml""")
            if args.d_min:
                r.write(f"\nd_min={args.d_min}")
    
        #
        # run_xia2.yml
        #
        with open("run_xia2.yml", "w") as r:
            r.write(f"metadata:\n  dose_point:\n")
            for i, f in enumerate(args.files):
                r.write(f'    "{args.path}/{f}/run{f}.h5" : "{os.getcwd()}/{f}/{f}_dose_point.h5:/dose_point"\n')
            r.write("""grouping:
  merge_by:
    values: 
      - dose_point""")

        print(f"Executing xia2.ssh...")
        p = subprocess.Popen(
            ['qsub', '-pe', 'smp', '20', '-q', 'medium.q', 'run_xia2.sh'],# stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8")  # shell=settings["sh"])
        output, err = p.communicate()
        if output:
            print(f"STDOUT: {output}")
        if err:
            print(f"STDERR: {err}")
        job_id = int(output.splitlines()[0].split()[2])


    elif args.dials:
        print(f"Executing dials.still_process jobs...")
        job_ids1 = []
        # run_dials.phil
        run_dials_phil_base = f"""input.reference_geometry={args.geom}
spotfinder.lookup.mask={args.mask}
integration.lookup.mask={args.mask}
spotfinder.filter.min_spot_size=2
spotfinder.filter.max_spot_size=10
significance_filter.enable=True
#significance_filter.isigi_cutoff=1.0
mp.nproc = 20
mp.method=multiprocessing
#refinement.parameterisation.detector.fix=none"""
        run_dials_phil_base += """
indexing {
  known_symmetry {
    space_group = """ + args.spacegroup + """
     unit_cell = """ + cell_str_comma + """
   }
  stills.indexer=stills
  stills.method_list=fft1d real_space_grid_search
  multiple_lattice_search.max_lattices=3
}"""
        if args.d_min:
            run_dials_phil_base += f"\nd_min={args.d_min}\n"

        # run_dials.sh
        with open("run_dials.sh", "w") as r:
            run_dials_sh_base = "module load dials/nightly\n" \
                "dials.stills_process run_dials.phil "

        groups = ["pump", "probe"]
        for i, f in enumerate(args.files):
            os.chdir(f)
            for group in groups:
                with open(f"{group}.txt", "r") as p:
                    images = p.read()
                os.mkdir(group)
                os.chdir(group)
                with open("run_dials.phil", "w") as r:
                    r.write(run_dials_phil_base)
                    for line in pump_images.splitlines():
                        r.write(f"input.image_tag={line}")
                with open("run_dials.sh", "w") as r:
                    r.write(run_dials_sh_base)
                    r.write(f"{args.path}/{f}/run{f}.h5")
                print(f"Executing dials.still_process... {f} {group}")
                p = subprocess.Popen(
                    ['qsub', '-pe', 'smp', '20', 'run_dials.sh'],# stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    encoding="utf-8")  # shell=settings["sh"])
                output, err = p.communicate()
                if output:
                    print(f"STDOUT: {output}")
                if err:
                    print(f"STDERR: {err}")
                job_id = int(output.splitlines()[0].split()[2])
                job_ids1.append(job_id)
                os.chdir("..")
            os.chdir("..")
        print("")
        print(str(job_ids1))
        print("Now you can have a break - time for tea or coffee!")

        job_ids2 = []
        for group in groups:
            os.mkdir(group)
            os.chdir(group)
            # run_ssx_reduce.sh
            with open("run_xia2.sh", "w") as r:
                r.write("module load dials/nightly\n")
                r.write("xia2.ssx_reduce ")
                for i, f in enumerate(args.files):
                    r.write("../" + f + "/" + group + "/idx-*_integrated*.{expt,refl} ")
            print(f"Executing xia2.ssx_reduce... {group}")
            p = subprocess.Popen(
                ['qsub', '-pe', 'smp', '20', '-q', 'medium.q', 'run_xia2.sh'],# stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="utf-8")  # shell=settings["sh"])
            output, err = p.communicate()
            if output:
                print(f"STDOUT: {output}")
            if err:
                print(f"STDERR: {err}")
            job_id = int(output.splitlines()[0].split()[2])
            job_ids2.append(job_id)
        print(str(job_ids2))
    return

if __name__ == "__main__":
    run()
