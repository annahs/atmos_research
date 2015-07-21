import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import math



#PSL size, median scat, Mie calc scat, 10thptile of actual scat, 90th ptile of actual scat
NC_2015_scat_calib = [
[0, 0,	0, 0, 0],
[150, 118,	0.135, 118-90,146-118],
[200, 342,	0.766, 342-269,404-342],
[240, 1165,	2.3,   1165-884, 1279-1165],
[269, 2535,	4.54,  2535-2013,2701-2535],
]             

	
#uncorr_eqtn = lambda x: 0.00202*x + 0.15284
#corr_eqtn = lambda x: 0.00289*x + 0.15284

scat_val = np.array([row[1] for row in NC_2015_scat_calib])
Mie_calc_val = np.array([row[2] for row in NC_2015_scat_calib])
yerrL =  [row[3] for row in NC_2015_scat_calib]
yerrU =  [row[4] for row in NC_2015_scat_calib]

Mie_calc_val = Mie_calc_val[:,np.newaxis]
lin_fit= np.linalg.lstsq(Mie_calc_val, scat_val)
print lin_fit

fit_eqtn = lambda x: lin_fit[0][0]*x 

fig = plt.figure()
ax = fig.add_subplot(111)
ax.errorbar(Mie_calc_val,scat_val,yerr=[yerrL,yerrU],fmt='o')
ax.plot(range(0, 6),[fit_eqtn(x) for x in range(0,6)],'b')
ax.set_ylim(0,3000)
plt.text(0.1,0.7,'slope: ' + str(lin_fit[0][0]),transform=ax.transAxes)
plt.ylabel('scattering pk height (a.u.)')
plt.xlabel('Mie calc scattering')

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/')
plt.savefig('Netcare Spring 2015 - PSL scattering calib plot - calc vs measured scattering amplitude.png', bbox_inches='tight')


plt.show()