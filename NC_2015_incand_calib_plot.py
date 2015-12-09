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



#mob dia, mass fg (from Gysel parameterization), pk_ht, 
NC_2015_incand_calib = [
[100, 0.41189,	109	],
[125, 0.75847,	258	],
[150, 1.26844,	536	],
[200, 2.88464,	1472],
[250, 5.41916,	2647],
[269, 6.64182,	3126],
]             


AD_corr_curve = []

for line in NC_2015_incand_calib:
	
	incand_pk_ht = line[2]
	uncorr_mass_fg = line[1]
	AD_corr_mass_fg = 0.00289*incand_pk_ht + 0.15284
	
	line.append(AD_corr_mass_fg)
	
uncorr_eqtn = lambda x: 0.00202*x + 0.15284
corr_eqtn = lambda x: 0.00289*x + 0.15284

	
pk_ht = [row[2] for row in NC_2015_incand_calib]
uncorr_mass = [row[1] for row in NC_2015_incand_calib]
ADcorr_mass = [row[3] for row in NC_2015_incand_calib]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(pk_ht,uncorr_mass,'ob')
#ax.plot(pk_ht,ADcorr_mass, '*r', label = 'Aquadag correction applied')
ax.plot(range(0, 4000),[uncorr_eqtn(x) for x in range(0,4000)],'b', label = 'uncorrected rBC mass')
ax.plot(range(0, 4000),[corr_eqtn(x) for x in range(0,4000)],'r', label = 'Aquadag correction applied')
plt.text(0.1,0.7,'AD corrected calibration equation\n0.00289*pkht + 0.15284',transform=ax.transAxes)
plt.xlabel('incandescent pk height (a.u.)')
plt.ylabel('rBC mass (fg)')
plt.legend()
plt.show()