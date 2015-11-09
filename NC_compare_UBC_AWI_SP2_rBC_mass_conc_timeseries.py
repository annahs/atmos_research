import sys
import os
import numpy as np
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

flight = 'science 7'

flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200]	,	
'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014]    ,
'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014]    ,
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014]   ,
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0]   ,
'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5] ,
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1] ,
'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1],
'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617] ,
'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55],
}



start_time = flight_times[flight][0]
end_time = flight_times[flight][1]

UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())

time_incr = 1 #in secs

#optional hk parameters to limit retrieved records to periods where instrument was stable
yag_min = 2.8
yag_max = 6.0
sample_flow_min = 0
sample_flow_max = 1000
sheath_flow_min = 400
sheath_flow_max = 850


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

UNIX_interval_start = UNIX_start_time
UNIX_interval_end = UNIX_interval_start + time_incr


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
		cursor.execute(('SELECT UNIX_UTC_ts,total_mass,sampled_vol from polar6_binned_mass_and_sampled_volume where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		mass_conc_data = cursor.fetchall()
		if mass_conc_data == []:
			UNIX_interval_start += time_incr
			UNIX_interval_end += time_incr
			continue
		
		mass_conc_list = []
		for row in mass_conc_data:
			UNIX_ts = row[0]
			mass = row[1] 
			volume = row[2]
			mass_conc = mass/volume
			mass_conc_list.append([UNIX_ts,mass_conc])

		
		UBC_mean_mass_conc = np.mean([row[1] for row in mass_conc_list])
		UBC_mean_ts = math.floor(np.mean([row[0] for row in mass_conc_list]))  #should give us the interval start :)

		
		#get the AWI mass conc data
		cursor.execute(('SELECT UNIX_UTC_ts,BC_mass_conc from polar6_awi_sp2_mass_concs where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		AWI_mass_conc_data = cursor.fetchall()
		if AWI_mass_conc_data == []:
			UNIX_interval_start += time_incr
			UNIX_interval_end += time_incr
			continue
		
		AWI_mass_conc_list = []
		for row in AWI_mass_conc_data:
			AWI_UNIX_ts = row[0]
			AWI_mass_conc = row[1]*1000    #convert ug/m3 to ng/m3
			AWI_mass_conc_list.append(AWI_mass_conc)
			
		AWI_mean_mass_conc = np.mean(AWI_mass_conc_list)
		#the AWI data has some strange dropouts to large neg values
		if AWI_mean_mass_conc <0:
			AWI_mean_mass_conc = np.nan
		
		
		#flags for problems
		if len(AWI_mass_conc_list)>1:
			print 'len!!',len(AWI_mass_conc_list)
		
		if UBC_mean_ts!= AWI_UNIX_ts:
			print 'timestamp alert!'
			print 'UBC:', UBC_mean_ts
			print 'AWI:', AWI_UNIX_ts
		##
		
		#ratio
		ratio = AWI_mean_mass_conc/UBC_mean_mass_conc
		
		
		if first_interval == True:
			plot_data.append([UBC_mean_ts,np.nan,np.nan,np.nan])   ###note timestamp! I've used the interval end to match AWI, but this is a bit more complicated  . . . 
			first_interval = False
		else:
			plot_data.append([UBC_mean_ts,UBC_mean_mass_conc,AWI_mean_mass_conc,ratio])
			
	

	UNIX_interval_start += time_incr
	UNIX_interval_end += time_incr

time_stamps = [dates.date2num(datetime.utcfromtimestamp(row[0])) for row in plot_data]
UBC_mass_conc = [row[1] for row in plot_data]
AWI_mass_conc = [row[2] for row in plot_data]
ratio = [row[3] for row in plot_data]



#plotting
hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60

fig = plt.figure(figsize=(16,10))
ax = fig.add_subplot(111)	
ax.scatter(time_stamps,UBC_mass_conc,marker='o',color='b')
ax.scatter(time_stamps,AWI_mass_conc,marker='>',color='r')
#ax.plot(time_stamps,ratio,color='g')
ax.set_ylabel('mass conc (ng/m3)')
ax.set_xlabel('time')
ax.xaxis.set_major_formatter(hfmt)
ax.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
plt.xlim(dates.date2num(start_time),dates.date2num(end_time))
plt.ylim(0,250)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

#plt.savefig('NC - Polar6 - '+flight+' - median Dp-Dc vs location - 155-180nm cores - 30sec interval.png', bbox_inches='tight') 

plt.show()

cnx.close()