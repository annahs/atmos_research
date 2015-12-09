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
from matplotlib import dates
from mpl_toolkits.basemap import Basemap
import calendar
import operator


start_time = datetime(2015,4,21,15,30)
end_time = datetime(2015,4,22,0,0)
yag_min = 3.5
yag_max = 6.0
sample_flow_min = 0
sample_flow_max = 1000
sheath_flow_min = 0
sheath_flow_max = 800

UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())

timeseries_mass_data = []
timeseries_hk_data = []
timeseries_flight_data = []


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT UNIX_UTC_ts,alt from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_start_time,UNIX_end_time))
flight_data = cursor.fetchall()
for row in flight_data:
	timestamp = datetime.utcfromtimestamp(row[0])
	alt = row[1]
	timeseries_flight_data.append([timestamp,alt])

	
cursor.execute(('SELECT UNIX_UTC_ts,sample_flow,yag_power,sheath_flow,yag_xtal_temp from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_start_time,UNIX_end_time))
hk_data = cursor.fetchall()
for row in hk_data:
	time_stamp   = row[0]
	sample_flow  = row[1]
	yag_power    = row[2]
	sheath_flow  = row[3]
	yag_xtal_temp= row[4]
	
	timeseries_hk_data.append([datetime.utcfromtimestamp(row[0]),sample_flow,yag_power,sheath_flow,yag_xtal_temp])
	
	#get up empty dict for putting binned data in to calc MMD
	binned_data = {
	70:0,
	80:0,
	90:0,
	100:0,
	110:0,
	120:0,
	130:0,
	140:0,
	150:0,
	160:0,
	170:0,
	180:0,
	190:0,
	200:0,
	210:0,
	}
	
	#get data from intervals with good hk parameters
	if (yag_min <= yag_power <= yag_max) and (sample_flow_min <= sample_flow <= sample_flow_max) and (sheath_flow_min <= sheath_flow <= sheath_flow_max):
		time_min = time_stamp - 0.5
		time_max = time_stamp + 0.5
		
		#get mass conc timeseries data
		cursor.execute(('SELECT UNIX_UTC_ts,total_mass,sampled_vol from polar6_binned_mass_and_sampled_volume where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(time_min,time_max))
		mass_data = cursor.fetchall()
		
		for row in mass_data:
			timestamp = datetime.utcfromtimestamp(row[0])
			total_mass_fg = row[1]
			sampled_vol_cc = row[2]
			mass_conc = total_mass_fg/sampled_vol_cc
			
		
		#get binned data for MMD		
		cursor.execute(('SELECT 70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220 from polar6_binned_mass_and_sampled_volume where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(time_min,time_max))
		binned_db_data = cursor.fetchall()

		for row in binned_db_data:
			binned_data[70]  += row[0]
			binned_data[80]  += row[1]
			binned_data[90]  += row[2]
			binned_data[100] += row[3]
			binned_data[110] += row[4]
			binned_data[120] += row[5]
			binned_data[130] += row[6]
			binned_data[140] += row[7]
			binned_data[150] += row[8]
			binned_data[160] += row[9]
			binned_data[170] += row[10]
			binned_data[180] += row[11]
			binned_data[190] += row[12]
			binned_data[200] += row[13]
			binned_data[210] += row[14]

		##normalize
		normed_dict = {}
		for bin in binned_data:
			mass = binned_data[bin]
			norm_mass = mass/(math.log(bin+10)-math.log(bin))
			normed_dict[bin] = norm_mass
		MMD = max(normed_dict.iteritems(), key=operator.itemgetter(1))[0]
	
		timeseries_mass_data.append([timestamp,mass_conc,MMD])
		
	
mass_conc_times = [dates.date2num(row[0]) for row in timeseries_mass_data]	
mass_concs = [row[1] for row in timeseries_mass_data]
MMD = [row[2] for row in timeseries_mass_data]

hk_times = [dates.date2num(row[0]) for row in timeseries_hk_data]	
hk_yag_power = [row[2] for row in timeseries_hk_data]
hk_sample_flow = [row[1] for row in timeseries_hk_data]
hk_sheath_flow = [row[3] for row in timeseries_hk_data]

flight_data_times = [dates.date2num(row[0]) for row in timeseries_flight_data]	
flight_data_alt = [row[1] for row in timeseries_flight_data]

####plotting	
#timeseries
fig = plt.figure()

hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60

ax1 = fig.add_subplot(111)

ax1.scatter(mass_conc_times,mass_concs, color = 'b',marker='.')#,linewidth=1)
ax1.set_ylabel('mass conc (ng/m3)')
ax1.set_xlabel('time')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
ax1.set_ylim(0,200)

#ax2 = ax1.twinx()
#ax2.set_ylabel('yag_power')
#ax2.plot(hk_times,hk_sheath_flow, color='r')

#ax2 = ax1.twinx()
#ax2.set_ylabel('MMD')
#ax2.plot(mass_conc_times,MMD, color='r')

ax3 = ax1.twinx()
ax3.set_ylabel('alt')
ax3.plot(flight_data_times,flight_data_alt, color='g', linewidth=1)

#ax4 = ax1.twinx()
#ax4.set_ylabel('yag_xtal_temp')
#ax4.plot(time_stamp,yag_xtal_temp, color='m',alpha=0.2)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

#plt.savefig('NC - Polar6 - Science 10 - mass conc vs alt - 70-220nm cores - uncorrected for portion of distribution outside of sampling range.png', bbox_inches='tight') 

plt.show()
cnx.close()