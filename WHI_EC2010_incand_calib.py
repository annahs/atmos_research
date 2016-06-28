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
[0.20238	, 24.80418  ],
[0.66044	, 82.24543  ],
[1.51286	, 210.18277 ],
[2.12027	, 306.78851 ],
[2.86612	, 416.44909 ],
[3.78257	, 562.66319 ],
[4.84818	, 729.76501 ],
[6.06277	, 902.08877 ],
[7.42637	, 1079.63446],
[8.98167	, 1278.06789],
[12.47547,	1695.82245  ],
[18.95172,	2463.44648  ],]


HG_pkht = np.array([row[1] for row in WHI_HG_incand_calib])
HG_mass = np.array([row[0] for row in WHI_HG_incand_calib])
HG_mass_corr = np.array([row[0]/0.7 for row in WHI_HG_incand_calib])
HG_fit = poly.polyfit(HG_pkht, HG_mass_corr, 2)	
HG_fit_uncorr = poly.polyfit(HG_pkht, HG_mass, 2)	
print 'HG fit_corr', HG_fit
print 'HG fit_uncorr', HG_fit_uncorr


for line in WHI_HG_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_fit = HG_fit[0] + HG_fit[1]*incand_pk_ht + HG_fit[2]*incand_pk_ht *incand_pk_ht 
	
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
plt.text(250,10, 'Aquadag corrected fit:\nrBC mass = {number:.{digits}g}'.format(number=HG_fit[0], digits=5) +  ' + ' + '{number:.{digits}g}'.format(number=HG_fit[1], digits=5) + '*pkht + ' + '{number:.{digits}g}'.format(number=HG_fit[2], digits=5) + '*pkht^2')  
ax.set_ylim(0,24)
ax.set_xlim(0,3000)

plt.legend()
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/calibrations/')
plt.savefig('WHI ECSP2 2010 Aquadag calibration curves.png', bbox_inches='tight')

plt.show()