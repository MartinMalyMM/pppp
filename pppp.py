import argparse
import os
import sys
from pathlib import Path
import subprocess
import time
import numpy as np

# ----------------------------------------------------------------------
# pppp - X-ray Pump and Probe Processing Pipeline
# 1st script - calculate average total scattered intensity
#
# Martin Maly - martin.maly@soton.ac.uk
# https://github.com/MartinMalyMM/pppp
# ----------------------------------------------------------------------
# EXAMPLE USAGE
# dials.python pppp.py --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ --files 133451 --geom /path/to/geometry_refinement/refined.expt --geom_crystfel /path/to/geometry1.geom
# dials.python pppp.py --geom /path/to/geometry_refinement/refined.expt --dir /dls/x02-1/data/2022/mx15722-39/cheetah/ --files 133451-0 133451-1 133451-2
# ----------------------------------------------------------------------
#
# Dependencies: qsub and Python3 (e.g. dials.python) on GNU/Linux
#
# After run, results are available in files average_intensity_all.csv and average_intensity_all.png
#
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#            IMPORTANT SETTING - PATHS TO DIALS AND CRYSTFEL
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
SOURCE_DIALS = "module load dials/nightly"
# SOURCE_DIALS = ""
SOURCE_CRYSTFEL = "module load crystfel"
# SOURCE_CRYSTFEL = ""
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


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


def plot_histogram(inputfile='average_intensity_all.csv', outputplot='average_intensity_all.png'):
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        from pandas import read_csv
    except:
        print(f"Histogram not plotted. An error ocurred while importing numpy, matplotlib.pyplot or pandas.")
        return None

    print("Plotting the result...")
    df = read_csv(inputfile, header=None, index_col=False, sep=',',
                  names=("runevent", "average_intensity"))
    x = df["average_intensity"].to_numpy()
    n_images = x.size
    maximal_intensity = 100
    n_histogram_bins = 2 * maximal_intensity
    n_labels = maximal_intensity / 10
    n, bins, patches = plt.hist(x, n_histogram_bins, density=True, facecolor='g', alpha=0.75)
    plt.xlim([0, maximal_intensity])
    n_images = x.size
    plt.locator_params(nbins=n_labels, axis='x')
    plt.xlabel('Average total scattered intensity')
    plt.grid(True)
    plt.title('Number of images used: ' + str(n_images))
    plt.savefig(outputplot, bbox_inches="tight", dpi=200)
    plt.title('Number of images used: ' + str(n_images))
    print(f"Histogram plotted to {outputplot}")
    return outputplot


def run():
    parser = argparse.ArgumentParser(
        description="pppp - X-ray Pump and Probe Processing Pipeline - 1st script - calculate average total scattered intensity"
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
            tags_sh.write(
                SOURCE_DIALS + "\n" + \
                f"""dials.stills_process show_image_tags=true {args.path}/{f}/run{f}.h5 > tags.txt""")
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
        # create files.lst for crystfel
        with open("files.lst", "a+") as files_lst:
            files_lst.write(args.path + "/" + f + "/run" + f + '''.h5
''')

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
        with open("filter_average_intensity.sh", "w") as filter_sh:
            filter_sh.write(
                SOURCE_DIALS + "\n" + \
                r'''dxtbx.radial_average reference_geometry=''' + args.geom + r" show_plots=false " + args.path + r"/" + f + r"/run" + f + r'''.h5 > filter_average_intensity_tmp.log
cat filter_average_intensity_tmp.log | grep Average | awk '{print $5}' > filter_average_intensity.log

i=1
while read p; do
  event=$(echo "$p" | cut -c13-18)
  run=$(echo "$p" | cut -c1-12)
  radav=$(sed "${i}q;d" filter_average_intensity.log)
  printf "%s%s %2s\n" $run$event,$radav >> average_intensity.csv
  i=$((i+1))
done <tags.txt''')
        subprocess.check_call(['chmod', '+x', "filter_average_intensity.sh"], encoding="utf-8")
        print(f"Executing qsub filter_average_intensity.sh for {f}...")
        if not args.sim:
            p = subprocess.Popen(
                ['qsub', '-pe', 'smp', '20', 'filter_average_intensity.sh'],# stdin=subprocess.PIPE,
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


    print("")
    print(str(job_ids2))
    print("Now you can have a break - time for tea or coffee!")

    average_intensity_merge = []
    for i, f in enumerate(files):
        os.chdir(f)
        if args.sim:
            subprocess.check_call(['touch', 'average_intensity.csv'], encoding="utf-8")
            #subprocess.check_call(['touch', 'pump.txt'])
            #subprocess.check_call(['touch', 'probe.txt'])
        else:
            wait_until_qjob_finished(job_ids2[i])
            with open("average_intensity.csv", "r") as f:
                lines = f.readlines()
            average_intensity_merge = average_intensity_merge + lines
        os.chdir("..")

    with open("average_intensity_all.csv", "w") as f:
        f.write('\n'.join(average_intensity_merge))
    print("Check data in the file average_intensity_all.csv")
    print("You can use it to plot a histogram.")

    # try:
    # import numpy as np
    # import matplotlib.pyplot as plt
    # from pandas import read_csv
    # print("Plotting the result...")
    outputplot = plot_histogram(inputfile='average_intensity_all.csv', outputplot='average_intensity_all.png')
    # print(f"Histogram plotted to {outputplot}")
    # except:
    # print(f"Histogram not plotted. :-(")

    if args.geom_crystfel:
        print("Creating events.lst for CrystFEL")
        try:
            p = subprocess.Popen(
                SOURCE_CRYSTFEL + ' && list_events -i files.lst -o events.lst -g '+ args.geom_crystfel,# stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="utf-8", shell=True)
            output, err = p.communicate()
            if output:
                print(f"STDOUT: {output}")
            if err:
                print(f"STDERR: {err}")
        except:
            print("Error occured while creating events.lst for CrystFEL")

    print("Done.")


if __name__ == "__main__":
    run()
