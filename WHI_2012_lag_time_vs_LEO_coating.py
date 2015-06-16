import sqlite3
from datetime import datetime
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors
import sys
import os
import calendar
from datetime import timedelta
import pickle

conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()
instrument = 'UBCSP2'
location = 'WHI'
type_particle = 'incand' #PSL, nonincand, incand
size = 200.
start_date = datetime(2012, 4, 1)
end_date = datetime(2012, 5, 31)
start_date_ts = calendar.timegm(start_date.timetuple())
end_date_ts = calendar.timegm(end_date.timetuple())
timezone = -8


#####rows in SP2_coating_analysis table
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
#lag_time_fit_to_incand FLOAT,  #lag time in pts
#LF_baseline_pct_diff FLOAT,
#rBC_mass_fg FLOAT,
#coat_thickness_nm FLOAT,
#coat_thickness_from_actual_scat_amp FLOAT



######get spike times these are in local time
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times_full = pickle.load(file)
file.close()

spike_times = []
for spike in spike_times_full:
	if spike.year >= 2010:
		if spike < datetime(2012,06,01):
			spike_times.append(spike)

plot_data = []
	
for row in c.execute('''SELECT coat_thickness_nm, lag_time_fit_to_incand,  sp2b_file, file_index,rBC_mass_fg,unix_ts_utc FROM SP2_coating_analysis 
WHERE instr=? and particle_type=? and file_index<? and unix_ts_utc>=? and unix_ts_utc<? and rBC_mass_fg >=? and rBC_mass_fg <?
ORDER BY unix_ts_utc''', 
(instrument,type_particle, 1000 ,start_date_ts,end_date_ts,0.32,10.05)):
	coat_thickness = row[0]
	lag_time_us = row[1]*0.2
	label1 = row[2]
	label2 = row[3]
	mass = row[4]
	event_time = datetime.utcfromtimestamp(row[5])+timedelta(hours = timezone) #db is UTC, convert to LT here
	VED = (((mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7
	label = label1 + '_' + str(label2)
	
	#spike times(local time)
	spike_half_interval = 30
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
				continue
				
	plot_data.append([coat_thickness,lag_time_us,label,VED])
	
conn.close()

x_data = [row[0] for row in plot_data]
y_data = [row[1] for row in plot_data]
labels = [row[2] for row in plot_data]
VEDs = [row[3] for row in plot_data]

print 'plotting'

####plots

#	
#data = zip(x_data, y_data, labels)
#
#fig = plt.figure()
#ax = fig.add_subplot(111)
#
#for x_data, y_data, pt_label in data:
#	plt.plot(x_data, y_data, 'o', picker=5, label = pt_label)
#
#def onpick(event):
#	thisline = event.artist
#	xdata = thisline.get_xdata()
#	ydata = thisline.get_ydata()
#	label = thisline.get_label()
#	print label
#	
#fig.canvas.mpl_connect('pick_event', onpick)
#plt.xlabel('coating thickness (nm)')
#plt.ylabel('time from scattering pk to incandescence pk (us)')
#plt.show()
#
##########

fig = plt.figure()
ax = fig.add_subplot(111)
cax = ax.scatter(x_data, y_data, c=VEDs, cmap=plt.get_cmap('jet'), marker='o',)
cbar = fig.colorbar(cax)
plt.xlabel('coating thickness - from scattering max (nm)')
plt.ylabel('time from scattering pk to incandescence pk (us)')


plt.show()



######hist

#fig = plt.figure()
#ax = fig.add_subplot(111)
#ax.hist(y_data, bins=30,range=(-10,10), histtype='step', color = 'black',linewidth=1.5)
#
#
#plt.show()
