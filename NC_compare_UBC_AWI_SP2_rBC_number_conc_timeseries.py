import sys
import os
import numpy as np
from scipy import stats
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
import matplotlib.pyplot as plt
import matplotlib.colors
from mpl_toolkits.basemap import Basemap
from matplotlib import dates
import copy

flight = 'science 3'
upper_conc_limit = 100
plot_corr_data = True
time_incr =	 30#in secs

#last number is fraction of mass distr sampled rel to AWI
flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200		]	,	
'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200		]     ,     #**
'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000	]   ,       #**
'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014	]    ,      #**
'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014	]   ,
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014	]   ,
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0		]   ,
'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81		]  ,
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5	] ,
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1			] ,
'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1	],
'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617	] ,
'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55		],
}


start_time = flight_times[flight][0]
end_time = flight_times[flight][1]

UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())



#optional hk parameters to limit retrieved records to periods where instrument was stable
yag_min = 2.8
yag_max = 6.0
sample_flow_min = 100
sample_flow_max = 200
sheath_flow_min = 400
sheath_flow_max = 800


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

UNIX_interval_start = UNIX_start_time
UNIX_interval_end = UNIX_interval_start + time_incr

icartt_data = []
plot_data = []
first_interval = True
while UNIX_interval_end <= UNIX_end_time:
	
	#check hk values
	cursor.execute(('SELECT sample_flow,yag_power,sheath_flow,yag_xtal_temp from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
	hk_data = cursor.fetchall()
	if hk_data == []:
		UNIX_interval_start += time_incr
		UNIX_interval_end += time_incr
		continue
		

	mean_sample_flow  = np.mean([row[0] for row in hk_data])
	mean_yag_power    = np.mean([row[1] for row in hk_data])
	mean_sheath_flow  = np.mean([row[2] for row in hk_data])
	mean_yag_xtal_temp= np.mean([row[3] for row in hk_data])

	
	#get data from intervals with good average hk parameters
	if (yag_min <= mean_yag_power <= yag_max) and (sample_flow_min <= mean_sample_flow <= sample_flow_max) and (sheath_flow_min <= mean_sheath_flow <= sheath_flow_max):
		
		
		#get the UBC mass conc data
		cursor.execute(('SELECT UNIX_UTC_ts,total_number,sampled_vol from polar6_binned_number_and_sampled_volume where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		number_conc_data = cursor.fetchall()
		if number_conc_data == []:
			UNIX_interval_start += time_incr
			UNIX_interval_end += time_incr
			continue
		
		mass_conc_list = []
		for row in number_conc_data:
			UNIX_ts = row[0]
			number = row[1]  
			volume = row[2]
			raw_number_conc = number/volume


			#get T and P for correction to STP
			cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_ts-0.5,UNIX_ts+0.5))
			TandP_data = cursor.fetchall()
			if TandP_data == []:
				STPcorr_number_conc = np.nan	
			else:
				temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
				pressure = TandP_data[0][1]
				correction_factor_for_STP = 1#(101325/pressure)*(temperature/273)
				STPcorr_number_conc = raw_number_conc*correction_factor_for_STP
				
			mass_conc_list.append([UNIX_ts,STPcorr_number_conc,raw_number_conc])
		
		UBC_mean_STPcorr_number_conc = np.mean([row[1] for row in mass_conc_list])
		UBC_mean_raw_number_conc = np.mean([row[2] for row in mass_conc_list])
		UBC_mean_ts = math.floor(np.mean([row[0] for row in mass_conc_list]))  #should give us the interval start or midtime :)
		
		#weird dropouts in UBC SP2 . . . . 
		if UBC_mean_raw_number_conc <=0.1:
			UBC_mean_raw_number_conc = np.nan
		if UBC_mean_STPcorr_number_conc <=0.5:
			UBC_mean_STPcorr_number_conc = np.nan
		
		
		
	
		if first_interval == True:
			plot_data.append([UBC_mean_ts,np.nan,np.nan])   
			first_interval = False
		else:
			plot_data.append([UBC_mean_ts,UBC_mean_STPcorr_number_conc,UBC_mean_raw_number_conc])
			
		
	UNIX_interval_start += time_incr
	UNIX_interval_end += time_incr
	

time_stamps = [dates.date2num(datetime.utcfromtimestamp(row[0])) for row in plot_data]
UBC_STPcorr_number_conc = [row[1] for row in plot_data]
UBC_raw_number_conc = [row[2] for row in plot_data]


cnx.close()

#plotting
hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60
if plot_corr_data == True:
	UBC_conc_to_plot = UBC_STPcorr_number_conc
	UBC_label = 'UBC SP2'
else:
	UBC_conc_to_plot = UBC_raw_number_conc
	UBC_label = 'UBC SP2 raw data'



fig = plt.figure(figsize=(12,14))
ax = fig.add_subplot(111)	
ax.plot(time_stamps,UBC_conc_to_plot,marker='s',color='g',alpha=0.5,label=UBC_label)
ax.set_ylabel('number conc (ng/m3)')
ax.set_xlabel('time')
ax.xaxis.set_major_formatter(hfmt)
ax.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
plt.xlim(dates.date2num(start_time),dates.date2num(end_time))
plt.ylim(0,upper_conc_limit)
fig.suptitle(flight, fontsize=20)
plt.legend(loc=2)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

#plt.savefig('NC - Polar6 - '+flight+' - AWI SP2 vs UBC SP2 mass concentrations-matched.png', bbox_inches='tight') 

plt.show()
##write icartt data to file

