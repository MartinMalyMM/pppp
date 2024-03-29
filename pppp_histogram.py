import sys
import numpy as np
import matplotlib.pyplot as plt
from pandas import read_csv


if len(sys.argv) > 1:
    csvfile = sys.argv[1]
else:
    csvfile = 'average_intensity_all.csv'
df = read_csv(csvfile, header=None, index_col=False, sep=',',
              names=("runevent", "radial_average"))
x = df["average_intensity"].to_numpy()
n, bins, patches = plt.hist(x, 180, density=True, facecolor='g', alpha=0.75)
plt.xlim([0, 90])
n_images = x.size
# plt.locator_params(nbins=9, axis='x')
plt.xlabel('Average total scattered intensity')
plt.grid(True)
plt.title('Number of images used: ' + str(n_images))
plt.savefig('average_intensity_all.png', bbox_inches="tight", dpi=200)
