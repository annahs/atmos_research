import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import os
import sys
import matplotlib.colors
import colorsys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import mmap



timezone = timedelta(hours = -8)

endpointsWHI =  {}

dir = 'C:/hysplit4/working/WHI/cluster_means/'
os.chdir(dir)


cluster_no = 0	
for file in os.listdir('.'):
	if file.endswith('mean.tdump'):
		
		tdump_file = open(file, 'r')
		print file
		endpoints = []
		data_start = False
	
		
		for line in tdump_file:
			newline = line.split()
			
			
			
			if data_start == True:
				lat = float(newline[9])
				lon = float(newline[10])
				pressure = float(newline[11]) #in hPa
				year =  int(newline[2])
				month = int(newline[3])
				day = int(newline[4])
				hour = int(newline[5])
				Py_datetime_UTC = datetime(year, month, day, hour)
				Py_datetime = Py_datetime_UTC + timezone
				
				endpoint = [lat, lon, pressure]
				endpoints.append(endpoint)
				
			if newline[1] == 'PRESSURE':
				data_start = True
		
		tdump_file.close() 
		
		endpointsWHI[cluster_no]=endpoints
		cluster_no +=1



#plottting
###set up the basemap instance  
lat_pt = 57.06
lon_pt = -157.96
plt_lat_min = -10
plt_lat_max = 90#44.2
plt_lon_min = -220#-125.25
plt_lon_max = -50

m = Basemap(width=9000000,height=7000000,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=1000.,projection='lcc',
			lat_1=45.,lat_2=55,lat_0=lat_pt,lon_0=lon_pt)
	
	
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(111)
m.drawmapboundary(fill_color='white') 

#rough shapes 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()



####other data

#label WHI
WHI_lon = -122.96
WHI_lat = 50.06
WHI_x,WHI_y = m(WHI_lon, WHI_lat)
plt.text(WHI_x-33000,WHI_y-17000,'WHI')
m.plot(WHI_x,WHI_y, color='black', marker='o')


##draw map scale
#scale_lat = lat_pt-7
#scale_lon = lon_pt-6
##m.drawmapscale(scale_lon, scale_lat, -118, 32, 100, barstyle='simple', units='km', fontsize=9, yoffset=None, labelstyle='simple', fontcolor='k', fillcolor1='w', fillcolor2='k', ax=None, format='%d', zorder=None)
#parallels = np.arange(0.,81,10.)
## labels = [left,right,top,bottom]
#m.drawparallels(parallels,labels=[False,True,True,False])
#meridians = np.arange(10.,351.,20.)
#m.drawmeridians(meridians,labels=[True,False,False,True])



linewidth = 2
pre_linewidth = 2
alphaval = 1

S = 1.0#0.1
hue = 0#0.65
i=0


colors = ['b','g','r','c','m','k','y','#DF7401','#585858']
labels = ['Western Pacific/Asia (15%)','Southern Pacific (19%)','Georgia Basin/Puget Sound (4%)','Northern Pacific (48%)','Northern Canada (5%)']
for cluster_no, endpoints in endpointsWHI.items():
	np_endpoints = np.array(endpoints)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	pressure = np_endpoints[:,2]
	x,y = m(lons,lats)
	#bt = m.scatter(x,y, c=pressure, cmap=plt.get_cmap('jet'),edgecolors='none')
	bt = m.plot(x,y,linewidth = linewidth, color =colors[cluster_no], label = labels[cluster_no])
	
	i+=1

plt.legend(loc = 3)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')

plt.savefig('cluster_means_from_HYSPLIT.png', bbox_inches='tight') 
plt.show()




