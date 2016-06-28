import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
from datetime import timedelta
import calendar
import mysql.connector



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

max_display_conc = 1000
correction_factor_for_massdistr = 1.85#set to 1 and deal with each cluster separately 1.96 #corrects for only sampling part of the mass distr +- 5%
R = 8.3144621 # in m3*Pa/(K*mol)

#get filter data
cursor.execute(('''SELECT UNIX_UTC_start_time,UNIX_UTC_end_time,daytime_EC_ngm3,nighttime_EC_ngm3 
				   FROM whi_filter_ec ''')
				  )

filter_data = cursor.fetchall()

weekly_data = []
for line in filter_data: 
	start_time = datetime.utcfromtimestamp(line[0]) + timedelta(hours = -8) #to PST
	end_time = datetime.utcfromtimestamp(line[1])
	mid_time = ((end_time-start_time)/2) + start_time
	daytime_EC_ngm3 = line[2]
	nighttime_EC_ngm3 = line[3]

	weekly_data.append([start_time,end_time,mid_time,daytime_EC_ngm3,nighttime_EC_ngm3,[],[]])
	

#get SP2 data
cursor.execute(('''SELECT bc.UNIX_GMT_ts, bc.BC_mass_conc, sc.pressure_Pa, sc.room_temp_C, bc.BC_mass_conc_LL, bc.BC_mass_conc_UL 
				   FROM whi_sp2_rbc_record_2009to2012_spikes_removed bc 
				   JOIN whi_sampling_conditions sc on bc.sampling_conditions_id = sc.id''')
				  )

SP2_data = cursor.fetchall()
record_dict = {}
for line in SP2_data:
	time = datetime.utcfromtimestamp(line[0]) + timedelta(hours = -8) #to PST
	record_hour = datetime(time.year,time.month,time.day,time.hour)
	BC_mass_conc = line[1]
	BC_mass_conc_LL = line[4]
	BC_mass_conc_UL = line[5]
	pressure = line[2]
	
	if pressure != None:
		temp = line[3] + 273.15  #C to K
		
		#calc correction factor
		volume_ambient = (R*temp)/(pressure)
		volume_STP = volume_ambient*(pressure/101325)*(273/temp)
		correction_factor_for_STP = 1#volume_ambient/volume_STP
		
		BC_mass_corr = BC_mass_conc*correction_factor_for_massdistr*correction_factor_for_STP
		BC_mass_corr_LL = BC_mass_conc_LL*correction_factor_for_massdistr*correction_factor_for_STP
		BC_mass_corr_UL = BC_mass_conc_UL*correction_factor_for_massdistr*correction_factor_for_STP
		
		mass_line = [BC_mass_corr,BC_mass_corr_LL,BC_mass_corr_UL]
		
		if record_hour not in record_dict:
			record_dict[record_hour] = []
		record_dict[record_hour].append(mass_line)                         

		
		for line in weekly_data:
			start_time = line[0]
			end_time = line[1]
			
			if start_time <= time < end_time:
				if 6 <= time.hour < 18:			#daytime
					line[5].append(mass_line)
				else:
					line[6].append(mass_line)

#hourly data
record_list=[]
for hour in record_dict:
	mean_mass = np.mean([row[0] for row in record_dict[hour]])
	record_list.append([hour,mean_mass])
record_list.sort()
hours = [row[0] for row in record_list ]
hourly_mass = [row[1] for row in record_list ]

					
#weekly data
time_to_plot = [dates.date2num(row[2]) for row in weekly_data]
filter_day = [row[3] for row in weekly_data]
filter_night = [row[4] for row in weekly_data]

SP2_means = []
for row in weekly_data:
	SP2_time = row[2]
	SP2_day_data = row[5]
	SP2_night_data = row[6]
	
	SP2_day_mean = np.mean([row[0] for row in SP2_day_data])
	SP2_day_minerr = SP2_day_mean - np.mean([row[1] for row in SP2_day_data])
	SP2_day_maxerr = np.mean([row[2] for row in SP2_day_data]) - SP2_day_mean
	
	SP2_night_mean = np.mean([row[0] for row in SP2_night_data])
	SP2_night_minerr = SP2_night_mean - np.mean([row[1] for row in SP2_night_data])
	SP2_night_maxerr = np.mean([row[2] for row in SP2_night_data]) - SP2_night_mean
	
	SP2_means.append([SP2_time,SP2_day_mean,SP2_day_minerr,SP2_day_maxerr,SP2_night_mean,SP2_night_minerr,SP2_night_maxerr])

SP2_day = [row[1] for row in SP2_means]
SP2_day_min = [row[2] for row in SP2_means]
SP2_day_max = [row[3] for row in SP2_means]
SP2_night = [row[4] for row in SP2_means]
SP2_night_min = [row[5] for row in SP2_means]
SP2_night_max = [row[6] for row in SP2_means]
	
	
fig = plt.figure(figsize=(8,12))

hfmt = dates.DateFormatter('%b')
hfmt = dates.DateFormatter('%m-%d')
display_month_interval = 1

ax1 =  plt.subplot2grid((3,1), (0,0))
ax2 =  plt.subplot2grid((3,1), (1,0))
ax3 =  plt.subplot2grid((3,1), (2,0))

ax1.scatter(hours,hourly_mass, color='grey', marker = '*',label='SP2 hourly')
ax1.scatter(time_to_plot,filter_day, color='r', marker = 'o',label='filter_day')
ax1.scatter(time_to_plot,filter_night, color='r', marker = '*',label='filter_night')
ax1.scatter(time_to_plot,SP2_day,  color='b', marker = 'o',label='SP2_day')
ax1.scatter(time_to_plot,SP2_night, color='b', marker = '*',label='SP2_night')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.DayLocator(interval = 7))
ax1.xaxis.set_visible(True)
ax1.set_xlim(dates.date2num(datetime.strptime('2009/06/20 12:00', '%Y/%m/%d %H:%M')), dates.date2num(datetime.strptime('2009/08/25', '%Y/%m/%d')))
ax1.set_ylim(0,3000)
ax1.set_xlabel('2009')
ax1.set_ylabel('EC/rBC mass concentration (ng/m3-STP)')
ax1.legend()

ax2.scatter(hours,hourly_mass, color='grey', marker = '*',label='SP2 hourly')
ax2.scatter(time_to_plot,filter_day, color='r', marker = 'o',label='filter_day')
ax2.scatter(time_to_plot,filter_night, color='r', marker = '*',label='filter_night')
ax2.scatter(time_to_plot,SP2_day,  color='b', marker = 'o',label='SP2_day')
ax2.scatter(time_to_plot,SP2_night, color='b', marker = '*',label='SP2_night')
ax2.xaxis.set_major_formatter(hfmt)
ax2.xaxis.set_major_locator(dates.DayLocator(interval = 7))
ax2.xaxis.set_visible(True)
ax2.set_xlim(dates.date2num(datetime.strptime('2010/06/01 12:00', '%Y/%m/%d %H:%M')), dates.date2num(datetime.strptime('2010/08/01', '%Y/%m/%d')))
ax2.set_xlabel('2010')
ax2.set_ylabel('EC/rBC mass concentration (ng/m3-STP)')
ax2.set_ylim(0,320)

ax3.scatter(hours,hourly_mass, color='grey', marker = '*',label='SP2 hourly')
ax3.scatter(time_to_plot,filter_day, color='r', marker = 'o',label='filter_day')
ax3.scatter(time_to_plot,filter_night, color='r', marker = '*',label='filter_night')
ax3.scatter(time_to_plot,SP2_day,color='b', marker = 'o',label='SP2_day')
ax3.scatter(time_to_plot,SP2_night, color='b', marker = '*',label='SP2_night')
ax3.xaxis.set_major_formatter(hfmt)
ax3.xaxis.set_major_locator(dates.DayLocator(interval = 7))
ax3.xaxis.set_visible(True)
ax3.set_xlim(dates.date2num(datetime.strptime('2012/04/01 12:00', '%Y/%m/%d %H:%M')), dates.date2num(datetime.strptime('2012/06/01', '%Y/%m/%d')))
ax3.set_xlabel('2012')
ax3.set_ylabel('EC/rBC mass concentration (ng/m3-STP)')
ax3.set_ylim(0,320)


plt.show()
				

				