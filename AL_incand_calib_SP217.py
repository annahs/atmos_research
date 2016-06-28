import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from pprint import pprint
import sqlite3
import calendar
from datetime import datetime
from datetime import timedelta
import math
import numpy.polynomial.polynomial as poly




#mass fg, pk_ht, UNCORR
AL_HG_incand_calib = [
[0.23173,25.17577  ],
[0.41398,48.99595  ],
[1.26106,186.48122 ],
[2.88282,489.41296 ],
[5.43241,880.95554 ],
[8.94784,1347.39537],
]


HG_pkht = np.array([row[1] for row in AL_HG_incand_calib])
HG_mass = np.array([row[0] for row in AL_HG_incand_calib])
HG_mass_corr = np.array([row[0]/0.7 for row in AL_HG_incand_calib])
HG_fit = poly.polyfit(HG_pkht, HG_mass_corr, 1)	
print 'HG fit', HG_fit


for line in AL_HG_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_fit = HG_fit[0] + HG_fit[1]*incand_pk_ht 
	
	line.append(AD_corr_fit)

	
HG_pk_ht = [row[1] for row in AL_HG_incand_calib]
HG_uncorr_mass = [row[0] for row in AL_HG_incand_calib]
HG_uncorr_fit = [row[2]*0.7 for row in AL_HG_incand_calib]
HG_ADcorr_fit = [row[2] for row in AL_HG_incand_calib]


fig = plt.figure(figsize=(12,10))
ax = fig.add_subplot(111)
ax.scatter(HG_pk_ht,HG_uncorr_mass,color='r', label = 'Uncorrected calibration')
ax.plot(HG_pk_ht,HG_ADcorr_fit, '--r', label = 'Aquadag correction applied')
ax.plot(HG_pk_ht,HG_uncorr_fit, '-r')
plt.xlabel('Incandescent pk height (a.u.)')
plt.ylabel('rBC mass (fg)')
plt.text(250,10, 'Aquadag corrected fit:\nrBC mass = -0.017584 + 9.2453E-3*pkht')
ax.set_ylim(0,14)
ax.set_xlim(0,2000)

plt.legend()
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert Data/SP2 Calibrations/')
plt.savefig('Alert SP2#17 Aquadag calibration curves.png', bbox_inches='tight')

plt.show()