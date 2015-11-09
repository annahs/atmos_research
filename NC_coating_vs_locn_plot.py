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
import copy

flight = 'ferry 3'

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
time_incr = 30 #in secs

min_BC_VED = 155
max_BC_VED = 180

yag_min = 2.8
yag_max = 6.0
sample_flow_min = 0
sample_flow_max = 1000
sheath_flow_min = 400
sheath_flow_max = 850


UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())


min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

UNIX_interval_start = UNIX_start_time

plot_data = []
first_interval = True
while UNIX_interval_start <= UNIX_end_time:
	UNIX_interval_end = UNIX_interval_start + time_incr

	#check hk values
	cursor.execute(('SELECT sample_flow,yag_power,sheath_flow,yag_xtal_temp from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
	hk_data = cursor.fetchall()
	if hk_data == []:
		UNIX_interval_start += time_incr
		continue
		

	mean_sample_flow  = np.mean([row[0] for row in hk_data])
	mean_yag_power    = np.mean([row[1] for row in hk_data])
	mean_sheath_flow  = np.mean([row[2] for row in hk_data])
	mean_yag_xtal_temp= np.mean([row[3] for row in hk_data])

	
	#get data from intervals with good average hk parameters
	if (yag_min <= mean_yag_power <= yag_max) and (sample_flow_min <= mean_sample_flow <= sample_flow_max) and (sheath_flow_min <= mean_sheath_flow <= sheath_flow_max):
		
		###get the lat, lon and alt means
		cursor.execute(('SELECT lat, lon, alt, UNIX_UTC_ts from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		lat_lon_data = cursor.fetchall()
		lats = [row[0] for row in lat_lon_data]
		lons = [row[1] for row in lat_lon_data]
		alts = [row[2] for row in lat_lon_data]
		UNIX_ts = [row[3] for row in lat_lon_data]

		lat_pt = np.mean(lats)
		lon_pt = np.mean(lons)
		alt_pt =  np.mean(alts)
		time_pt = np.mean(UNIX_ts)

		
		###get the coating data
		cursor.execute(('SELECT rBC_mass_fg,coat_thickness_nm  from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and rBC_mass_fg >= %s and rBC_mass_fg < %s and particle_type = %s and instrument = %s'),(UNIX_interval_start,UNIX_interval_end,min_rBC_mass,max_rBC_mass,'incand','UBCSP2'))
		coating_data = cursor.fetchall()
		if coating_data == []:
			UNIX_interval_start += time_incr
			continue
		Dp_Dc_list = []
		for row in coating_data:
			rBC_mass = row[0]
			coat_th = row[1]
			core_VED = (((rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7
			try:
				Dp_Dc = ((2*coat_th)+core_VED)/core_VED
				Dp_Dc_list.append(Dp_Dc)
			except:
				continue
		
		median_Dp_Dc = np.median(Dp_Dc_list)
		
		#get the mass conc data
		cursor.execute(('SELECT total_mass,sampled_vol from polar6_binned_mass_and_sampled_volume where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		mass_conc_data = cursor.fetchall()
		mass_conc_list = []
		for row in mass_conc_data:
			mass = row[0] 
			volume = row[1]
			mass_conc = mass/volume
			mass_conc_list.append(mass_conc)

		mean_mass_conc = np.mean(mass_conc_list)

		if first_interval == True:
			plot_data.append([lat_pt, lon_pt,alt_pt, median_Dp_Dc,time_pt,np.nan])
			first_interval = False
		else:
			plot_data.append([lat_pt, lon_pt,alt_pt, median_Dp_Dc,time_pt,mean_mass_conc])
			
	UNIX_interval_start += time_incr

#Add some HYSPIT bts
bt_files = [
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/HYSPLIT/tdump20150421_1630',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/HYSPLIT/tdump20150421_1800',
'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/HYSPLIT/tdump20150421_2030',
]

bts = []

for file in bt_files:

	tdump_file = open(file, 'r')
	endpoints = []
	data_start = False

	i=0
	for line in tdump_file:
		newline = line.split()

		if data_start == True:
			lat = float(newline[9])
			lon = float(newline[10])
			height = float(newline[11])
		
			endpoint = [lat, lon,height]
			endpoints.append(endpoint)
			i+=1
			
		if newline[1] == 'PRESSURE':
			data_start = True
	
	tdump_file.close() 

	bts.append(endpoints)
		
map_width = 300000
map_height = 300000

if flight in ['science 6','science 7','ferry 3']:
	map_width = 500000
	map_height = 400000

fig = plt.figure(figsize=(14,8))
ax = fig.add_subplot(211)	
	
###set up the basemap instance  
lat_pt = flight_times[flight][3]			
lon_pt = flight_times[flight][2]

m = Basemap(width=map_width,height=map_height,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=100.,projection='lcc',
			lat_1=75.,lat_2=85,lat_0=lat_pt,lon_0=lon_pt)

##rough shapes 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
m.drawmapboundary(fill_color='#ABD9E9')
#m.bluemarble()

##meridians
#parallels = np.arange(60.,90,1)
#m.drawparallels(parallels,labels=[False,True,True,False])
#meridians = np.arange(10.,351.,10)
#m.drawmeridians(meridians,labels=[False,False,False,True])

#flight data
lats = [row[0] for row in plot_data]
lons = [row[1] for row in plot_data]
alts = [row[2]/100 for row in plot_data]
dp_dcs = [row[3] for row in plot_data]
x,y = m(lons,lats)
flight_plot = m.scatter(x,y, c=dp_dcs, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o', s=alts,)

cb = plt.colorbar()
cb.set_label('Dp/Dc', rotation=270,labelpad=14)

#city labels

if flight in ['science 1','ferry 1']:
	city_x,city_y = m(15.6500, 78.2200) 
	plt.text(city_x-5000,city_y+10000,'Longyearbyen')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['ferry 2']:
	city_x,city_y = m(-16.6667, 81.6000) 
	plt.text(city_x-5000,city_y+10000,'Station Nord')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['science 8','science 9','science 10']:
	city_x,city_y = m(-133.7306, 68.3617)
	plt.text(city_x-5000,city_y+10000,'Inuvik')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['science 6','science 7', 'ferry 4']:
	city_x,city_y = m(-85.9408, 79.9889)
	plt.text(city_x-5000,city_y+10000,'Eureka')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['science 2','science 3','science 4','science 5','ferry 3']:
	city_x,city_y = m(-62.338, 82.5014) 
	plt.text(city_x-5000,city_y+10000,'Alert')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)




#mass conc plot
ax = fig.add_subplot(221)	
	
###set up the basemap instance  
lat_pt = flight_times[flight][3]			
lon_pt = flight_times[flight][2]

m = Basemap(width=map_width,height=map_height,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=100.,projection='lcc',
			lat_1=75.,lat_2=85,lat_0=lat_pt,lon_0=lon_pt)

##rough shapes 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
m.drawmapboundary(fill_color='#ABD9E9')
#m.bluemarble()

##meridians
#parallels = np.arange(60.,90,1)
#m.drawparallels(parallels,labels=[False,True,True,False])
#meridians = np.arange(10.,351.,10)
#m.drawmeridians(meridians,labels=[False,False,False,True])

#flight data
lats = [row[0] for row in plot_data]
lons = [row[1] for row in plot_data]
alts = [row[2]/100 for row in plot_data]
mass_concs = [row[5] for row in plot_data]
x,y = m(lons,lats)
flight_plot = m.scatter(x,y, c=mass_concs, cmap=plt.get_cmap('Greys'),edgecolors='none', marker = 'o', s=alts,)

cb = plt.colorbar()
cb.set_label('rBC mass conc (ng/m3)', rotation=270,labelpad=14)

#city labels
if flight in ['science 1','ferry 1']:
	city_x,city_y = m(15.6500, 78.2200) 
	plt.text(city_x-5000,city_y+10000,'Longyearbyen')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['ferry 2']:
	city_x,city_y = m(-16.6667, 81.6000) 
	plt.text(city_x-5000,city_y+10000,'Station Nord')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['science 8','science 9','science 10']:
	city_x,city_y = m(-133.7306, 68.3617)
	plt.text(city_x-5000,city_y+10000,'Inuvik')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['science 6','science 7', 'ferry 4']:
	city_x,city_y = m(-85.9408, 79.9889)
	plt.text(city_x-5000,city_y+10000,'Eureka')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

if flight in ['science 2','science 3','science 4','science 5','ferry 3']:
	city_x,city_y = m(-62.338, 82.5014) 
	plt.text(city_x-5000,city_y+10000,'Alert')
	m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)



###
dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

plt.savefig('NC - Polar6 - '+flight+' - median Dp-Dc vs location - 155-180nm cores - 30sec interval.png', bbox_inches='tight') 

plt.show()


	
###plot dp/dc as function of alt
altitudes = [row[2] for row in plot_data]
dp_dc_values = [row[3] for row in plot_data]
mass_conc_values = [row[5] for row in plot_data]


fig = plt.figure(figsize=(8,10))

ax1 = fig.add_subplot(211)
ax1.scatter(dp_dc_values,altitudes,c=dp_dc_values, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o',)
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel('Dp/Dc')
ax1.set_ylim(0,6000)
ax1.set_xlim(0.8,2.4)

ax2 = fig.add_subplot(212)
ax2.set_xlabel('rBC mass concentration (ng/m3)')
ax2.set_ylabel('altitude (m)')
ax2.scatter(mass_conc_values,altitudes, color='grey')
ax2.set_xlim(0,100)
if flight in ['science 8']:
	ax2.set_xlim(0,200)
	
ax2.set_ylim(0,6000)


plt.savefig('NC - Polar6 - '+flight+' - median Dp-Dc vs alt for 155-180nm cores - mean rBC mass conc vs alt - 30sec interval.png', bbox_inches='tight') 


plt.show()

	
	
cnx.close()