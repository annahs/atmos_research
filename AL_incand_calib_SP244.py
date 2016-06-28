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






986.22
725.78
1567.4
2941
5127.9
8463.7
13283
18566
24234
37216
52182









#mass fg, pk_ht, UNCORR
AL_HG_incand_calib = [
[0.11144 ,986.22    ],
[0.22994 ,725.78    ],
[0.41189 ,1567.4    ],
[0.67707 ,2941    ],
[1.04293 ,5127.9    ],
[1.52461 ,8463.7    ],
[2.13496 ,13283    ],
[2.88464 ,18566    ],
[3.78215 ,24234    ],
[6.04449 ,37216    ],
[8.95095 ,52182    ],
]

AL_LG_incand_calib = [	
[0.67707  ,276.81],
[1.04293  ,494.74],
[1.52461  ,843],
[2.13496  ,1325.2],
[2.88464  ,1869.5],
[3.78215  ,2448],
[6.04449  ,3801.7],
[8.95095  ,5368.3],
]

HG_pkht = np.array([row[1] for row in AL_HG_incand_calib])
HG_mass = np.array([row[0] for row in AL_HG_incand_calib])
HG_mass_corr = np.array([row[0]/0.7 for row in AL_HG_incand_calib])
HG_fit = poly.polyfit(HG_pkht, HG_mass_corr, 2)	
print 'HG AD corr fit', HG_fit


for line in AL_HG_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_fit = HG_fit[0] + HG_fit[1]*incand_pk_ht + HG_fit[2]*incand_pk_ht*incand_pk_ht
	
	line.append(AD_corr_fit)

LG_pkht = np.array([row[1] for row in AL_LG_incand_calib])
LG_mass = np.array([row[0] for row in AL_LG_incand_calib])
LG_mass_corr = np.array([row[0]/0.7 for row in AL_LG_incand_calib])
LG_fit = poly.polyfit(LG_pkht, LG_mass_corr, 2)	
print 'LG AD corr fit', LG_fit

	
for line in AL_LG_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_fit = LG_fit[0] + LG_fit[1]*incand_pk_ht + LG_fit[2]*incand_pk_ht*incand_pk_ht
	
	line.append(AD_corr_fit)
	
	
HG_pk_ht = [row[1] for row in AL_HG_incand_calib]
HG_uncorr_mass = [row[0] for row in AL_HG_incand_calib]
HG_uncorr_fit = [row[2]*0.7 for row in AL_HG_incand_calib]
HG_ADcorr_fit = [row[2] for row in AL_HG_incand_calib]

LG_pk_ht = [row[1] for row in AL_LG_incand_calib]
LG_uncorr_mass = [row[0] for row in AL_LG_incand_calib]
LG_uncorr_fit = [row[2]*0.7 for row in AL_LG_incand_calib]
LG_ADcorr_fit = [row[2] for row in AL_LG_incand_calib]

fig = plt.figure(figsize=(12,10))
ax = fig.add_subplot(111)
ax.scatter(HG_pk_ht,HG_uncorr_mass,color='r', label = 'HG uncorrected calibration')
ax.plot(HG_pk_ht,HG_ADcorr_fit, '--r', label = 'HG Aquadag correction applied')
ax.plot(HG_pk_ht,HG_uncorr_fit, '-r')
ax.scatter(LG_pk_ht,LG_uncorr_mass,color = 'blue', label = 'LG uncorrected calibration')
ax.plot(LG_pk_ht,LG_ADcorr_fit, '--b', label = 'LG Aquadag correction applied')
ax.plot(LG_pk_ht,LG_uncorr_fit, '-b')
plt.xlabel('Incandescent pk height (a.u.)')
plt.ylabel('rBC mass (fg)')
plt.text(9600,8, 'Aquadag corrected fit:\nrBC mass = 0.26887 + 1.9552E-4*HG_pkht + 8.31906E-10*HG_pkht^2')
plt.text(5900,12, 'Aquadag corrected fit:\nrBC mass = 0.56062 + 1.7402E-3*LG_pkht + 1.0009E-7*LG_pkht^2')
#plt.axhspan(1.8,12.8, color='g', alpha=0.25, lw=0)
#plt.axhspan(0,1.8, color='c', alpha=0.25, lw=0)
#plt.axhspan(12.8,41, color='y', alpha=0.25, lw=0)
ax.set_ylim(0,16)
ax.set_xlim(0,55000)

plt.legend()
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert Data/SP2 Calibrations/')
plt.savefig('Alert SP2#44 Aquadag calibration curves.png', bbox_inches='tight')

plt.show()