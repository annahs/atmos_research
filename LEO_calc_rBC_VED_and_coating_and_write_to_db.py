import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
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
#UNIQUE (sp2b_file, file_index, instr)


#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()
c2 = conn.cursor()

instrument = 'UBCSP2'
instrument_locn = 'POLAR6'
type_particle = 'incand'
start_date = datetime(2015,4,5)
end_date =   datetime(2015,4,6)
max_file_index = 10000
lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor545.lupckl'
rBC_density = 1.8 
incand_sat = 3750
LF_max = 45000 #above this is unreasonable

lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()




begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())


def get_rBC_mass(incand_pk_ht, instrument, year):
	if year == 2012 and instrument=='UBCSP2':
		rBC_mass = 0.003043*incand_pk_ht + 0.24826 #AD corrected linear calibration for UBCSP2 at WHI 2012
	if year == 2010 and instrument=='ECSP2':
		rBC_mass = 0.01081*incand_pk_ht - 0.32619  #AD corrected linear calibration for ECSP2 at WHI 2010if year == 2010 and instrument=='ECSP2':
	if year == 2015 and instrument=='UBCSP2':
		rBC_mass = 0.00202*incand_pk_ht + 0.15284  #AD corrected linear calibration for ECSP2 at WHI 2010
	return rBC_mass

def get_coating_thickness(BC_VED,LEO_amp,coating_lookup_table):
	#get the coating thicknesses from the lookup table which is a dictionary of dictionaries, the 1st keyed with BC core size and the second being coating thicknesses keyed with calc scat amps                  
	core_diameters = sorted(coating_lookup_table.keys())
	prev_diameter = core_diameters[0]

	for core_diameter in core_diameters:
		if core_diameter > BC_VED:
			core_dia_to_use = prev_diameter
			break
		prev_diameter = core_diameter

	#now get the coating thickness for the scat_amp this is the coating thickness based on the raw scattering max
	scattering_amps = sorted(coating_lookup_table[core_dia_to_use].keys())
	prev_amp = scattering_amps[0]
	for scattering_amp in scattering_amps:
		if LEO_amp < scattering_amp:
			scat_amp_to_use = prev_amp
			break
		prev_amp = scattering_amp

	scat_coating_thickness = coating_lookup_table[core_dia_to_use].get(scat_amp_to_use, np.nan) # returns value for the key, or none
	return scat_coating_thickness

LOG_EVERY_N = 10000

test=[]
i = 0
for row in c.execute('''SELECT incand_amp, LF_scat_amp, unix_ts_utc, sp2b_file, file_index, instr FROM SP2_coating_analysis 
WHERE instr=? and instr_locn=? and particle_type=? and incand_amp<? and LF_scat_amp<? and unix_ts_utc>=? and unix_ts_utc<? and file_index<=?''', 
(instrument,instrument_locn,type_particle,incand_sat,LF_max,begin_data,end_data,max_file_index)):
	incand_amp = row[0]
	LF_amp = row[1]
	event_time = datetime.utcfromtimestamp(row[2])
	file = row[3]
	index = row[4]
	instrt = row[5]
	
	rBC_mass = get_rBC_mass(incand_amp, instrt, event_time.year)
	if rBC_mass >= 0.25 and LF_amp < 45000 and LF_amp > 0:
		rBC_VED = (((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
		coat_th = get_coating_thickness(rBC_VED,LF_amp,lookup_table)
	else:
		rBC_VED = None
		coat_th = None
	
	if rBC_VED >= 155 and rBC_VED <180:
		test.append([rBC_VED,coat_th])
	
	
	c2.execute('''UPDATE SP2_coating_analysis SET rBC_mass_fg=?, coat_thickness_nm=? WHERE sp2b_file=? and file_index=? and instr=?''', (rBC_mass,coat_th, file,index,instrt))
	
	i+=1
	if (i % LOG_EVERY_N) == 0:
		print 'record: ', i
	
conn.commit()
conn.close()


#test plot
ved = [row[0] for row in test]
coat = [row[1] for row in test]
print np.nanmedian(coat)


fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(coat, bins=20,range=(-50,200), histtype='step', color = 'black')


plt.show()
