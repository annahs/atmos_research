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
[0.22994  ,    693.12 ],
[0.22994  ,    664.57 ],
[0.28534  ,    1199.79],
[0.41189  ,    617.7  ],
[0.41189  ,    1462.2 ],
[0.41189  ,    739.58 ],
[0.67551  ,    3310.95],
[0.75847  ,    2076.1 ],
[0.75847  ,    2327.4 ],
[0.75847  ,    3024   ],
[1.25406  ,    6410.49],
[1.26844  ,    6186.6 ],
[1.26844  ,    5418.8 ],
[1.26844  ,    5402.2 ],
[1.96969  ,    9788   ],
[1.96969  ,    10626  ],
[2.66016  ,    13813.1],
[2.88464  ,    17294  ],
[2.88464  ,    16266  ],
[2.88464  ,    17354  ],
[4.03042  ,    24658  ],
[4.03042  ,    23574  ],
[4.60001  ,    24328.7],
[5.41916  ,    32861  ],
[6.64182  ,    38700  ],
[6.64182  ,    39214  ],
[6.64182  ,    37626  ],
[7.05122  ,    37864.2],
[8.95095  ,    49764  ],
[8.95095  ,    48229  ],
[8.95095  ,    50201  ],
]


#mass fg, pk_ht, UNCORR 
#AL_LG_incand_calib = [
#[1.26844 ,601.39  ],
#[1.26844 ,524.74  ],
#[1.26844 ,520.09  ],
#[1.96969 ,1041.6  ],
#[1.96969 ,978.83  ],
#[2.88464 ,1627.2  ],
#[2.88464 ,1718    ],
#[2.88464 ,1735.5  ],
#[4.03042 ,2456.4  ],
#[4.03042 ,2357.6  ],
#[5.41916 ,3291.3  ],
#[6.64182 ,3781.9  ],
#[6.64182 ,3944.9  ],
#[6.64182 ,3899.8  ],
#[8.95095 ,5020.3  ],
#[8.95095 ,5074.7  ],
#[8.95095 ,4885.5  ],
#[13.49107 ,6953.1  ],
#[13.49107 ,6742.2  ],
#[13.49107 ,7104.2  ],
#[18.99872 ,9242.2  ],
#[18.99872 ,8897.5  ],
#[18.99872 ,8819.4  ],
#[25.40154 ,10794   ],
#[25.40154 ,11057   ],
#[25.40154 ,11531   ],
#]
#

AL_LG_incand_calib = [	
[1.26844   ,524.74	],
[1.26844   ,520.09	],
[1.26844   ,601.39	],
[1.96969   ,978.83	],
[1.96969   ,1041.6	],
[2.66016   ,1398	],
[2.88464   ,1718	],
[2.88464   ,1627.2	],
[2.88464   ,1735.5	],
[4.03042   ,2456.4	],
[4.03042   ,2357.6	],
[4.60001   ,2461	],
[5.41916   ,3291.3	],
[6.64182   ,3899.8	],
[6.64182   ,3944.9	],
[6.64182   ,3781.9	],
[7.05122   ,3847	],
[8.95095   ,4885.5	],
[8.95095   ,5074.7	],
[8.95095   ,5020.3	],
[9.94943   ,5384	],
[13.26053  ,7146	],
[13.49107  ,7104.2	],
[13.49107  ,6953.1	],
[13.49107  ,6742.2	],
[16.94251  ,8902	],
[18.99872  ,8819.4	],
[18.99872  ,9242.2	],
[18.99872  ,8897.5	],
[25.18362  ,13298	],
[25.40154  ,10794	],
[25.40154  ,11057	],
[25.40154  ,11531	],
]

HG_pkht = np.array([row[1] for row in AL_HG_incand_calib])
HG_mass = np.array([row[0] for row in AL_HG_incand_calib])
HG_mass_corr = np.array([row[0]/0.7 for row in AL_HG_incand_calib])
HG_fit = poly.polyfit(HG_pkht, HG_mass_corr, 2)	
print 'HG fit', HG_fit


for line in AL_HG_incand_calib:
	
	incand_pk_ht = line[1]
	uncorr_mass_fg = line[0]
	AD_corr_fit = HG_fit[0] + HG_fit[1]*incand_pk_ht + HG_fit[2]*incand_pk_ht*incand_pk_ht
	
	line.append(AD_corr_fit)

LG_pkht = np.array([row[1] for row in AL_LG_incand_calib])
LG_mass = np.array([row[0] for row in AL_LG_incand_calib])
LG_mass_corr = np.array([row[0]/0.7 for row in AL_LG_incand_calib])
LG_fit = poly.polyfit(LG_pkht, LG_mass_corr, 2)	
print 'LG fit', LG_fit

	
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
ax.scatter(HG_pk_ht,HG_uncorr_mass,color='r', label = 'HG uncorrected rBC mass')
ax.plot(HG_pk_ht,HG_ADcorr_fit, '--r', label = 'HG Aquadag correction applied')
ax.plot(HG_pk_ht,HG_uncorr_fit, '-r')
ax.scatter(LG_pk_ht,LG_uncorr_mass,color = 'blue', label = 'LG uncorrected rBC mass')
ax.plot(LG_pk_ht,LG_ADcorr_fit, '--b', label = 'LG Aquadag correction applied')
ax.plot(LG_pk_ht,LG_uncorr_fit, '-b')
plt.xlabel('incandescent pk height (a.u.)')
plt.ylabel('rBC mass (fg)')
plt.text(10000,11, '0.41527 + 2.13238E-4*HG_pkht + 7.17406E-10*HG_pkht^2')
plt.text(11000,30, '0.70095 + 1.82480E-3*LG_pkht + 1.22794E-7*LG_pkht^2')
plt.axhspan(1.8,12.8, color='g', alpha=0.25, lw=0)
plt.axhspan(0,1.8, color='c', alpha=0.25, lw=0)
plt.axhspan(12.8,41, color='y', alpha=0.25, lw=0)
ax.set_ylim(0,42)
ax.set_xlim(0,55000)

plt.legend()
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert Data/SP2 Calibrations/')
plt.savefig('Alert SP2#58 Aquadag calibration curves.png', bbox_inches='tight')

plt.show()