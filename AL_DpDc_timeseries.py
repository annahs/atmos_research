import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.cm as cm
from matplotlib import dates
import calendar


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()



start_date = datetime(2012,3,27)
end_date =   datetime(2014,1,1)
hour_step = 6

min_BC_VED = 160
max_BC_VED = 180
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

timeseries = []
while start_date < end_date:
	print start_date
	period_end = start_date + timedelta(hours = hour_step)
	UNIX_start_time = calendar.timegm(start_date.utctimetuple())
	UNIX_end_time   = calendar.timegm(period_end.utctimetuple())


	cursor.execute(('''SELECT rBC_mass_fg,coat_thickness_nm_min,coat_thickness_nm_max, LF_scat_amp 
						FROM alert_leo_coating_data 
						WHERE UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and HK_flag = 0 and rBC_mass_fg >= %s and rBC_mass_fg<%s '''),
						(UNIX_start_time,UNIX_end_time, min_rBC_mass,max_rBC_mass))
	coat_data = cursor.fetchall()

	#hexbin plot
	interval_data_min = []
	interval_data_max = []
	for row in coat_data:
		mass = row[0] 
		coat_min = row[1]
		coat_max = row[2]
		LEO_amp = row[3]	
		
		if coat_min != None and coat_max!= None and LEO_amp > 100:
			core_VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
			particle_min_VED = core_VED + 2*coat_min
			particle_max_VED = core_VED + 2*coat_max
			Dp_Dc_min = particle_min_VED/core_VED
			Dp_Dc_max = particle_max_VED/core_VED
			interval_data_min.append(coat_min)
			interval_data_max.append(coat_max)
	
	timepoint = start_date + timedelta(hours = hour_step/2)
	mean_DpDc_min = np.mean(interval_data_min)
	mean_DpDc_max = np.mean(interval_data_max)
	timeseries.append([timepoint,mean_DpDc_min,mean_DpDc_max])
	
	start_date = start_date + timedelta(hours = hour_step)
	
cnx.close()

date_pt = [dates.date2num(row[0]) for row in timeseries]
DpDc_min = [row[1] for row in timeseries]
DpDc_max = [row[2] for row in timeseries]


#plotting
fig = plt.figure(figsize=(12,8))
ax1 = fig.add_subplot(211)

hfmt = dates.DateFormatter('%Y-%m-%d')

ax1.plot(date_pt,DpDc_min, marker = 'o',color='b')
ax1.set_xlabel('date')
ax1.set_ylabel('avg coating thickness\n (' + str(min_BC_VED) + '-' + str(max_BC_VED) + 'nm rBC cores)')
ax1.xaxis.set_major_formatter(hfmt)
ax1.set_xlim(dates.date2num(datetime(2012,4,1)), dates.date2num(datetime(2012,5,1)))
ax1.set_ylim(0,80)

ax2 = fig.add_subplot(212)
ax2.plot(date_pt,DpDc_max, marker = 'o',color='r',label = 'maximum coat')
ax2.plot(date_pt,DpDc_min, marker = 'o',color='b',label = 'minimum coat')
ax2.set_xlabel('date')
ax2.set_ylabel('avg coating thickness\n (' + str(min_BC_VED) + '-' + str(max_BC_VED) + 'nm rBC cores)')
ax2.xaxis.set_major_formatter(hfmt)
ax2.set_xlim(dates.date2num(datetime(2013,10,1)), dates.date2num(datetime(2013,12,1)))
ax2.set_ylim(0,80)
plt.legend()
plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/seasonal coating/coating 6hr avgs.png', bbox_inches='tight')

plt.show()     
	
