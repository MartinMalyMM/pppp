import argparse
import os
import sys
from pathlib import Path
import subprocess
import time
import numpy as np

# ----------------------------------------------------------------------
# EXAMPLE USAGE
# dials.python pppp.py --geom /path/to/geometry_refinement/refined.expt --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ --files 133451-0 133451-1 133451-2
# ----------------------------------------------------------------------

# assuming Python3 (e.g. dials.python) and qsub on GNU/Linux


# https://stackoverflow.com/questions/2785821/is-there-an-easy-way-in-python-to-wait-until-certain-condition-is-true
def wait_until_not_empty(filename, period=5):
    while True:
        if os.path.exists(filename):
            if os.stat(filename).st_size != 0: return True
        #print("Still waiting...")
        time.sleep(period)
    return False


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


def plot_histogram(inputfile='radial_average_all.csv', outputplot='radial_average_all.png'):
    df = read_csv(inputfile, header=None, index_col=False, sep=',',
                  names=("runevent", "radial_average"))
    x = df["radial_average"].to_numpy()
    n_images = x.size
    n, bins, patches = plt.hist(x, 250, density=True, facecolor='g', alpha=0.75)
    plt.xlim([0, 90])
    plt.xlabel('Radial average')
    plt.grid(True)
    plt.savefig(outputplot, bbox_inches="tight", dpi=200)
    plt.title('Number of images used: ' + str(n_images))
    return outputplot


def run():
    parser = argparse.ArgumentParser(
        description="pppp - Pump and Probe Processing Pipeline - 1st script"
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
        "--geom",
        help="Path to a geometry file for DIALS",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--geom_crystfel",
        help="Path to a geometry file for CrystFEL",
        type=str,
    )
    parser.add_argument(
        "--sim", "--simulate",
        help="Simulate: create files but not execute qsub jobs",
        action="store_true",
        dest="sim",
    )
    args = parser.parse_args()

    print("PPPP Pump & Probe Processing Pipeline")
    cwd = os.getcwd()
    print(f"Working directory: {cwd}")
    print("")

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

    job_ids1 = []
    for i, f in enumerate(files):
        os.mkdir(f)
        os.chdir(f)
        with open("tags.sh", "w") as tags_sh:
            tags_sh.write(f"""module load dials
dials.stills_process show_image_tags=true {args.path}/{f}/run{f}.h5 > tags.txt""")
        subprocess.check_call(['chmod', '+x', "tags.sh"], encoding="utf-8")
        print(f"Executing qsub tags.sh for {f}...")
        if not args.sim:
            p = subprocess.Popen(
                ['qsub', '-pe', 'smp', '20', 'tags.sh'],# stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="utf-8")  # shell=settings["sh"])
            output, err = p.communicate()

            if output:
                print(f"STDOUT: {output}")
            if err:
                print(f"STDERR: {err}")
            job_id = int(output.splitlines()[0].split()[2])
            job_ids1.append(job_id)
        else:
            subprocess.check_call(['touch', 'tags.txt'], encoding="utf-8")
        os.chdir("..")
    print("")
    print("List of jobs now running:")
    print(str(job_ids1))
    print("Waiting for the jobs to be finished...")
    #print("Waiting for 30 seconds...")
    #time.sleep(30)

    job_ids2 = []
    for i, f in enumerate(files):
        os.chdir(f)
        wait_until_not_empty('tags.txt')
        if not args.sim:
            wait_until_qjob_finished(job_ids1[i])
            with open("tags.txt", "r") as tags_txt:
                tags_txt_lines = tags_txt.readlines()
            #for k, line in enumerate(tags_txt_lines):
            #    if "Showing image tags" in line:
            #        j = k
            #        break
            #tags_txt_lines_strip = tags_txt_lines[j + 1:]
            tags_txt_lines_strip = []#
            for line in tags_txt_lines:
                if "run" == line[:3]:
                    tags_txt_lines_strip.append(line)
        else:
            tags_txt_lines_strip = ""
        with open("tags.txt", "w") as tags_txt:
            tags_txt.writelines(tags_txt_lines_strip)
        with open("filter_radial_av.sh", "w") as filter_sh:
            filter_sh.write(r'''module load dials/nightly
dxtbx.radial_average reference_geometry=''' + args.geom + r" show_plots=false " + args.path + r"/" + f + r"/run" + f + r'''.h5 > filter_radial_av_tmp.log
cat filter_radial_av_tmp.log | grep Average | awk '{print $5}' > filter_radial_av.log

i=1
while read p; do
  event=$(echo "$p" | cut -c13-18)
  run=$(echo "$p" | cut -c1-12)
  radav=$(sed "${i}q;d" filter_radial_av.log)
  printf "%s%s %2s\n" $run$event,$radav >> radial_average.csv
  i=$((i+1))
done <tags.txt''')
        subprocess.check_call(['chmod', '+x', "filter_radial_av.sh"], encoding="utf-8")
        print(f"Executing qsub filter_radial_av.sh for {f}...")
        if not args.sim:
            p = subprocess.Popen(
                ['qsub', '-pe', 'smp', '20', 'filter_radial_av.sh'],# stdin=subprocess.PIPE,
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

        # files.lst for crystfel
        with open("files.lst", "a+") as files_lst:
            files_lst.write(args.path + "/" + f + "/run" + f + '.h5/n')


    print("")
    print(str(job_ids2))
    print("Now you can have a break - time for tea or coffee!")

    radial_average_merge = []
    for i, f in enumerate(files):
        os.chdir(f)
        if args.sim:
            subprocess.check_call(['touch', 'radial_average.csv'], encoding="utf-8")
            #subprocess.check_call(['touch', 'pump.txt'])
            #subprocess.check_call(['touch', 'probe.txt'])
        else:
            wait_until_qjob_finished(job_ids2[i])
            with open("radial_average.csv", "r") as f:
                lines = f.readlines()
            radial_average_merge = radial_average_merge + lines
        os.chdir("..")

    with open("radial_average_all.csv", "w") as f:
        f.write('\n'.join(radial_average_merge))
    print("Check data in the file radial_average_all.csv")

    try:
        import numpy as np
        import matplotlib.pyplot as plt
        from pandas import read_csv
        print("Plotting the result...")
        outputplot = plot_histogram(inputfile='radial_average_all.csv', outputplot='radial_average_all.png')
        print(f"Histogram plotted to {outputplot}")
    except:
        print("You can use it to plot a histogram.")

    if args.geom_crystfel:
        print("Creating events.lst for CrystFEL")
        p = subprocess.Popen(
            ['module', 'load', 'crystfel', '&&', 'list_events', '-i', 'files.lst', '-o', 'events.lst', '-g', args.geom_crystfel],# stdin=subprocess.PIPE,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
             encoding="utf-8")  # shell=settings["sh"])
        output, err = p.communicate()
        if output:
            print(f"STDOUT: {output}")
        if err:
            print(f"STDERR: {err}")

    print("Done.")


if __name__ == "__main__":
    run()
