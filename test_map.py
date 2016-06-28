import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from mpl_toolkits.basemap import Basemap

plot_data = [
#[-64.8471		,69.3589	   ],
#[-71.11666		,71.70185167   ] ,
#[-81.01786		,73.56860833   ] ,
#[-83.97575		,74.11009      ] ,
#[-92.2254		,74.2369       ] ,
#[-86.99806333	,74.42822667   ] ,
#[-75.27019167	,73.92597333   ] ,
#[-57.8847		,73.2611       ] ,
#[-72.19268833	,76.26021667   ] ,
#[-73.27239833	,76.3168       ] ,
#[-72.68896667	,78.93360833   ] ,
#[-69.2132		,80.15         ] ,
[-78.38091833	,74.700675     ] ,
#[-96.23453333	,72.92619167   ] ,
#[-99.24270667	,70.09025167   ] ,
]
	
trajs = []
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare IN/HYSPLIT/'
os.chdir(data_dir)
for file in os.listdir(data_dir):
	if file.startswith('tdumpTEST'):
		print file
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
		
		trajs.append(endpoints)
		

	
map_width = 2000000
map_height = 2000000


fig = plt.figure()
ax = fig.add_subplot(111)	
	
###set up the basemap instance  
lat_pt = 70	
lon_pt = -72

#m = Basemap(projection='nplaea',boundinglat=50,lon_0=270,resolution='l')

m = Basemap(width=map_width,height=map_height,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=100.,projection='lcc',
			lat_1=lat_pt-10,lat_2=lat_pt+10,lat_0=lat_pt,lon_0=lon_pt)
			


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
lats = [row[1] for row in plot_data]
lons = [row[0] for row in plot_data]
x,y = m(lons,lats)

#x,y = m(lon,lat)
plot = m.plot(x,y, marker = 'o',color='blue', markersize = 8, linestyle = '')

for row in trajs:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	heights = np_endpoints[:,2]
	x,y = m(lons,lats)
	bt = m.plot(x,y,linewidth = 1.5)
	i+=1



plt.show()

