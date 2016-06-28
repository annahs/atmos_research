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
from matplotlib.markers import TICKLEFT, TICKRIGHT, TICKUP, TICKDOWN

#location:  USAF,city, lat, long, elev ,daytime RH and T, nightime RH and T, timezone
stations = {

'JINNAH INTL':							[417800,	'Karachi',	 	24.907,		067.161,	0030.5,	{},	{},	 5  ], 
'JOHN F KENNEDY INTERNATIONAL A':		[744860, 	'New York',	 	40.639,		-073.762,	0003.4,	{},	{},	-5  ],
'CAIRO INTL':							[623660, 	'Cairo',	 	30.122,		031.406,	0116.4,	{},	{},	 2  ],
'BEIJING - CAPITAL INTERNATIONA': 		[545110, 	'Beijing',	 	40.080,	 	116.585,	0035.4,	{},	{},	 8  ],
'LICENCIADO BENITO JUAREZ INTL':		[766793, 	'Mexico City',	19.436,		-099.072,	2229.9,	{},	{},	-6  ],
'CONGONHAS':							[837800, 	'Sao Paulo',	-23.627,	-046.655,	0801.9,	{},	{},	-3  ],
'CHHATRAPATI SHIVAJI INTL':				[430030, 	'Mumbai',		19.089,		072.868,	0011.3,	{},	{},	 5.5],
'TOKYO INTL':							[476710, 	'Tokyo',		35.552,		139.780,	0010.7,	{},	{},	 9  ],
'INDIRA GANDHI INTL':					[421810, 	'Delhi',		28.567, 	077.103,	0236.8,	{},	{},	 5.5],
'HONGQIAO INTL':						[583670, 	'Shanghai',		31.198,		121.336,	0003.0,	{},	{},	 8	],
'OSAKA INTL':							[477710, 	'Osaka',		34.786,		135.438,	0015.2,	{},	{},	 9	],
'HAZRAT SHAHJALAL INTL':				[419220, 	'Dhaka',		23.843,		090.398,	0009.1,	{},	{},	 6	],
'NETAJI SUBHASH CHANDRA BOSE IN':		[428090, 	'Kolkata',		22.655,		088.447,	0004.9,	{},	{},	 5.5],
'ATATURK':								[170600, 	'Istanbul',		40.977,		028.821,	0049.7,	{},	{},	 2	],
'AEROPARQUE JORGE NEWBERY':				[875820, 	'Buenos Aires',	-34.559, 	-058.416,	0005.5,	{},	{},	 -3  ],
}

##plotting
fig = plt.figure(figsize=(14,8))

ax1 = plt.subplot2grid((1,1), (0,0))				

lat_pt = 15			
lon_pt = 0
map_width = 24000000
map_height = 10000000

#m1 = Basemap(width=map_width,height=map_height,
#			rsphere=(6378137.00,6356752.3142),
#			resolution='l',area_thresh=1000.,projection='lcc',
#			lat_1=10.,lat_2=20,lat_0=lat_pt,lon_0=lon_pt)

m1 = Basemap(projection='kav7',lon_0=0,resolution='c')

#parallels = np.arange(-90.,90,45)
#m1.drawparallels(parallels,labels=[False,False,False,False])
#meridians = np.arange(0.,360.,45)
#m1.drawmeridians(meridians,labels=[False,False,False,False])

##rough shapes 
m1.drawcoastlines(color='grey')
m1.drawmapboundary(fill_color='#eef7fa')
m1.fillcontinents(color='#FFFFBF',lake_color='#eef7fa',zorder=0)
m1.drawcountries(color='grey')

#city labels
text_size = 15
marker_size = 11
marker_edge_w = 6
marker_edge_w_o = 4
for station, data in stations.iteritems():
	city_name = data[1]
	city_lon = data[3]
	city_lat = data[2]
	city_x,city_y = m1(city_lon, city_lat) 
	if city_name == 'Karachi': 	
		ax1.text(city_x+500000,city_y-500000,city_name,size=text_size)
		m1.plot(city_x,city_y, color='r',mew=marker_edge_w, ms=marker_size,marker='x')
	#if city_name == 'New York': 	 
	#	ax1.text(city_x+500000,city_y-220000,city_name,size=text_size)
	if city_name == 'Cairo': 	                            
		ax1.text(city_x-2000000,city_y-500000,city_name,size=text_size)	
		m1.plot(city_x,city_y, color='r',mew=marker_edge_w, ms=marker_size,marker='x')
	if city_name == 'Beijing': 	                            
		label_x = city_x-2500000
		label_y = city_y+1500000
		ax1.text(label_x,label_y,city_name,size=text_size)
		ax1.plot([city_x, label_x+2000000], [city_y, label_y], 'k-', linewidth=2)
		m1.plot(city_x,city_y, color='r',mew=marker_edge_w, ms=marker_size,marker='x')
	if city_name == 'Mexico City': 	                        
		ax1.text(city_x-4500000,city_y-220000,city_name,size=text_size)
		m1.plot(city_x,city_y, color='r',mew=marker_edge_w, ms=marker_size,marker='x')
	if city_name == 'Sao Paulo': 	                        
		ax1.text(city_x+500000,city_y-220000,city_name,size=text_size)
		m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	#if city_name == 'Mumbai': 	
	#	label_x = city_x-2000000
	#	label_y = city_y-1800000
	#	ax1.text(label_x,label_y,city_name,size=text_size)
	#	ax1.plot([city_x, label_x+2000000], [city_y, label_y+500000], 'k-', linewidth=2)
	#	m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	if city_name == 'Tokyo': 		
		label_x = city_x+500000
		label_y = city_y+500000
		ax1.text(label_x,label_y,city_name,size=text_size)
		ax1.plot([city_x, label_x], [city_y, label_y], 'k-', linewidth=2)
		m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	#if city_name == 'Delhi': 		
	#	label_x = city_x+500000
	#	label_y = city_y+950000
	#	ax1.text(label_x,label_y,city_name,size=text_size)
	#	ax1.plot([city_x, label_x], [city_y, label_y], 'k-', linewidth=2)
	#	m1.plot(city_x,city_y, color='r',mew=marker_edge_w, ms=marker_size,marker='x')
	if city_name == 'Shanghai': 
		label_x = city_x+650000
		label_y = city_y-1500000
		ax1.text(label_x,label_y,city_name,size=text_size)
		ax1.plot([city_x, label_x], [city_y, label_y+500000], 'k-', linewidth=2)
		m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	#if city_name == 'Osaka': 	
	#	label_x = city_x+700000
	#	label_y = city_y-1000000
	#	ax1.text(label_x,label_y,city_name,size=text_size)
	#	ax1.plot([city_x, label_x], [city_y, label_y+500000], 'k-', linewidth=2)
	#if city_name == 'Dhaka': 	
	#	label_x = city_x+500
	#	label_y = city_y+600000
	#	ax1.text(label_x,label_y,city_name,size=text_size)
	#	ax1.plot([city_x, label_x], [city_y, label_y], 'k-', linewidth=2)
	#	m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	#if city_name == 'Kolkata': 	
	#	label_x = city_x-900000
	#	label_y = city_y-4000000
	#	ax1.text(label_x,label_y,city_name,size=text_size)
	#	ax1.plot([city_x, label_x+500000], [city_y, label_y+600000], 'k-', linewidth=2)
	#	m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	if city_name == 'Istanbul': 	
		label_x = city_x+500000
		label_y = city_y+900000
		ax1.text(label_x,label_y,city_name,size=text_size)
		ax1.plot([city_x, label_x], [city_y, label_y], 'k-', linewidth=2)
		m1.plot(city_x,city_y, color='g',mew=marker_edge_w_o, ms=marker_size,marker='o',fillstyle ='none')
	#if city_name == 'Buenos Aires': 
	#	ax1.text(city_x+500000,city_y-220000,city_name,size=text_size)
		
	
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/megacities NOAA NCDC data/'
plt.savefig(data_dir + 'megaicities map - temp limited.png',  bbox_inches='tight') 






plt.show()

	
	
