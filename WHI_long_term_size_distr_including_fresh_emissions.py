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
import copy


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

timezone = -8

######get spike times (these are sorted by datetime)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times_full = pickle.load(file)
file.close()

spike_times = []
for spike in spike_times_full:
	if spike.year >= 2010:
		if spike < datetime(2012,06,01):
			spike_times.append(spike)
			
#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST  in LT
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST in LT

#open cluslist and read into a python list
cluslist = []
CLUSLIST_file = 'C:/hysplit4/working/WHI/CLUSLIST_10'
with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5]))+timedelta(hours = timezone) #convert UTC->LT here
		if traj_time.year >=2010:
			cluslist.append([traj_time,cluster_no])

# sort cluslist by row_datetime in place		
cluslist.sort(key=lambda clus_info: clus_info[0])  

#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

instrument_locn = 'WHI'
type_particle = 'incand'
start_date = datetime.strptime('20100101','%Y%m%d')
end_date = datetime.strptime('20120601','%Y%m%d')
rBC_density = 1.8 
incand_sat = 3750
LF_max = 45000 #above this is unreasonable

min_rBC_mass = 0.32#100-#0.94#1.63-#120 2.6-#140 3.86-#160nm 0.25-#65
min_BC_VED = (((min_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7
max_rBC_mass = 10.05#140 3.86-160 5.5-#180nm 7.55-#200 10.05-#220
max_BC_VED = (((max_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7

begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())

#create list of size bins for size distrs
bins = []
start_size = 70 #VED in nm
end_size = 220 #VED in nm
interval_length = 5 #in nm
while start_size < end_size:    
    bins.append(start_size)
    start_size += interval_length

#create dictionary with size bins as keys
binned_data = {}
for bin in bins:
	binned_data[bin] = [0,0]
	
rBC_FT_data_cluster_NPac = copy.deepcopy(binned_data)
rBC_FT_data_cluster_SPac = copy.deepcopy(binned_data)
rBC_FT_data_cluster_Cont = copy.deepcopy(binned_data)
rBC_FT_data_cluster_LRT = copy.deepcopy(binned_data)
rBC_FT_data_cluster_GBPS = copy.deepcopy(binned_data)
rBC_FT_data_fresh_emissions = copy.deepcopy(binned_data)

#start data analysis
event_in_spike = False
LOG_EVERY_N = 10000
i=0
for row in c.execute('''SELECT rBC_mass_fg, coat_thickness_nm, unix_ts_utc, LF_scat_amp, LF_baseline_pct_diff, sp2b_file, file_index, instr,actual_scat_amp
FROM SP2_coating_analysis 
WHERE instr_locn=? and particle_type=? and rBC_mass_fg>=? and  rBC_mass_fg<? and unix_ts_utc>=? and unix_ts_utc<?
ORDER BY unix_ts_utc''', 
(instrument_locn,type_particle, min_rBC_mass, max_rBC_mass, begin_data,end_data)):	
	i+=1
	rBC_mass = row[0]
	coat_thickness = row[1]
	event_time = datetime.utcfromtimestamp(row[2])+timedelta(hours = timezone) #db is UTC, convert to LT here
	LEO_amp = row[3]
	LF_baseline_pctdiff = row[4]
	file = row[5]
	index = row[6]
	instrt = row[7]
	meas_scat_amp = row[8]
	rBC_VED = (((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
	
	#if in a BB time, ignore
	if (fire_time1[0] <= event_time <= fire_time1[1]) or (fire_time2[0] <= event_time <= fire_time2[1]):
		continue
	
	#spike times(local time)
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
				for key in rBC_FT_data_fresh_emissions:
					key_value = float(key)
					interval_end = key_value + interval_length
					if rBC_VED >= key_value and rBC_VED < interval_end:
						rBC_FT_data_fresh_emissions[key][0] = rBC_FT_data_fresh_emissions[key][0] + rBC_mass
						rBC_FT_data_fresh_emissions[key][1] = rBC_FT_data_fresh_emissions[key][1] + 1
					
	if event_in_spike == True:
		continue	
	
	
	
	#trajectory clusters
	earliest_traj_time = cluslist[0][0]
	while event_time > earliest_traj_time:
		cluslist.pop(0)
		earliest_traj_time = cluslist[0][0]
		print 'clusters left', len(cluslist)
	
	
	for traj in cluslist:
		traj_time_PST = traj[0]
		cluster_no = traj[1]
			
		if ((traj_time_PST-timedelta(hours=3)) <= event_time < (traj_time_PST+timedelta(hours=3))):
			if cluster_no == 9:
				for key in rBC_FT_data_cluster_GBPS:
					key_value = float(key)
					interval_end = key_value + interval_length
					if rBC_VED >= key_value and rBC_VED < interval_end:
						rBC_FT_data_cluster_GBPS[key][0] = rBC_FT_data_cluster_GBPS[key][0] + rBC_mass
						rBC_FT_data_cluster_GBPS[key][1] = rBC_FT_data_cluster_GBPS[key][1] + 1
						
			if cluster_no == 4:
				for key in rBC_FT_data_cluster_Cont:
					key_value = float(key)
					interval_end = key_value + interval_length
					if rBC_VED >= key_value and rBC_VED < interval_end:
						rBC_FT_data_cluster_Cont[key][0] = rBC_FT_data_cluster_Cont[key][0] + rBC_mass
						rBC_FT_data_cluster_Cont[key][1] = rBC_FT_data_cluster_Cont[key][1] + 1
						
			if cluster_no in [6,8]:
				for key in rBC_FT_data_cluster_SPac:
					key_value = float(key)
					interval_end = key_value + interval_length
					if rBC_VED >= key_value and rBC_VED < interval_end:
						rBC_FT_data_cluster_SPac[key][0] = rBC_FT_data_cluster_SPac[key][0] + rBC_mass
						rBC_FT_data_cluster_SPac[key][1] = rBC_FT_data_cluster_SPac[key][1] + 1
						
			if cluster_no in [2,7]:
				for key in rBC_FT_data_cluster_LRT:
					key_value = float(key)
					interval_end = key_value + interval_length
					if rBC_VED >= key_value and rBC_VED < interval_end:
						rBC_FT_data_cluster_LRT[key][0] = rBC_FT_data_cluster_LRT[key][0] + rBC_mass
						rBC_FT_data_cluster_LRT[key][1] = rBC_FT_data_cluster_LRT[key][1] + 1
						
			if cluster_no in [1,3,5,10]:
				for key in rBC_FT_data_cluster_NPac:
					key_value = float(key)
					interval_end = key_value + interval_length
					if rBC_VED >= key_value and rBC_VED < interval_end:
						rBC_FT_data_cluster_NPac[key][0] = rBC_FT_data_cluster_NPac[key][0] + rBC_mass
						rBC_FT_data_cluster_NPac[key][1] = rBC_FT_data_cluster_NPac[key][1] + 1
			
	
	if (i % LOG_EVERY_N) == 0:
		print 'record: ', i
		
conn.close()

lists = [['GBPS',rBC_FT_data_cluster_GBPS],['Cont',rBC_FT_data_cluster_Cont], ['NPac', rBC_FT_data_cluster_NPac], ['SPac',rBC_FT_data_cluster_SPac], ['LRT', rBC_FT_data_cluster_LRT], ['fresh',rBC_FT_data_fresh_emissions]]


data_to_pickle = {}
for list in lists:
	air_mass_name = list[0]
	air_mass_info = list[1]
	data_to_pickle[air_mass_name] = air_mass_info
	

#save data
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('raw size and number distributions by air mass for '+str(round(min_BC_VED,2)) +'nm to ' + str(round(max_BC_VED,2))+'nm.binpickl', 'w')
pickle.dump(data_to_pickle, file)
file.close()
	



