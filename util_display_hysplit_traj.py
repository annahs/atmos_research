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



tdump_file = open('C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert-March 2016/tdump201603', 'r')
print file

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

		
		endpoint = [lat, lon]
		endpoints.append(endpoint)
		
	if newline[1] == 'PRESSURE':
		data_start = True

tdump_file.close() 


#plottting
###set up the basemap instance  
lat_pt = 80.
lon_pt = -65.
plt_lat_min = 0
plt_lat_max = 90#44.2
plt_lon_min = -150#-125.25
plt_lon_max = -1

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
np_endpoints = np.array(endpoints)
lats = np_endpoints[:,0] 
lons = np_endpoints[:,1]
x,y = m(lons,lats)

bt = m.plot(x,y,linewidth = 2, color ='r')



plt.show()




