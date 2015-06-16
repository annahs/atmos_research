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

#id INTEGER PRIMARY KEY AUTOINCREMENT,
#sp2b_file TEXT, 
#file_index INT, 
#instr TEXT,
#instr_locn TEXT,
#particle_type TEXT,		
#particle_dia FLOAT,				
#unix_ts_utc FLOAT,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#LF_scat_amp FLOAT,
#incand_amp FLOAT,
#lag_time_fit_to_incand FLOAT,
#LF_baseline_pct_diff FLOAT,
#rBC_mass_fg FLOAT,
#coat_thickness_nm FLOAT,
#zero_crossing_posn FLOAT,
#UNIQUE (sp2b_file, file_index, instr)


#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

instrument = 'UBCSP2'
instrument_locn = 'WHI'
type_particle = 'PSL'
psl_size = 200

FF = []
act = []

for row in c.execute('''SELECT FF_scat_amp, actual_scat_amp, sp2b_file, file_index, instr
FROM SP2_coating_analysis 
WHERE instr=? and instr_locn=? and particle_type=? and particle_dia=?''', 
(instrument,instrument_locn,type_particle,psl_size)):	
	FF_amp = row[0]
	act_amp = row[1]
	
	FF.append(FF_amp)
	act.append(act_amp)
	
conn.close()
	
print np.median(act)
	
	
fig = plt.figure()

ax = fig.add_subplot(111)

#x_limits = [0,250]
#y_limits = [0,250]


#h = plt.hexbin(rBC_VEDs, coatings, cmap=cm.jet,gridsize = 50, mincnt=1)
hist = plt.hist(act, bins=50)

plt.xlabel('frequency')
plt.xlabel('Coating Thickness (nm)')
#cb = plt.colorbar()
#cb.set_label('frequency')

plt.show()      

