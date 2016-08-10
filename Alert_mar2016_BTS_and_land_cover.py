import numpy as np
from struct import *
import sys
import os
import math
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import matplotlib.colors

#Note: With respect to the ASCII text data files, the lat/lon grids are flipped in orientation. 
#Specifically, the binary arrays are stored beginning with the upper left corner, whereas the ASCII text data are stored beginning with the lower left corner. 
#Please be aware of this when working with these files.
dates = [
#datetime(2016,3,12),
datetime(2016,3,13),
datetime(2016,3,14),
datetime(2016,3,15),
datetime(2016,3,16),
datetime(2016,3,17),
datetime(2016,3,18),
datetime(2016,3,19),
datetime(2016,3,20),
datetime(2016,3,21),
datetime(2016,3,23),
datetime(2016,3,24),
datetime(2016,3,25),
datetime(2016,3,26),
datetime(2016,3,27),
datetime(2016,3,28),
datetime(2016,3,29),
]


date = datetime(2016,3,14)
day_of_year = date.timetuple().tm_yday
print date,day_of_year
lat_pt = 60


#binary arrays
path = 'C:/Users/Sarah Hanna/Documents/Data/Alert - Meng/IMS-24km/'
os.chdir(path)

file_lon = 'imslon_24km.bin'
file_lat = 'imslat_24km.bin'

f_lon = open(file_lon, 'rb')
f_lat = open(file_lat, 'rb')

lons_s = np.fromfile(f_lon, dtype='<f4')
lats_s = np.fromfile(f_lat, dtype='<f4')

lons = np.reshape(lons_s, [1024,1024], order='C')
lats = np.reshape(lats_s, [1024,1024], order='C')

f_lon.close()
f_lat.close()


#NSIDC ascii data
file = 'ims20160'+str(day_of_year)+'_24km_v1.3.asc'
plot_data = []
with open(file, 'r') as f:
	for line in range(0,30):
		f.readline()
	row=0
	for line in f:
		newline = list(line)[:-1]
		col = 0
		for item in newline:
			value = int(item)
			lon_o = lons[row][col]
			lat_o = lats[row][col]
			#move marker to center of 24x24 cell (11842.495 is half width of cell(23,684.997 meters per cell in x and y))
			lat = lat_o  + (11842.495/6371200.0) * (180 / math.pi);
			lon = lon_o  + (11842.495/6371200.0) * (180 / math.pi) / math.cos(math.radians(lat_o * math.pi/180));
			if np.isnan(lon) == False and np.isnan(lat) == False and lat >= lat_pt:
				plot_data.append([lon,lat,value])
				#x,y = m(-lon+20, lat)
				#if value == 0:
				#	color = 'grey'
				#if value == 1:
				#	color = 'b'
				#if value == 2:
				#	color = 'g'
				#if value == 3:
				#	color = 'yellow'
				#if value == 4:
				#	color = 'white'
				
				#m.plot(x,y, markerfacecolor =color, marker='s', linestyle = 'None',markersize=1,markeredgecolor=color,alpha=0.5)	
			col +=1
		#print row
		row+=1

		
		
		
#plottting
###set up the basemap instance  

m = Basemap(projection='npstere',boundinglat=60,lon_0=-80,resolution='l',rsphere=6371200.0,lat_ts=60, round=True)
fig = plt.figure()
ax = fig.add_subplot(111)

for row in plot_data:
	lon = row[0]
	lat = row[1]
	value = row[2]
	x,y = m(-lon+20, lat)
	if value == 0:
		color = 'grey'
	if value == 1:
		color = 'b'
	if value == 2:
		color = 'g'
	if value == 3:
		color = 'yellow'
	if value == 4:
		color = 'white'

	m.plot(x,y, markerfacecolor =color, marker='s', linestyle = 'None',markersize=1,markeredgecolor=color,alpha=0.5)


		
#BTs		
bt = []

with open('C:/HYSPLIT_argh/Alert_march2016_working/CLUSLIST_3','r') as f:
	
	for line in f:
		newline = line.split()
		cluster = int(newline[0])
		file = newline[7]
		bt_date_str =  file[-8:-2]
		
		bt_date = datetime.strptime(bt_date_str,'%y%m%d')
		if bt_date == date:
			print bt_date
			tdump_file = open(file, 'r')
			endpoints = []
			data_start = False

			i=0
			for line in tdump_file:
				newline = line.split()

				if data_start == True:
					lat = float(newline[9])
					lon = float(newline[10])
				
					endpoint = [lat, lon]
					endpoints.append(endpoint)
					i+=1
				if newline[1] == 'PRESSURE':
					data_start = True
				
				
			tdump_file.close() 
			
			bt.append(endpoints)
			
print 'plotting endpoints'
for row in bt:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt_plot = m.plot(x,y,color='r',linewidth=2)
		

m.drawcoastlines()
m.drawcountries()
parallels = np.arange(0.,81,10.)
m.drawparallels(parallels,labels=[False,False,False,False])
meridians = np.arange(10.,351.,60.)
m.drawmeridians(meridians,labels=[True,True,True,True])

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert - Meng/')
#plt.savefig('ALERT_10day_backtrajectory_with_surface_cover_'+str(day_of_year)+'.png', bbox_inches='tight') 


plt.show()
plt.clf()
plt.close(fig)