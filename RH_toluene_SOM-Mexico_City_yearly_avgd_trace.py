import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates
from matplotlib import patches
import os
import pickle
from datetime import datetime
import time
from pprint import pprint
import sys
from datetime import timedelta
from mpl_toolkits.basemap import Basemap

am_start_time = 3
am_end_time = 6

pm_start_time = 15
pm_end_time = 18

weekly = True

stations_to_use = ['LICENCIADO BENITO JUAREZ INTL','MEXICO (CENTRAL)   D.F.']



#location:  USAF,country, lat, long, elev ,daytime RH, nightime RH, timezone, wet season RH avgs, dry season RH avgs
stations = {
'LICENCIADO BENITO JUAREZ INTL' :[766793, 'MEXICO', 19.436,  -099.072, 2229.9,{},{},-6,[],[],'red'],
'MEXICO (CENTRAL)   D.F.'    	:[766800, 'MEXICO', 19.400,  -099.183, 2303.0,{},{},-6,[],[],'blue'],
'GEOGRAFIA UNAM' 				:[766810, 'MEXICO', 19.317,  -099.183, 2278.0,{},{},-6,[],[],'green'],
}


file = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/8975896585411dat.txt'

am_data = {} #also max_data
pm_data = {} #also min data

dated_data = {}

with open(file, 'r') as f:
	f.readline()
	f.readline()

	for line in f:
		
		newline = line.split(',')
		stn = newline[0].rstrip() 
		day = newline[3]
		hour = newline[4]	# in UTC	
		temp_qc = newline[9]
		dewp_qc = newline[11]
		temp = float(newline[8]) 
		RHx = float(newline[12])
		
		timezone = stations[stn][7]
	
		date = datetime.strptime(day, '%Y%m%d') 
		datetime_local = datetime.strptime(day + ' ' + hour, '%Y%m%d %H%M') + timedelta(hours = timezone)  
		day_of_year = date.timetuple().tm_yday
		week_of_year = day_of_year/7
		

		
		if stn in stations_to_use:
				
			#data QC
			if temp_qc in ['1','5'] and dewp_qc in ['1','5']:  #data has 'Passed all quality control checks'
				
				#####min/max data
				if date in dated_data:
					dated_data[date].append(RHx)
				else:
					dated_data[date] = [RHx]
						
				
					
				####am/pm data
				##get am data
				#if datetime_local.hour >= am_start_time and datetime_local.hour < am_end_time:
				#	if day_of_year in am_data:
				#		am_data[day_of_year].append(RHx)
				#	else:
				#		am_data[day_of_year] = [RHx]
				#		
				##get pm data 
				#if datetime_local.hour >= pm_start_time and datetime_local.hour < pm_end_time:
				#	if day_of_year in pm_data:
				#		pm_data[day_of_year].append(RHx)
				#	else:
				#		pm_data[day_of_year] = [RHx]	
				#	



for date, RHs in dated_data.iteritems():
	max_RH_on_date = np.max(RHs)
	min_RH_on_date = np.min(RHs)
	
	if weekly == True:
		day_of_year = date.timetuple().tm_yday/7
	else:
		day_of_year = date.timetuple().tm_yday
	
	##co=opting am and pm dicts for min max data
	if day_of_year in am_data:
		am_data[day_of_year].append(max_RH_on_date)
	else:
		am_data[day_of_year] = [max_RH_on_date]

	if day_of_year in pm_data:
		pm_data[day_of_year].append(min_RH_on_date)
	else:
		pm_data[day_of_year] = [min_RH_on_date]
	##

night_count = 0
day_count = 0

summer_pm_avgs = []
summer_am_avgs = []

for day_of_year, RHs in pm_data.iteritems():
	
	pm_avg_RH = np.mean(RHs)
	pm_10th_ptile = np.percentile(RHs, 10)
	pm_25th_ptile = np.percentile(RHs, 25)
	pm_75th_ptile = np.percentile(RHs, 75)
	pm_90th_ptile = np.percentile(RHs, 90)
	
	summer_pm_avgs.append([day_of_year,pm_avg_RH,pm_10th_ptile,pm_25th_ptile,pm_75th_ptile,pm_90th_ptile])
	night_count +=1

for day_of_year, RHs in am_data.iteritems():
	print len(RHs)
	am_avg_RH = np.mean(RHs)
	am_10th_ptile = np.percentile(RHs, 10)
	am_25th_ptile = np.percentile(RHs, 25)
	am_75th_ptile = np.percentile(RHs, 75)
	am_90th_ptile = np.percentile(RHs, 90)
	
	summer_am_avgs.append([day_of_year,am_avg_RH,am_10th_ptile,am_25th_ptile,am_75th_ptile,am_90th_ptile])
	day_count +=1

 
	
#Plotting

if weekly == True:
	uxlim = 52
	xlabel_text = 'Week of Year'
	month_incr = 4
	label_start = 2
	weeks = 52
	name = 'weekly'
	
else:
	uxlim = 365
	xlabel_text = 'Day of Year'
	month_incr = 28
	label_start = 15
	weeks = 365
	name = 'daily'

hfmt = dates.DateFormatter('%b')

pm_day_of_year = [row[0] for row in summer_pm_avgs]
pm_avgs = [row[1] for row in summer_pm_avgs]
pm_10p = [row[2] for row in summer_pm_avgs]
pm_25p = [row[3] for row in summer_pm_avgs]
pm_75p = [row[4] for row in summer_pm_avgs]
pm_90p = [row[5] for row in summer_pm_avgs]

am_day_of_year = [row[0] for row in summer_am_avgs]
am_avgs = [row[1] for row in summer_am_avgs]
am_10p = [row[2] for row in summer_am_avgs]
am_25p = [row[3] for row in summer_am_avgs]
am_75p = [row[4] for row in summer_am_avgs]
am_90p = [row[5] for row in summer_am_avgs]

fig1 = plt.figure()

ax1 =  plt.subplot2grid((1,1), (0,0))

ax1.plot(pm_day_of_year,pm_avgs, color = 'red', alpha = 1, marker = 'None')
ax1.plot(am_day_of_year,am_avgs, color='blue', alpha = 1, marker = 'None')
ax1.fill_between(pm_day_of_year, pm_10p, pm_90p, facecolor='red', alpha=0.2)
ax1.fill_between(pm_day_of_year, pm_25p, pm_75p, facecolor='red', alpha=0.3)
ax1.fill_between(am_day_of_year, am_10p, am_90p, facecolor='blue', alpha=0.2)
ax1.fill_between(am_day_of_year, am_25p, am_75p, facecolor='blue', alpha=0.3)
ax1.xaxis.set_visible(True)
ax1.yaxis.set_visible(True)
ax1.set_ylabel('%RH')
ax1.set_xlabel(xlabel_text)
ax1.set_ylim(0, 100)
ax1.set_xlim(0, uxlim)

#month labelling
label_locs = []
month_lines = []
label_loc = label_start
month_loc =  month_incr
while label_loc <= weeks:
	label_locs.append(label_loc)
	month_lines.append(month_loc)
	label_loc = label_loc + month_incr
	month_loc = month_loc + month_incr


ax2 = ax1.twiny()
new_tick_locations = np.array(label_locs)
ax2.set_xticks(new_tick_locations)
ax2.xaxis.set_tick_params(width=0)
ax2.set_xticklabels(['jan','jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])
for line in month_lines:
	ax2.axvline(line, color = 'grey')

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/Mexico_City_RH_' + name + '.png',  bbox_inches='tight') 

plt.show()



