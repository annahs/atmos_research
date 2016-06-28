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
from matplotlib import colorbar
import matplotlib.colors
from mpl_toolkits.basemap import Basemap
import copy

flight = 'test'
save = True

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

'test':[datetime(2015,4,5,0,0),datetime(2015,4,14,0,0)]
}



start_time = flight_times[flight][0]
end_time = flight_times[flight][1]
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


plot_data = []

###get the lat, lon and alt means
cursor.execute(('SELECT lat, lon, alt,UNIX_UTC_ts from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_start_time,UNIX_end_time))
lat_lon_data = cursor.fetchall()
lats = []
lons = []
alts = []
for locn in lat_lon_data:
	lat = locn[0] 
	lon = locn[1]
	alt = locn[2]
	UNIX_UTC_ts = locn[3]
	if alt >= 0:
		if (UNIX_UTC_ts < calendar.timegm(datetime(2015,4,6,0,0).utctimetuple())) or (calendar.timegm(datetime(2015,4,7,0,0).utctimetuple()) <= UNIX_UTC_ts < calendar.timegm(datetime(2015,4,10,0,0).utctimetuple())) or (calendar.timegm(datetime(2015,4,11,0,0).utctimetuple()) <= UNIX_UTC_ts):
			lats.append(lat)
			lons.append(lon)
			alts.append(alt)
	

##plotting



fig = plt.figure(figsize=(14,8))

ax1 = plt.subplot2grid((2,2), (0,0), rowspan=2)				
ax2 = plt.subplot2grid((2,2), (0,1))
ax3 = plt.subplot2grid((2,2), (1,1))




##Main Map #########
lat_pt = 78.5			
lon_pt = -20
map_width = 6000000
map_height = 4000000

m1 = Basemap(projection='nplaea',boundinglat=65,lon_0=270,resolution='l',area_thresh=10000., ax=ax1)
#meridians
parallels = np.arange(60.,91,10)
m1.drawparallels(parallels,labels=[False,False,True,False])
#meridians = np.arange(10.,351.,10)
#m.drawmeridians(meridians,labels=[False,False,False,True])

##rough shapes 
m1.drawcoastlines()
m1.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m1.drawcountries()
m1.drawmapboundary(fill_color='#f7fafc')
#city labels
city_x,city_y = m1(15.6500, 78.2200) 
ax1.text(city_x-100000,city_y+150000,'Longyearbyen',size=14)
m1.plot(city_x,city_y, color='r', linestyle = 'None',marker='o', markersize = 14)

city_x,city_y = m1(-85.9408, 79.9889)
ax1.text(city_x-680000,city_y+120000,'Eureka',size=14)
m1.plot(city_x,city_y, color='r', linestyle = 'None',marker='o', markersize = 14)

city_x,city_y = m1(-62.338, 82.5014) 
ax1.text(city_x-300000,city_y+100000,'Alert',size=14)
m1.plot(city_x,city_y, color='r', linestyle = 'None',marker='o', markersize = 14)




#####Lyrb only ########
lat_pt = 78.5			
lon_pt = 14.5
map_width = 400000
map_height = 300000

m2 = Basemap(width=map_width,height=map_height,
			rsphere=(6378137.00,6356752.3142),
			resolution='h',area_thresh=1.,projection='lcc',
			lat_1=75.,lat_2=85,lat_0=lat_pt,lon_0=lon_pt, ax=ax2)

##rough shapes 
m2.drawcoastlines()
m2.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m2.drawcountries()
m2.drawmapboundary(fill_color='#f7fafc')

#draw map scale
sc_lat = 77.4
sc_lon = 9.5
m2.drawmapscale(sc_lon, sc_lat, sc_lon, 76, 100, barstyle='simple', units='km', fontsize=12, yoffset=None, labelstyle='simple', fontcolor='k', fillcolor1='w', fillcolor2='k', ax=None, format='%d', zorder=None)

#flight data
x,y = m2(lons,lats)
flight_plot2 = m2.scatter(x,y, c=alts, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o',s=3)
cax, kw = colorbar.make_axes_gridspec(ax2,shrink = 1)
cb2 = plt.colorbar(flight_plot2, cax=cax)
cb2.set_label('altitude (m)', rotation=270,labelpad=14)

#city labels
city_x,city_y = m2(15.6500, 78.2200) 
ax2.text(city_x-27000,city_y-27000,'Longyearbyen', size=14)
m2.plot(city_x,city_y, color='r', linestyle = 'None',marker='o', markersize = 12)




##eureka and alert
lat_pt = 82			
lon_pt = -86.
map_width = 800000
map_height = 600000

m3 = Basemap(width=map_width,height=map_height,
			rsphere=(6378137.00,6356752.3142),
			resolution='h',area_thresh=1.,projection='lcc',
			lat_1=75.,lat_2=85,lat_0=lat_pt,lon_0=lon_pt, ax=ax3)

##rough shapes 
m3.drawcoastlines()
m3.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m3.drawcountries()
m3.drawmapboundary(fill_color='#f7fafc')

#draw map scale (Draw a map scale at lon,lat of length length representing distance in the map projection coordinates at lon0,lat0.)
sc_lat = 83.7
sc_lon = -110.5
m3.drawmapscale(sc_lon, sc_lat, sc_lon, sc_lat, 100, barstyle='simple', units='km', fontsize=12, yoffset=None, labelstyle='simple', fontcolor='k', fillcolor1='w', fillcolor2='k', ax=None, format='%d', zorder=None)

#flight data
x,y = m3(lons,lats)
flight_plot3 = m3.scatter(x,y, c=alts, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o',s=3)
cax, kw = colorbar.make_axes_gridspec(ax3, shrink = 1)
cb3 = plt.colorbar(flight_plot3, cax=cax)
cb3.set_label('altitude (m)', rotation=270,labelpad=14)


#city labels
city_x,city_y = m3(-85.9408, 79.9889)
ax3.text(city_x+70000,city_y+24000,'Eureka', size=14)
m3.plot(city_x,city_y, color='r', linestyle = 'None',marker='o', markersize = 12)

city_x,city_y = m3(-62.338, 82.5014) 
ax3.text(city_x-60000,city_y+55000,'Alert', size=14)
m3.plot(city_x,city_y, color='r', linestyle = 'None',marker='o', markersize = 12)

plt.tight_layout()


os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/')	
if save == True:
	plt.savefig('POLAR6_maps and flight Tracks - Longyearbyen,Alert,Eureka.png', bbox_inches='tight')


plt.show()