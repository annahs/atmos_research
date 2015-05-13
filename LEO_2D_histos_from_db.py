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
type_particle = 'incand'
start_date = datetime.strptime('20120401','%Y%m%d')
end_date = datetime.strptime('20120531','%Y%m%d')
lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/lookup_tables/coating_lookup_table_WHI_2012_UBCSP2.lupckl'
rBC_density = 1.8 
incand_sat = 3750
LF_max = 45000 #above this is unreasonable

lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()

min_rBC_mass = 1.63#120 2.6-#140 3.86-#160nm 0.25
max_rBC_mass = 2.6#140 3.86-160 5.5-#180nm 10.05
 
VED_min = 65
VED_max = 220

scat_lim = 100

begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())

data = []

particles=0
no_scat=0 
no_scat_110 =0
fit_failure=0
early_evap=0
early_evap_110=0
flat_fit=0
LF_high=0


for row in c.execute('''SELECT rBC_mass_fg, coat_thickness_nm, unix_ts_utc, LF_scat_amp, LF_baseline_pct_diff, sp2b_file, file_index, instr,actual_scat_amp
FROM SP2_coating_analysis 
WHERE instr=? and instr_locn=? and particle_type=? and rBC_mass_fg>=? and  rBC_mass_fg<? and unix_ts_utc>=? and unix_ts_utc<?''', 
(instrument,instrument_locn,type_particle, min_rBC_mass, max_rBC_mass, begin_data,end_data)):	
	particles+=1
	
	rBC_mass = row[0]
	coat_thickness = row[1]
	event_time = datetime.utcfromtimestamp(row[2])
	LEO_amp = row[3]
	LF_baseline_pctdiff = row[4]
	file = row[5]
	index = row[6]
	instrt = row[7]
	meas_scat_amp = row[8]
	rBC_VED = (((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm

	if meas_scat_amp < 6:
		no_scat +=1
		if rBC_VED > scat_lim:
			no_scat_110+=1
			data.append([rBC_VED,coat_thickness])

	
	if LEO_amp == 0.0 and LF_baseline_pctdiff == None and meas_scat_amp >= 6:
		early_evap +=1
		if rBC_VED > scat_lim:
			early_evap_110 +=1
			
	if LEO_amp == -2:
		early_evap +=1
		if rBC_VED > scat_lim:
			early_evap_110 +=1
		
	if LEO_amp == -1:
		fit_failure +=1
	
	if LEO_amp == 0.0 and LF_baseline_pctdiff != None:
		flat_fit +=1
	
	if LEO_amp > LF_max:
		LF_high +=1
	
	if LEO_amp > 0:
		data.append([rBC_VED,coat_thickness])

	
print '# of particles', particles
print 'no_scat', no_scat
print 'no_scat_110', no_scat_110
print 'fit_failure', fit_failure
print 'early_evap', early_evap
print 'early_evap_110', early_evap_110
print 'flat_fit', flat_fit
print 'LF_high', LF_high

evap_pct = (early_evap)*100.0/particles
evap_pct_110 = (early_evap_110)*100.0/particles
no_scat_pct = (no_scat)*100.0/particles
no_scat_pct_110 = no_scat_110*100./particles

print evap_pct, evap_pct_110, no_scat_pct,no_scat_pct_110



rBC_VEDs = [row[0] for row in data]
coatings = [row[1] for row in data]
median_coat = np.median (coatings)
print 'median coating',median_coat

#####hexbin coat vs core###

fig = plt.figure()

ax = fig.add_subplot(111)

#x_limits = [0,250]
#y_limits = [0,250]


#h = plt.hexbin(rBC_VEDs, coatings, cmap=cm.jet,gridsize = 50, mincnt=1)
hist = plt.hist(coatings, bins=50)
plt.xlabel('frequency')
plt.xlabel('Coating Thickness (nm)')
#cb = plt.colorbar()
#cb.set_label('frequency')

plt.show()      

