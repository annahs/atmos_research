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

start_time = datetime(2015,4,20,15,30)
end_time = datetime(2015,4,20,20,0) 
time_incr = 30 #in secs

min_BC_VED = 155
max_BC_VED = 180


UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())


min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

UNIX_interval_start = UNIX_start_time

plot_data = []
while UNIX_interval_start <= UNIX_end_time:
	
	
	UNIX_interval_end = UNIX_interval_start + time_incr
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
	
	#if math.isnan(lat_pt) == False:
	#	print datetime.utcfromtimestamp(UNIX_interval_start)
	#	print lat_pt, lon_pt
	
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
	
	mean_Dp_Dc = np.mean(Dp_Dc_list)
	
	plot_data.append([lat_pt, lon_pt,alt_pt, mean_Dp_Dc,time_pt ])
	
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
		
	
	
###set up the basemap instance  
lat_pt = 67.
lon_pt = -131.

m = Basemap(width=400000,height=600000,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=100.,projection='lcc',
			lat_1=75.,lat_2=85,lat_0=lat_pt,lon_0=lon_pt)
	
#m = Basemap(projection='npstere',boundinglat=75,lon_0=270,resolution='l')
	
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(111)
#
##rough shapes 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
m.drawmapboundary(fill_color='#ABD9E9')
#m.bluemarble()

#meridians
parallels = np.arange(60.,85,2)
m.drawparallels(parallels,labels=[False,True,True,False])
meridians = np.arange(10.,351.,2.)
m.drawmeridians(meridians,labels=[False,False,False,True])

#flight data
lats = [row[0] for row in plot_data]
lons = [row[1] for row in plot_data]
alts = [row[2]/100 for row in plot_data]
dp_dcs = [row[3] for row in plot_data]
timestamps = [row[4] for row in plot_data]
x,y = m(lons,lats)
flight = m.scatter(x,y, c=dp_dcs, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o', s=alts,)

cb = plt.colorbar()
cb.set_label('Dp/Dc', rotation=270)

##hysplit bts
#for bt in bts:
#	np_endpoints = np.array(bt)
#	lats = np_endpoints[:,0] 
#	lons = np_endpoints[:,1]
#	heights = np_endpoints[:,2]
#	x,y = m(lons,lats)
#	bt = m.plot(x,y,'k',linewidth=2)


#city label
city_x,city_y = m(-133.7306, 68.3617)
plt.text(city_x-5000,city_y+10000,'Inuvik')
m.plot(city_x,city_y, color='blue', linestyle = 'None',marker='*', markersize = 10)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

plt.savefig('NC - Polar6 - Science 8 - Dp-Dc vs location - 155-180nm cores.png', bbox_inches='tight') 

plt.show()
	
cnx.close()