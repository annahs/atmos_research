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
WHI_HG_incand_calib = [
[0.87206  ,52.50704	],
[1.12272  ,75.499	],
[1.4047   ,93.55246	],
[1.76501  ,127.22018],
[2.12533  ,165.82211],
[2.56397  ,211.81462],
[4.16188  ,379.35877],
[4.81984  ,436.83438],
[5.5718   ,482.78394],
[7.16971  ,630.59125],
[8.20366  ,694.59427],
[9.17493  ,786.56641],
[10.31854 ,853.84387],
[11.5248  ,907.95486],
[14.15666 ,1139.50203],
]


HG_pkht = np.array([row[1] for row in WHI_HG_incand_calib])
HG_mass = np.array([row[0] for row in WHI_HG_incand_calib])
HG_mass_corr = np.array([row[0]/0.7 for row in WHI_HG_incand_calib])
HG_fit = poly.polyfit(HG_pkht, HG_mass_corr, 1)	
print 'HG fit', HG_fit


for line in WHI_HG_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_fit = HG_fit[0] + HG_fit[1]*incand_pk_ht# + HG_fit[2]*incand_pk_ht *incand_pk_ht 
	
	line.append(AD_corr_fit)

	
HG_pk_ht = [row[1] for row in WHI_HG_incand_calib]
HG_uncorr_mass = [row[0] for row in WHI_HG_incand_calib]
HG_uncorr_fit = [row[2]*0.7 for row in WHI_HG_incand_calib]
HG_ADcorr_fit = [row[2] for row in WHI_HG_incand_calib]


fig = plt.figure(figsize=(12,10))
ax = fig.add_subplot(111)
ax.scatter(HG_pk_ht,HG_uncorr_mass,color='r', label = 'Uncorrected calibration')
ax.plot(HG_pk_ht,HG_ADcorr_fit, '--r', label = 'Aquadag correction applied')
ax.plot(HG_pk_ht,HG_uncorr_fit, '-r')
plt.xlabel('Incandescent pk height (a.u.)')
plt.ylabel('rBC mass (fg)')
#plt.text(250,10, 'Aquadag corrected fit:\nrBC mass = {number:.{digits}g}'.format(number=HG_fit[0], digits=5) +  ' + ' + '{number:.{digits}g}'.format(number=HG_fit[1], digits=5) + '*pkht + ' + '{number:.{digits}g}'.format(number=HG_fit[2], digits=5) + '*pkht^2')  
plt.text(250,15, 'Aquadag corrected fit:\nrBC mass =' + str(round(HG_fit[0],5)) + ' + ' + '{number:.{digits}g}'.format(number=HG_fit[1], digits=5) + '*pkht')
ax.set_ylim(0,24)
ax.set_xlim(0,1500)

plt.legend()
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/calibrations/')
plt.savefig('WHI ECSP2 2009 Aquadag calibration curves.png', bbox_inches='tight')

plt.show()