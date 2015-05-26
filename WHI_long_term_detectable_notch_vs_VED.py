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


#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST  in LT
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST in LT



######get spike times
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times_full = pickle.load(file)
file.close()

spike_times = []
for spike in spike_times_full:
	if spike.year >= 2010:
		if spike < datetime(2012,06,01):
			spike_times.append(spike)


#set parameters
instrument_locn = 'WHI'
type_particle = 'incand'
start_date = datetime.strptime('20100111','%Y%m%d')
end_date = datetime.strptime('20120531','%Y%m%d')
rBC_density = 1.8 
incand_sat = 3750
LF_max = 45000 #above this is unreasonable

min_rBC_mass = 0.32#100-#0.94#1.63-#120 2.6-#140 3.86-#160nm 0.25-#65
min_BC_VED = (((min_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7
max_rBC_mass = 10.05#140 3.86-160 5.5-#180nm 7.55-#200 10.05-#220
max_BC_VED = (((max_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7

begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())


##############initialize binning variables
bins = []
start_size = 65 #VED in nm
end_size = 220 #VED in nm
interval_length = 5 #in nm

#create list of size bins
while start_size < end_size:    
    bins.append(start_size)
    start_size += interval_length

#create dictionary with size bins as keys
binned_data_aged = {}
for bin in bins:
	binned_data_aged[bin] = [0,0]

binned_data_fresh = copy.deepcopy(binned_data_aged)


LOG_EVERY_N = 10000
particles =0 

fit_failure = 0
flat_fit = 0
LF_high = 0

#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

for row in c.execute('''SELECT rBC_mass_fg, coat_thickness_nm, unix_ts_utc, LF_scat_amp, LF_baseline_pct_diff, sp2b_file, file_index, instr,actual_scat_amp
FROM SP2_coating_analysis 
WHERE instr_locn=? and particle_type=? and rBC_mass_fg>=? and  rBC_mass_fg<? and unix_ts_utc>=? and unix_ts_utc<?
ORDER BY unix_ts_utc''', 
(instrument_locn,type_particle, min_rBC_mass, max_rBC_mass, begin_data,end_data)):	
	particles+=1
	detectable_notch = True
	
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
	
	#if in a BB time, skip
	if (fire_time1[0] <= event_time <= fire_time1[1]) or (fire_time2[0] <= event_time <= fire_time2[1]):
		continue
		
	
	#parse if notch detectable
	if meas_scat_amp < 6 :  #no scat
		detectable_notch = False
	if meas_scat_amp >= 6 and meas_scat_amp <= 20 and LEO_amp == 0.0 and LF_baseline_pctdiff == None:   #early evap
		detectable_notch = False
	if LEO_amp == -2:  #early evap
		detectable_notch = False
		
	if LEO_amp == -1:
		fit_failure +=1
	if LEO_amp == 0.0 and LF_baseline_pctdiff != None:
		flat_fit +=1
	if LEO_amp > LF_max:
		LF_high +=1
	
	
	#spike times(local time)
	for spike in spike_times:
		spike_start = spike-timedelta(minutes=2)
		spike_end = spike+timedelta(minutes=2)
		if (spike_start <= event_time < spike_end):
			for key in binned_data_fresh:
				key_value = float(key)
				interval_end = key_value + interval_length
				if rBC_VED >= key_value and rBC_VED < interval_end:
					binned_data_fresh[key][0] = binned_data_fresh[key][0] + 1
					if detectable_notch == True:		
						binned_data_fresh[key][1] = binned_data_fresh[key][1] + 1
			
		continue
	
	
	
	for key in binned_data_aged:
		key_value = float(key)
		interval_end = key_value + interval_length
		if rBC_VED >= key_value and rBC_VED < interval_end:
			binned_data_aged[key][0] = binned_data_aged[key][0] + 1
			if detectable_notch == True:		
				binned_data_aged[key][1] = binned_data_aged[key][1] + 1

				
	
	if (particles % LOG_EVERY_N) == 0:
		print 'record: ', particles
		
conn.close()
	
print 'fit_failure', fit_failure
print 'flat_fit', flat_fit
print 'LF_high', LF_high

#agd
fractions_detectable_aged = []
for bin, counts in binned_data_aged.iteritems():
	bin_midpoint = bin + interval_length/2.0
	total_particles = counts[0]
	detectable_notches = counts[1]
	
	try:
		fraction_detectable = detectable_notches*1.0/total_particles
	except:
		fraction_detectable=np.nan
		
	fractions_detectable_aged.append([bin_midpoint,fraction_detectable])

fractions_detectable_aged.sort()

#fresh
fractions_detectable_fresh = []
for bin, counts in binned_data_fresh.iteritems():
	bin_midpoint = bin + interval_length/2.0
	total_particles = counts[0]
	detectable_notches = counts[1]
	
	try:
		fraction_detectable = detectable_notches*1.0/total_particles
	except:
		fraction_detectable=np.nan
		
	fractions_detectable_fresh.append([bin_midpoint,fraction_detectable])

fractions_detectable_fresh.sort()

#save data
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('fraction of detectable notch positions by BC core size - aged.pickl', 'w')
pickle.dump(fractions_detectable_aged, file)
file.close()

#save data
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('fraction of detectable notch positions by BC core size - fresh.pickl', 'w')
pickle.dump(fractions_detectable_fresh, file)
file.close()

##plotting

bins = [row[0] for row in fractions_detectable_aged]
fractions = [row[1] for row in fractions_detectable_aged]

binsf = [row[0] for row in fractions_detectable_aged]
fractionsf = [row[1] for row in fractions_detectable_aged]

#####plotting

fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(bins, fractions)
ax.scatter(binsf, fractionsf)
ax.set_ylabel('frctaion of detectable notch positions')
ax.set_xlabel('rBC core VED')
plt.show()      

