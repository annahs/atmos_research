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

night_start_time = 18
night_end_time = 6

stations_to_use = ['LICENCIADO BENITO JUAREZ INTL','MEXICO (CENTRAL)   D.F.']

months_of_interest = [7,8,9]


#location:  USAF,country, lat, long, elev ,daytime RH, nightime RH, timezone, wet season RH avgs, dry season RH avgs
stations = {
'LICENCIADO BENITO JUAREZ INTL' :[766793, 'MEXICO', 19.436,  -099.072, 2229.9,{},{},-6,[],[],'red'],
'MEXICO (CENTRAL)   D.F.'    	:[766800, 'MEXICO', 19.400,  -099.183, 2303.0,{},{},-6,[],[],'blue'],
'GEOGRAFIA UNAM' 				:[766810, 'MEXICO', 19.317,  -099.183, 2278.0,{},{},-6,[],[],'green'],
}


file = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/8975896585411dat.txt'

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
		RHx = float(newline[12])
		
		timezone = stations[stn][7]
	
		date = datetime.strptime(day, '%Y%m%d')
		datetime_local = datetime.strptime(day + ' ' + hour, '%Y%m%d %H%M') + timedelta(hours = timezone)  
		

		if stn in stations.keys():
				
			#data QC
			if temp_qc in ['1','5'] and dewp_qc in ['1','5']:  #data has 'Passed all quality control checks'  #data has 'Passed all quality control checks'
				
				daytime_data = stations[stn][5]
				nighttime_data = stations[stn][6]
				
				#get daytime data
				if datetime_local.hour >= night_end_time and datetime_local.hour < night_start_time:
					if date in daytime_data:
						daytime_data[date].append(RHx)
					else:
						daytime_data[date] = [RHx]
						
				#get nighttime data up to midnight
				if datetime_local.hour >= night_start_time and datetime_local.hour < 24:
					if date in nighttime_data:
						nighttime_data[date].append(RHx)
					else:
						nighttime_data[date] = [RHx]
					
				#get nighttime data after midnight
				if datetime_local.hour >= 0 and datetime_local.hour < night_end_time:
					date_to_use = date - timedelta(days = 1)

					if date_to_use in nighttime_data:
						nighttime_data[date_to_use].append(RHx)
					else:
						nighttime_data[date_to_use] = [RHx]

				
		
combined_seasonal_and_station_data = []			
for stn in stations:
	print stn
	daytime_data = stations[stn][5]
	nighttime_data = stations[stn][6]
	
	night_count = 0
	day_count = 0

	for date, RHs in nighttime_data.iteritems():
		nighttime_avg_RH = np.mean(RHs)
		night_count +=1

		if date.month in months_of_interest:
			combined_seasonal_and_station_data.append(nighttime_avg_RH)
			
		
			
	for date, RHs in daytime_data.iteritems():
		daytime_avg_RH = np.mean(RHs)
		day_count +=1
		
		if day_count <= night_count:
			if date.month in months_of_interest:
				combined_seasonal_and_station_data.append(daytime_avg_RH)
			


#Plotting


bins_to_use = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]


fig2 = plt.figure(figsize = (8,8))

bin_number = 20
bin_range = (0,100)

label_x_pos = 0.05
label_y_pos = 0.85


ax1  = plt.subplot2grid((1,1), (0,0), colspan=1)

						

											
n,bins,patches = ax1.hist(combined_seasonal_and_station_data,bins = bins_to_use,  color='blue')
ax1.yaxis.set_visible(True)
ax1.set_ylabel('Frequency')
#ax1.text(label_x_pos, label_y_pos,'ALL STATIONS', transform=ax1.transAxes)
ax1.set_xlim(0,100)
ax1.xaxis.set_label_position('bottom')
ax1.set_xlabel('12-hr averaged %RH')




plt.subplots_adjust(hspace=0.05)


plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/Mexico_City_RH_all_stations - wet seasons - 12hr avgs.png',  bbox_inches='tight') 

#save data to file 
stn_list = ', '.join(stations_to_use)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/')

file = open('Mex City RH - wet Season for all stations - 12hr avgs.txt', 'w')
file.write('Mex City %RH - wet Season for all stations  - 12hr avgs (' + stn_list + ')' +  '\n')
file.write('0-5%' + '\t' + '5-10%' + '\t' + '10-15%' + '\t' + '15-20%' + '\t' +'20-25%' + '\t' +'25-30%' + '\t' +'30-35%' + '\t' +'35-40%' + '\t' + '40-45%' + '\t' +'45-50%' + '\t' +'50-55%' + '\t' +'55-60%' + '\t' +'60-65%' + '\t' +'65-70%' + '\t' + '70-75%' + '\t' +'75-80%' + '\t' +'80-85%' + '\t' +'85-90%' + '\t' +'90-95%' + '\t' +'95-100%'+'\n')
for row in n: 
	file.write(str(row) + '\t')
file.close()

plt.show()


