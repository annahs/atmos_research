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



#mass fg, pk_ht, 
WHI_2012_incand_calib = [
[0.10223	,40			 ],
[0.21718	,38.24573    ],
[0.39249	,84.97978    ],
[0.57401	,141.70101   ],
[0.7397		,204.62578   ],
[1.07964	,347.9183    ],
[1.4103		,486.58653   ],
[1.7443		,628.56949   ],
[2.76014	,1084.06677  ],
[3.40748	,1406.0667   ],
[6.51873	,2963.90429  ],
[7.42515	,3447.05123  ],
]



AD_corr_curve = []

for line in WHI_2012_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_mass_fg = 0.003043*incand_pk_ht + 0.24826
	
	line.append(AD_corr_mass_fg)
	
	
pk_ht = [row[1] for row in WHI_2012_incand_calib]
uncorr_mass = [row[0] for row in WHI_2012_incand_calib]
ADcorr_mass = [row[2] for row in WHI_2012_incand_calib]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(pk_ht,uncorr_mass,'-bo', label = 'uncorrected rBC mass')
ax.plot(pk_ht,ADcorr_mass, '--r*', label = 'Aquadag correction applied')
plt.xlabel('incandescent pk height (a.u.)')
plt.ylabel('rBC mass (fg)')

plt.legend()
plt.show()