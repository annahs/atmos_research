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
#zero_crossing_posn FLOAT,
#UNIQUE (sp2b_file, file_index, instr)

timezone = -8

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

instrument = 'UBCSP2'
instrument_locn = 'WHI'
type_particle = 'incand'
start_date = datetime.strptime('20100401','%Y%m%d')
end_date = datetime.strptime('20120531','%Y%m%d')
rBC_density = 1.8 
incand_sat = 3750
LF_max = 45000 #above this is unreasonable

min_rBC_mass = 1.63#100-#0.94#1.63-#120 2.6-#140 3.86-#160nm 0.25-#65
max_rBC_mass = 3.86#140 3.86-160 5.5-#180nm 10.05-#220
 
VED_min = 65
VED_max = 220

scat_lim = 100

begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())

BB = []
NPac= []
SPac= []
Cont= []
LRT = []
GBPS= []


particles=0
no_scat=0 
fit_failure=0
early_evap=0
flat_fit=0
LF_high=0


for row in c.execute('''SELECT rBC_mass_fg, coat_thickness_nm, unix_ts_utc, LF_scat_amp, LF_baseline_pct_diff, sp2b_file, file_index, instr,actual_scat_amp
FROM SP2_coating_analysis 
WHERE instr_locn=? and particle_type=? and rBC_mass_fg>=? and  rBC_mass_fg<? and unix_ts_utc>=? and unix_ts_utc<?''', 
(instrument_locn,type_particle, min_rBC_mass, max_rBC_mass, begin_data,end_data)):	
	particles+=1
	
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
	
	Dp = rBC_VED + coat_thickness*2.0
	Dc = rBC_VED
	
	
	try:
		DpDc = math.pow((Dp**3/Dc**3),(1./3.))
	except:
		DpDc = np.nan
	
	
	#skip if a bad record
	if meas_scat_amp < 6 :
		no_scat +=1
	if meas_scat_amp >= 6 and LEO_amp == 0.0 and LF_baseline_pctdiff == None:
		early_evap +=1
		continue
	if LEO_amp == -2:
		early_evap +=1
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

	
	#ignore spike times	(LT)
	for spike in spike_times:
		spike_start = spike-timedelta(minutes=5)
		spike_end = spike+timedelta(minutes=5)
		if (spike_start <= event_time < spike_end):
			continue	
	
	
	#if in a BB time, put this data in BB dict
	if (fire_time1[0] <= event_time <= fire_time1[1]) or (fire_time2[0] <= event_time <= fire_time2[1]):
		BB.append(DpDc)
		continue
		
	for traj in cluslist:
		traj_time_PST = traj[0]
		cluster_no = traj[1]
		
		
		if ((traj_time_PST-timedelta(hours=3)) <= event_time < (traj_time_PST+timedelta(hours=3))):
			if meas_scat_amp < 6 or LEO_amp > 0:
				if cluster_no == 9:
					GBPS.append(DpDc)
				if cluster_no == 4:
					Cont.append(DpDc)
				if cluster_no in [6,8]:
					SPac.append(DpDc)
				if cluster_no in [2,7]:
					LRT.append(DpDc)
				if cluster_no in [1,3,5,10]:
					NPac.append(DpDc)
				
				
print len(GBPS),len(Cont),len(SPac),len(NPac),len(LRT),len(BB)
	
print '# of particles', particles
print 'no_scat', no_scat
print 'fit_failure', fit_failure
print 'early_evap', early_evap
print 'flat_fit', flat_fit
print 'LF_high', LF_high

evap_pct = (early_evap)*100.0/particles
no_scat_pct = (no_scat)*100.0/particles

print evap_pct, no_scat_pct

lists = [GBPS,Cont, NPac, SPac, LRT]

for list in lists:
	print np.median(list)

conn.close()
#####plotting

fig = plt.figure()

ax = fig.add_subplot(111)

#hist = plt.hist(BB, bins=50,histtype='step', label = 'BB')
hist = plt.hist(GBPS, bins=50,histtype='step', label = 'GBPS')
hist = plt.hist(Cont, bins=50,histtype='step', label = 'N Can')
hist = plt.hist(LRT, bins=50,histtype='step', label = 'W Pac/Asia')
hist = plt.hist(SPac, bins=50,histtype='step', label = 'S Pac')
hist = plt.hist(NPac, bins=50,histtype='step', label = 'N Pac')
plt.xlabel('frequency')
plt.xlabel('Coating Thickness (nm)')
#cb = plt.colorbar()
#cb.set_label('frequency')

plt.legend()
plt.show()      

