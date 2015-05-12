import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from matplotlib import dates
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
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5])) 
		if traj_time.year >=2010:
			cluslist.append([traj_time,cluster_no])

#sort cluslist by row_datetime in place		
cluslist.sort(key=lambda clus_info: clus_info[0])  

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

#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

instrument = 'UBCSP2'
instrument_locn = 'WHI'
type_particle = 'incand'
rBC_density = 1.8 
LF_max = 45000
min_rBC_mass = 0.25#100-#0.94#1.63-#120 2.6-#140 3.86-#160nm 0.25-#65
max_rBC_mass = 10.05#140 3.86-160 5.5-#180nm 10.05-#220
coat_min = 120
coat_max = 160

particles=0
no_scat=0 
fit_failure=0
early_evap=0
flat_fit=0
LF_high=0

overall_data = []
for traj in cluslist:
	traj_time_UTC = traj[0]
	traj_time_PST = traj_time_UTC+timedelta(hours = timezone)
	cluster_no = traj[1]
	print traj_time_PST, cluster_no
	
	traj_start = traj_time_UTC-timedelta(hours=3) #use UTC to retrieve data b/c table dates are in UTC
	traj_end = traj_time_UTC+timedelta(hours=3)

	begin_data = calendar.timegm(traj_start.timetuple())
	end_data = calendar.timegm(traj_end.timetuple())

	coating_data = []
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

		#ignore any spike times	(LT)
		for spike in spike_times:
			spike_start = spike-timedelta(minutes=5)
			spike_end = spike+timedelta(minutes=5)
			if (spike_start <= event_time < spike_end):
				continue
		
		#then get the mass distributions for all particles
		for key in binned_data:
			key_value = float(key)
			interval_end = key_value + interval_length
			if rBC_VED >= key_value and rBC_VED < interval_end:
				binned_data[key][0] = binned_data[key][0] + rBC_mass
				binned_data[key][1] = binned_data[key][1] + 1

		#now get the available coating data
		
		#skip if not a good LEO record
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

		#if in a BB time,skip
		if (fire_time1[0] <= event_time <= fire_time1[1]) or (fire_time2[0] <= event_time <= fire_time2[1]):
			continue
			
		#collect good coating data
		if rBC_VED >= coat_min and rBC_VED <coat_max:
			if meas_scat_amp < 6:
				coat_thickness = 0.0
			
			if meas_scat_amp < 6 or LEO_amp > 0:
				Dp = rBC_VED + coat_thickness*2.0
				Dc = rBC_VED
				coating_data.append([Dp,Dc])

	#get dp/dc for traj
	Dp_vals = [row[0] for row in coating_data]
	Dc_vals = [row[1] for row in coating_data]
	
	sum_of_Dp_cubes = 0
	for Dp in Dp_vals:
		sum_of_Dp_cubes = sum_of_Dp_cubes + Dp**3	
		
	sum_of_Dc_cubes = 0
	for Dc in Dc_vals:
		sum_of_Dc_cubes = sum_of_Dc_cubes + Dc**3
	
	try:
		DpDc = math.pow((sum_of_Dp_cubes/sum_of_Dc_cubes),(1./3.))
	except:
		DpDc = np.nan
		print 'Dp/Dc', sum_of_Dp_cubes, sum_of_Dc_cubes
		
		
	#fiddle with mass distrs (sort, etc)   
	mass_distr_list = []
	for bin, value in binned_data.iteritems():
		bin_mass = value[0]
		bin_numb = value[1]
		temp = [bin,bin_mass,bin_numb]
		mass_distr_list.append(temp)
	mass_distr_list.sort()
	
	for row in mass_distr_list: 	#normalize
		row.append(row[1]) #these 2 lines append teh raw mass and number concs
		row.append(row[2]) 
		row[1] = row[1]/(math.log(row[0]+interval_length)-math.log(row[0])) #d/dlog(VED)
		row[2] = row[2]/(math.log(row[0]+interval_length)-math.log(row[0])) #d/dlog(VED)
		row[0] = row[0]+interval_length/2 #correction for our binning code recording bin starts as keys instead of midpoints
		
		
	overall_data.append([traj_time_PST,cluster_no,DpDc,mass_distr_list])

	binned_data = {}
	for bin in bins:
		binned_data[bin] = [0,0]
		
		
conn.close()

print '# of particles', particles
print 'no_scat', no_scat
print 'fit_failure', fit_failure
print 'early_evap', early_evap
print 'flat_fit', flat_fit
print 'LF_high', LF_high

evap_pct = (early_evap)*100.0/particles
no_scat_pct = (no_scat)*100.0/particles

print evap_pct, no_scat_pct

#save overall_data
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('MMD_and_coating_data.binpickl', 'w')
pickle.dump(overall_data, file)
file.close()


#####plotting


datetimes =  [dates.date2num(row[0]) for row in overall_data]
DpDc = [row[2] for row in overall_data] 

fire_span1_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')
fire_alpha = 0.25
fire_color = '#990000'

fig = plt.figure(figsize=(11.5,7.5))

hfmt = dates.DateFormatter('%b')
#hfmt = dates.DateFormatter('%m-%d')

display_month_interval = 1

startdate_2010 = '2010/05/31'
enddate_2010 = '2010/08/04'

startdate_2012 = '2012/03/29'
enddate_2012 = '2012/06/05'

                           
ax7 =  plt.subplot2grid((4,2), (0,0), colspan=1,rowspan = 2)
ax8 =  plt.subplot2grid((4,2), (0,1), colspan=1,rowspan = 2, sharey=ax7)
										
#ax10 = plt.subplot2grid((4,2), (2,0), colspan=1,rowspan = 2)
#ax11 = plt.subplot2grid((4,2), (2,1), colspan=1,rowspan = 2, sharey=ax10)
											

ax7.plot(datetimes,DpDc, marker = 'o')
ax7.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax7.xaxis.set_visible(True)
ax7.yaxis.set_visible(True)
ax7.set_ylabel('Dp/Dc')
ax7.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax7.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax7.text(0.1, 0.9,'2010', transform=ax7.transAxes)


ax8.plot(datetimes,DpDc, marker = 'o')
ax8.xaxis.set_major_formatter(hfmt)
ax8.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax8.xaxis.set_visible(True)
ax8.yaxis.set_visible(False)
ax8.set_xlabel('month')
ax8.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax8.text(0.1, 0.9,'2012', transform=ax8.transAxes)


#legend = ax8.legend(loc='upper center', bbox_to_anchor=(0.5, 1.275), ncol=3, numpoints=1)

plt.show()
