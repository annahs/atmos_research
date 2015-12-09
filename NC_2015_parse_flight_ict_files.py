import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import calendar
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.colors
import math
from matplotlib import dates
import sqlite3

flight = 'science 8'


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



start_coating_data = flight_times[flight][0]
end_coating_data = flight_times[flight][1]


#set parameters
instrument_locn = 'POLAR6'
type_particle = 'incand'
min_BC_VED = 155.
max_BC_VED = 180.
binning_half_interval = timedelta(minutes=0.25)

min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

begin_data = calendar.timegm(start_coating_data.timetuple())
end_data = calendar.timegm(end_coating_data.timetuple())

ict_files = [
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04050943Polar6_20150405_R0_V1.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04051303Polar6_20150405_R0_V2.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04081351Polar6_20150408_R0_V1.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04081752Polar6_20150408_R0_V2.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04091350Polar6_20150409_R0.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04101428Polar6_20150410_R0_V1.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04101538Polar6_20150410_R0_V2.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04111557Polar6_20150411_R0_V1.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04111803Polar6_20150411_R0_V2.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04131514Polar6_20150413_R0.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04172122Polar6_20150417_R0.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04201549Polar6_20150420_R0_V1.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04202145Polar6_20150420_R0_V2.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04210021Polar6_20150421_R0_V1.ict',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/AIMMS_04211608Polar6_20150421_R0_V2.ict',
]

#connect to database and get coating data
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

first_data_pt = True
coating_data = []
temp = []
for row in c.execute('''SELECT coat_thickness_nm, unix_ts_utc, rBC_mass_fg
FROM SP2_coating_analysis 
WHERE instr_locn=? and particle_type=? and rBC_mass_fg >=? and rBC_mass_fg <? and unix_ts_utc>? and unix_ts_utc<=?
ORDER BY unix_ts_utc''', 
(instrument_locn,type_particle, min_rBC_mass, max_rBC_mass,begin_data,end_data )):	
	coat_th = row[0]
	if coat_th != None:
		
		event_time = datetime.utcfromtimestamp(row[1])
		
		if first_data_pt == True:
			bin_center = event_time + binning_half_interval
			first_data_pt = False
			
		rBC_mass = row[2]
		rBC_density = 1.8
		rBC_VED =(((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7
		dp_dc = (rBC_VED+2*coat_th)/rBC_VED
		
		if (bin_center-binning_half_interval) < event_time <=  (bin_center+binning_half_interval):
			temp.append(dp_dc)
		
		if event_time > (bin_center+binning_half_interval):
			mean=np.mean(temp)
			temp=[]
			coating_data.append([bin_center,mean])
			bin_center = event_time + binning_half_interval
			
conn.close()



coating_time = [dates.date2num(row[0]) for row in coating_data]
coating = [row[1] for row in coating_data]


#flight data
flight_data = []

for ict_file in ict_files:
	with open(ict_file,'r') as f:
		i=0
		while i < 7:
			line = f.readline()
			i+=1
		
		newline = line.split(',') #the seventh line is the date
		file_year = int(newline[0])
		file_month = int(newline[1])
		file_day = int(newline[2])
		
				
	
	
		data_start = False
		for line in f:
			newline = line.split(',')
			
			if data_start == True:
			
				
				Temp = float(newline[2])
				RH = float(newline[3])
				lat = float(newline[7])
				lon = float(newline[8]) 
				alt = float(newline[9]) 
				
				time_hours = float(newline[1])
				time_minutes = time_hours * 60
				time_seconds = time_minutes * 60

				hours_part   = int(math.floor(time_hours))
				minutes_part = int(math.floor(time_minutes % 60))
				seconds_part = int(math.floor(time_seconds % 60))
				
				

				try:
					date_time = datetime(file_year,file_month,file_day, hours_part,minutes_part,seconds_part)
				except:
					continue
				
				if start_coating_data <= date_time < end_coating_data:
				
					flight_data.append([date_time, Temp, RH, lat, lon, alt ])
				

			if newline[0] == 'TimeWave' and newline[1] == 'Time_Hr':
				data_start = True


			
time = [dates.date2num(row[0]) for row in flight_data]
temp = [row[1] for row in flight_data]
RH = [row[2] for row in flight_data]
alt = [row[5] for row in flight_data]
	
	
	
	
####plotting	
#timeseries
fig = plt.figure()

hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60

ax1 = fig.add_subplot(111)

ax1.scatter(coating_time,coating, c=coating, cmap=plt.get_cmap('jet'),marker='o')#,linewidth=1)
ax1.set_ylabel('coat (dp/dc)')
ax1.set_xlabel('time')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
ax1.set_ylim(0.85,2.5)

ax2 = ax1.twinx()
ax2.set_ylabel('alt')
ax2.scatter(time,alt, color='k',)
ax2.set_ylim(0,6000)

#ax3 = ax1.twinx()
#ax3.set_ylabel('TEMP')
#ax3.plot(time,temp, color='r', linewidth=1)

#ax4 = ax1.twinx()
#ax4.set_ylabel('RH')
#ax4.plot(time,RH, color='b')

plt.show()
sys.exit()
#map

fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(111)

#m = Basemap(width=1000000,height=700000,resolution='l',projection='laea',lat_ts=80,lat_0=80,lon_0=-90.)
m = Basemap(projection='npstere',boundinglat=65,lon_0=270,resolution='l')

m.drawparallels(np.arange(-80.,90.,10.))
m.drawmeridians(np.arange(-180.,181.,20.))
	

m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()

lats = [row[3] for row in flight_data]
lons = [row[4] for row in flight_data]
x,y = m(lons,lats)

bt = m.plot(x,y,linewidth=2)

plt.show()

	