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
#coat_thickness_from_actual_scat_amp FLOAT
#UNIQUE (sp2b_file, file_index, instr)

file_info = '_RI2.26-1.26_calib_factor225'

#mie parametrs to use
lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/lookup_tables/coating_lookup_table_WHI_2012_UBCSP2-nc(2p26,1p26)-calib_scale_factor225.lupckl'
rBC_density = 1.8

lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()

#analysis parameters
instrument = 'UBCSP2'
instrument_locn = 'WHI'
timezone = -8
type_particle = 'incand'
start_date = datetime.strptime('20120401','%Y%m%d')
end_date = datetime.strptime('20120601','%Y%m%d')
LF_max = 45000 #above this is unreasonable

min_rBC_mass = 3.4  #100-#0.94#1.63-#120 2.6-#140 3.86-#160nm 0.25-#65
min_BC_VED = (((min_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7
max_rBC_mass = 5.6  #140 3.86-160 5.5-#180nm 7.55-#200 10.05-#220
max_BC_VED = (((max_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7

begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())



######get spike times (these are in local time already)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times_full = pickle.load(file)
file.close()

spike_times = []
for spike in spike_times_full:
	if spike.year >= 2012:
		if spike < datetime(2012,06,01):
			spike_times.append(spike)

#open cluslist and read into a python list (convert UTC to local time here)
cluslist = []
CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip_amount_added'
#CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip_added-sig_precip_72hrs_pre_arrival'
#CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip_added-sig_precip_any_time'

with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5]))+timedelta(hours = timezone) #convert UTC->LT here
		significant_rainfall = newline[8]
		if traj_time.year >=2012:
			cluslist.append([traj_time,cluster_no,significant_rainfall])

#sort cluslist by row_datetime in place		
cluslist.sort(key=lambda clus_info: clus_info[0])  
print len(cluslist)

#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()


#set up lists and counters needed 
cluster_1 = []
cluster_2= []
cluster_3= []
cluster_4 = []
cluster_5= []
cluster_6= []
cluster_GBPS= []
spikes = []

particles=0
no_scat=0 
fit_failure=0
early_evap=0
flat_fit=0
LF_high=0
count_155_180 = 0
no_scat_155_180 = 0
early_evap_155_180 = 0

LOG_EVERY_N = 10000

#methods 

def get_rBC_mass(incand_pk_ht):
	rBC_mass = 0.003043*incand_pk_ht + 0.24826 #AD corrected linear calibration for UBCSP2 at WHI 2012
	#rBC_mass = (-1.09254*10**-7)*incand_pk_ht*incand_pk_ht+0.00246*incand_pk_ht + 0.20699 #AD UNcorrected calibration for UBCSP2 at WHI 2012
	return rBC_mass

def get_coating_thickness(BC_VED,scat_amp,coating_lookup_table):
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
		if scat_amp < scattering_amp:
			scat_amp_to_use = prev_amp
			break
		prev_amp = scattering_amp

	scat_coating_thickness = coating_lookup_table[core_dia_to_use].get(scat_amp_to_use, np.nan) # returns value for the key, or none
	return scat_coating_thickness


#analysis
for row in c.execute('''SELECT incand_amp, LF_scat_amp, unix_ts_utc, sp2b_file, file_index, instr, LF_baseline_pct_diff, actual_scat_amp FROM SP2_coating_analysis 
WHERE instr=? and instr_locn=? and particle_type=? and rBC_mass_fg>=? and  rBC_mass_fg<? and unix_ts_utc>=? and unix_ts_utc<?
ORDER BY unix_ts_utc''', 
(instrument,instrument_locn,type_particle,min_rBC_mass, max_rBC_mass,begin_data,end_data)):
	particles+=1

	incand_amp = row[0]
	LEO_amp = row[1]
	event_time = datetime.utcfromtimestamp(row[2])+timedelta(hours = timezone)
	file = row[3]
	index = row[4]
	instrt = row[5]
	LF_baseline_pctdiff = row[6]
	meas_scat_amp = row[7]

	rBC_mass = get_rBC_mass(incand_amp)
	rBC_VED = (((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
	coat_thickness = get_coating_thickness(rBC_VED, LEO_amp, lookup_table)

	##
	if rBC_VED >=155 and rBC_VED <=180:
		count_155_180 += 1
	##
	
	#note particles records that can't be analysed
	if meas_scat_amp < 6 :
		no_scat +=1
		if rBC_VED >=155 and rBC_VED <=180:
			no_scat_155_180 += 1
	if meas_scat_amp >= 6 and meas_scat_amp <= 20 and LEO_amp == 0.0 and LF_baseline_pctdiff == None:
		early_evap +=1
		if rBC_VED >=155 and rBC_VED <=180:
			early_evap_155_180 +=1
		continue
	if LEO_amp == -2:
		early_evap +=1
		if rBC_VED >=155 and rBC_VED <=180:
			early_evap_155_180 +=1
		continue
	if LEO_amp == -1:
		fit_failure +=1
		continue
	if LEO_amp == 0.0 and LF_baseline_pctdiff != None:
		flat_fit +=1
		continue
	if LEO_amp > LF_max:
		LF_high +=1
		continue

	if meas_scat_amp < 6:
		coat_thickness = (91-rBC_VED)/2

	
	#trajectory clusters (converted to local time above)
	earliest_traj_time = cluslist[0][0]
	while event_time > (earliest_traj_time+timedelta(hours=1)):
		cluslist.pop(0)
		earliest_traj_time = cluslist[0][0]
		print 'clusters left', len(cluslist)

	#data for current trajectory
	traj_time_PST = cluslist[0][0]
	cluster_no  = cluslist[0][1]
	rain = cluslist[0][2]
	
	
	
	#spike times(already in local time)
	event_in_spike = False
	
	spike_half_interval = 2
	if len(spike_times):
		earliest_spike_time = spike_times[0]
		while event_time > earliest_spike_time+timedelta(minutes=spike_half_interval) and len(spike_times):
			spike_times.pop(0)
			if len(spike_times):
				earliest_spike_time = spike_times[0]
			print 'spikes left', len(spike_times)
		
		if len(spike_times):
			current_spike = spike_times[0]
			spike_start = current_spike-timedelta(minutes=spike_half_interval)
			spike_end = current_spike+timedelta(minutes=spike_half_interval)
			if (spike_start <= event_time < spike_end):
				event_in_spike = True
				if meas_scat_amp < 6 or LEO_amp > 0:
					spikes.append([rBC_VED,coat_thickness,event_time, rain])
			
	if event_in_spike == True:
		continue	

	##non-spike times
	if ((traj_time_PST-timedelta(hours=1)) <= event_time < (traj_time_PST+timedelta(hours=1))):
		if meas_scat_amp < 6 or LEO_amp > 0:
			if cluster_no == 1:
				cluster_1.append([rBC_VED,coat_thickness,event_time,rain])
			if cluster_no == 2:                                   
				cluster_2.append([rBC_VED,coat_thickness,event_time,rain])
			if cluster_no == 3:                                    
				cluster_3.append([rBC_VED,coat_thickness,event_time,rain])
			if cluster_no == 4:                                 
				cluster_4.append([rBC_VED,coat_thickness,event_time,rain])
			if cluster_no == 5:                               
				cluster_5.append([rBC_VED,coat_thickness,event_time,rain])				
			if cluster_no == 6:                                   
				cluster_6.append([rBC_VED,coat_thickness,event_time,rain])
			if cluster_no == 7:
				cluster_GBPS.append([rBC_VED,coat_thickness,event_time,rain])
			
			
	
	if (particles % LOG_EVERY_N) == 0:
		print 'record: ', particles
		
conn.close()
	
print '# of particles', particles
print 'no_scat', no_scat
print 'fit_failure', fit_failure
print 'early_evap', early_evap
print 'flat_fit', flat_fit
print 'LF_high', LF_high

print '155-180', count_155_180, no_scat_155_180, early_evap_155_180

evap_pct = (early_evap)*100.0/particles
no_scat_pct = (no_scat)*100.0/particles

print evap_pct, no_scat_pct, 

lists = [['cluster_1',cluster_1],['cluster_2',cluster_2],['cluster_3', cluster_3],['cluster_4',cluster_4],['cluster_5', cluster_5],['cluster_6',cluster_6],['cluster_GBPS',cluster_GBPS],['fresh',spikes]]


data_to_pickle = {}
for list in lists:
	air_mass_name = list[0]
	air_mass_info = list[1]
	#print air_mass_name, np.median(air_mass_info), len(list[1])
	data_to_pickle[air_mass_name] = air_mass_info
	

#save data
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating thicknesses by air mass for '+str(round(min_BC_VED,2)) +'nm to ' + str(round(max_BC_VED,2))+ 'nm-density' +str(rBC_density) + file_info +'.binpickl', 'w')
pickle.dump(data_to_pickle, file)
file.close()



