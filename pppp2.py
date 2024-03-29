import argparse
import os
import sys
from pathlib import Path
import subprocess
import time
import numpy as np
import h5py

# ----------------------------------------------------------------------
# pppp - X-ray Pump and Probe Processing Pipeline
# 2nd script - split diffraction images according to the threshold - average total scattered intensity
#
# Martin Maly - martin.maly@soton.ac.uk
# https://github.com/MartinMalyMM/pppp
# ----------------------------------------------------------------------
# EXAMPLE USAGE
# dials.python pppp2.py --threshold 30 --files 133357 133358 --dir /path/to/cheetah/ --events /path/to/events.lst
#
# dials.python pppp2.py --threshold 32 35 \
#     --files 133357-0 133357-1 133357-2 133358-0 133358-1 133358-2 133359-0 133359-1 133359-2 \
#     --dir /path/to/cheetah/ \
#     --geom /path/to/refined.expt \
#     --mask /path/to/mask/pixels3.mask \
#     --pdb /path/to/reference.pdb \
#     --spacegroup P21 --cell 50.0 60.0 70.0 90.0 90.0 90.0 --d_min 1.6 \
#     --xia2 --dials
# ----------------------------------------------------------------------
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#            IMPORTANT SETTING - PATH TO DIALS
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
SOURCE_DIALS = "module load dials/nightly"
# SOURCE_DIALS = ""
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


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


def isfile_or_touch(path):
    if os.path.isfile(path):
        print(f"File created: {os.path.basename(os.getcwd())}/{path}")
    else:
        Path(path).touch()
        print(f"File empty:  {os.path.basename(os.getcwd())}/{path}")
    return


def create_dose_point_h5(dir, threshold_low, threshold_high=None, events=None):
    """Creates files for:
       * xia2.ssx: filename_dose_point.h5, run_xia2.sh, run_xia2.phil, run_xia2.yml
       * dials.stills_process: run_dials.sh, run_dials.phil, run_xia2_process.sh
       * CrystFEL: events_pump.lst events_probe.lst events_not_assigned.lst"""
    if not threshold_high:
        threshold_high = threshold_low
    with open("average_intensity.csv", "r") as f:
        lines = f.readlines()
    if len(lines) == 1:
        lines = lines[0].split()
    if os.path.isfile("pump.txt"): os.remove("pump.txt")
    if os.path.isfile("probe.txt"): os.remove("probe.txt")
    if os.path.isfile("not_assigned.txt"): os.remove("not_assigned.txt")
    if events:
        if os.path.isfile("events_pump.lst"): os.remove("events_pump.lst")
        if os.path.isfile("events_probe.lst"): os.remove("events_probe.lst")
        if os.path.isfile("events_not_assigned.lst"): os.remove("events_not_assigned.lst")
        with open(events, "r") as f_events:
            lines_events_all = f_events.readlines()
    a = np.array([], dtype='i')
    for i, l in enumerate(lines):
        if lines[i].strip() == "":
            continue
        line = lines[i].strip().split(",")
        run = line[0]
        rad_average = float(line[1])
        file_h5 = run.split("_")[0].replace("run", "")
        # event = str(int(run.split("_")[1]))
        # line_crystfel = f"{dir}/{file_h5}/run{file_h5}.h5 //{event} \n"
        if i == 0:
            print(f"File {file_h5}")
        if events:
            if i == 0:
                lines_events = list(filter(lambda x:file_h5 in x, lines_events_all))
                print(f"No. of events: {str(len(lines_events))}")
            line_event = lines_events[i]
        if rad_average < threshold_low:
            a = np.append(a, 0)
            with open("pump.txt", "a+") as f:
                f.write(run + "\n")
            if events:
                with open("events_pump.lst", "a+") as f:
                    f.write(line_event)
        elif rad_average >= threshold_high:
            a = np.append(a, 1)
            with open("probe.txt", "a+") as f:
                f.write(run + "\n")
            if events:
                with open("events_probe.lst", "a+") as f:
                    f.write(line_event)
        else:
            a = np.append(a, 2)
            with open("not_assigned.txt", "a+") as f:
                f.write(run + "\n")
            if events:
                with open("events_not_assigned.lst", "a+") as f:
                    f.write(line_event)
    isfile_or_touch("pump.txt")
    isfile_or_touch("probe.txt")
    if os.path.isfile("not_assigned.txt"): print(f"File created: {os.path.basename(os.getcwd())}/not_assigned.txt")
    if events:
        isfile_or_touch("events_pump.lst")
        isfile_or_touch("events_probe.lst")
        if os.path.isfile("events_not_assigned.lst"): print(f"File created: {os.path.basename(os.getcwd())}/events_not_assigned.lst")
    f = h5py.File(os.path.basename(os.getcwd()) + '_dose_point.h5', 'w')
    f.create_dataset("dose_point", data=a)
    f.close()
    print(f"File created: {os.path.basename(os.getcwd())}/{os.path.basename(os.getcwd())}_dose_point.h5")
    print("")
    return


def run():
    parser = argparse.ArgumentParser(
        description="pppp - Pump and Probe Processing Pipeline - 2nd script - split diffraction images according to the threshold - average total scattered intensity"
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
        "--dir", "--path",
        help="Absolute path to the directory with data",
        type=str,
        required=True,
        dest="path"
    )
    parser.add_argument(
        "--files",
        help="Names of files to be involved in processing",
        type=str,
        # required=True,
        nargs="+"
    )
    parser.add_argument(
        "--events",
        help="Absolute path to an events.lst file from CrystFEL - required for generating of pump and probe event.lst files",
        type=str,
    )
    parser.add_argument(
        "--xia2",
        help="After splitting the data, run xia2.ssx for data processing",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--dials",
        help="After splitting the data, run dials.stills_process and xia2.ssx_reduce for data processing",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--geom",
        help="Absolute path to a geometry file for DIALS and xia2",
        type=str,
        #required=True,
    )
    parser.add_argument(
        "--pdb",
        help="Absolute path to a reference PDB file",
        type=str,
        #required=True,
    )
    parser.add_argument(
        "--mask",
        help="Absolute path to a mask file",
        type=str,
        #required=True,
    )
    parser.add_argument(
        "--skip-splitting",
        help="Skip data splitting, assuming the data have been split already",
        action="store_true",
        dest="skip_splitting",
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
        # required=True
    )
    parser.add_argument(
        "--cell",
        type=float,
        nargs=6,
        help="Specify unit cell parameters divided by spaces, e.g. 60 50 40 90 90 90",
        metavar=("cell_a", "cell_b", "cell_c", "cell_alpha", "cell_beta", "cell_gamma"),
        # required=True
    )
    parser.add_argument(
        "--sim", "--simulate",
        help="Simulate: create files but not execute qsub jobs",
        action="store_true",
        dest="sim",
    )
    args = parser.parse_args()

    print("PPPP Pump & Probe Processing Pipeline - step 2")
    print("2nd script - split diffraction images according to the threshold - average total scattered intensity")
    cwd = os.getcwd()
    print(f"Working directory: {cwd}")
    print("")

    if len(args.threshold) == 1:
        threshold_low = args.threshold[0]
        threshold_high = args.threshold[0]
    elif len(args.threshold) == 2:
        threshold_low = args.threshold[0]
        threshold_high = args.threshold[1]
    elif len(args.threshold) > 2:
        sys.exit('Argument --threshold takes one or two values')
    # TO DO     if not args.just_split and not ...

    if args.files:
        # add -0 -1 -2 if not put in --files argument
        files_are_full_list = True
        for file in args.files:
            if file[-2] != "-":
                files_are_full_list = False
        if files_are_full_list:
            files = args.files
        else:
            files = []
            for file in args.files:
                files.append(file + "-0")
                files.append(file + "-1")
                files.append(file + "-2")
    else:
        files = [ f.path for f in os.scandir(".") if f.is_dir() ]
        for i, f in enumerate(files):
            files[i] = files[i].replace(".", "")
            files[i] = files[i].replace("/", "")

    if args.path[-1] == "/":
        args.path = args.path[:-1]

    events_pump_merge = []
    events_probe_merge = []
    if not args.skip_splitting:
        print(f"Separating images to groups using a threshold: {str(threshold_low)} {str(threshold_high)}...")
        for i, f in enumerate(files):
            os.chdir(f)
            events = None
            if args.events:
                events = args.events
            create_dose_point_h5(args.path, threshold_low, threshold_high, events)
            if args.events:
                with open("events_pump.lst", "r") as events_pump_lst:
                    events_pump_lines = events_pump_lst.readlines()
                with open("events_probe.lst", "r") as events_probe_lst:
                    events_probe_lines = events_probe_lst.readlines()
                events_pump_merge = events_pump_merge + events_pump_lines
                events_probe_merge = events_probe_merge + events_probe_lines
            os.chdir("..")
    if args.events:
        with open("events_pump.lst", "w") as f:
            f.write(''.join(events_pump_merge))
        with open("events_probe.lst", "w") as f:
            f.write(''.join(events_probe_merge))

    #
    # Create run_xia2.yml
    #
    with open("run_xia2.yml", "w") as r:
        r.write(f"metadata:\n  dose_point:\n")
        for i, f in enumerate(files):
            r.write(f'    "{args.path}/{f}/run{f}.h5" : "{os.getcwd()}/{f}/{f}_dose_point.h5:/dose_point"\n')
        r.write("""grouping:
  merge_by:
    values: 
      - dose_point""")

    f_list = []
    for i, f in enumerate(files):
        f_list.append(f"{f}/run{f}")
    f_str = ",".join(f_list)

    #
    # Create run_xia2.sh
    #
    with open("run_xia2.sh", "w") as r:
        r.write(f"""{SOURCE_DIALS}
xia2.ssx run_xia2.phil image={args.path}/""" + "{" + f_str + "}.h5")

    #
    # Create run_xia2.phil
    #
    with open("run_xia2.phil", "w") as r:
        r.write(f"""spotfinding.min_spot_size=2
spotfinding.max_spot_size=10
grouping=run_xia2.yml""")
        if args.geom: r.write(f"\nreference_geometry={args.geom}")
        if args.mask: r.write(f"\nmask={args.mask}")
        if args.spacegroup: r.write(f"\nspace_group={args.spacegroup}")
        if args.geom: r.write(f"\nreference={args.pdb}")
        if args.d_min: r.write(f"\nd_min={args.d_min}")
        if args.cell:
            cell_str = str(args.cell[0]) + " " + str(args.cell[1]) + " " + str(args.cell[2]) + " " + str(args.cell[3]) + " " + str(args.cell[4]) + " " + str(args.cell[5])
            cell_str_comma = str(args.cell[0]) + ", " + str(args.cell[1]) + ", " + str(args.cell[2]) + ", " + str(args.cell[3]) + ", " + str(args.cell[4]) + ", " + str(args.cell[5])
            r.write(f"\nindexing.unit_cell={cell_str}")

    #
    # Create run_dials.phil
    #
    run_dials_phil_base = f"""spotfinder.filter.min_spot_size=2
spotfinder.filter.max_spot_size=10
#significance_filter.enable=True
#significance_filter.isigi_cutoff=1.0
mp.nproc = 20
mp.method=multiprocessing
#refinement.parameterisation.detector.fix=none"""
    if args.geom: run_dials_phil_base += f"\ninput.reference_geometry={args.geom}"
    if args.mask:
        run_dials_phil_base += f"\nspotfinder.lookup.mask={args.mask}"
        run_dials_phil_base += f"\nintegration.lookup.mask={args.mask}"
    run_dials_phil_base += """
indexing {
  stills.indexer=stills
  stills.method_list=fft1d real_space_grid_search
  multiple_lattice_search.max_lattices=3"""
    if args.spacegroup and args.cell:
        run_dials_phil_base += """
  known_symmetry {
    space_group = """ + args.spacegroup + """
     unit_cell = """ + cell_str_comma + """
  }"""
    run_dials_phil_base += "\n}"
    if args.d_min:
        run_dials_phil_base += f"\nspotfinder.filter.d_min={args.d_min}\n"

    #
    # Create run_dials.sh
    #
    with open("run_dials.sh", "w") as r:
        run_dials_sh_base = f"{SOURCE_DIALS}\n" \
            "dials.stills_process run_dials.phil "
    groups = ["pump", "probe"]
    for i, f in enumerate(files):
        os.chdir(f)
        for group in groups:
            with open(f"{group}.txt", "r") as p:
                images = p.read()
            os.mkdir(group)
            os.chdir(group)
            with open("run_dials.phil", "w") as r:
                r.write(run_dials_phil_base)
                for line in images.splitlines():
                    r.write(f"input.image_tag={line}\n")
            with open("run_dials.sh", "w") as r:
                r.write(run_dials_sh_base)
                r.write(f"{args.path}/{f}/run{f}.h5")
            os.chdir("..")
        os.chdir("..")

    # if args.just_split:
    #     print("Done.")
    #     return

    if args.xia2:
        print(f"Executing xia2.ssx...")
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

    if args.dials:
        print(f"Executing dials.stills_process jobs...")
        job_ids1 = []
        for i, f in enumerate(files):
            os.chdir(f)
            for group in groups:
                os.chdir(group)
                print(f"Executing dials.stills_process... {f} {group}")
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

        for j in range(len(job_ids1)):
            wait_until_qjob_finished(job_ids1[j])

        job_ids2 = []
        for group in groups:
            os.mkdir(group)
            os.chdir(group)
            # run_ssx_reduce.sh
            with open("run_xia2_reduce.sh", "w") as r:
                r.write(SOURCE_DIALS + "\n")
                r.write("xia2.ssx_reduce ")
                for i, f in enumerate(files):
                    r.write("../" + f + "/" + group + "/idx-*_integrated*.{expt,refl} ")
            print(f"Executing xia2.ssx_reduce... {group}")
            p = subprocess.Popen(
                ['qsub', '-pe', 'smp', '20', '-q', 'medium.q', 'run_xia2_reduce.sh'],# stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="utf-8")  # shell=settings["sh"])
            output, err = p.communicate()
            if output:
                print(f"STDOUT: {output}")
            if err:
                print(f"STDERR: {err}")
            job_id = int(output.splitlines()[0].split()[2])
            job_ids2.append(job_id)
            os.chdir("..")
        print(str(job_ids2))
    return

if __name__ == "__main__":
    run()
