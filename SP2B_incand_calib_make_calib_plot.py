import sqlite3
from datetime import datetime
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import sys
import calendar



instrument = 'UBCSP2'
location = 'POLAR6' #WHI DMT POLAR6
type_particle = 'Aquadag' #PSL, nonincand, incand, Aquadag
#sizes = [80,100,125,150,200,250,269]#,300,350,400,450]
sizes = [300]
start_date = datetime(2015, 1, 1)
end_date = datetime(2016, 1, 1)
start_date_ts = calendar.timegm(start_date.timetuple())
end_date_ts = calendar.timegm(end_date.timetuple())

conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

#check actual vs fit peak posns	

#c.execute('''CREATE TABLE if not exists SP2_coating_analysis(
#id INTEGER PRIMARY KEY AUTOINCREMENT,
#sp2b_file TEXT, 			eg 20120405x001.sp2b
#file_index INT, 			
#instr TEXT,				eg UBCSP2, ECSP2
#instr_locn TEXT,			eg WHI, DMT, POLAR6
#particle_type TEXT,		eg PSL, nonincand, incand, Aquadag
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
#)''')
	
	
AD_data = {}
	
for size in sizes:	
	
	c.execute('''SELECT incand_amp FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=? and particle_dia=?''', 
	(instrument, location, type_particle, size))

	result = c.fetchall()
	
	temp = []
	for line in result:
		amp = line[0]
		temp.append(amp)
	print size, len(temp),np.median(temp), np.mean(temp)
	AD_data[size] = temp
	


conn.close()



##plotting
print 'plotting'

#fig = plt.figure()
#ax = fig.add_subplot(111)
#
#ax.hist(AD_data[80], bins=60)
#
#plt.show()   

fig, axes = plt.subplots(7,1, figsize=(10, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)

axs = axes.ravel()

bin_number = 400


i = 0
for ADsize in AD_data:

	axs[i].hist(AD_data[ADsize], bins=bin_number)
	axs[i].axvline(np.median(AD_data[ADsize]), color='r', linestyle='--')
	axs[i].text(0.6, 0.8,ADsize, transform=axs[i].transAxes)
	axs[i].set_xlim(0,4000)
	i+=1

plt.show()   