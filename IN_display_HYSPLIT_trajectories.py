import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
from mpl_toolkits.basemap import Basemap
import matplotlib.colors



trajs = []
	
#CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/French_campaign/Backtrajectories_biodetect-working/CLUSLIST_11'

#48 hour files
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare IN/HYSPLIT/'

os.chdir(data_dir)

plot_data = [
[-64.8471		,69.3589	   ],
[-71.11666		,71.70185167   ] ,
[-81.01786		,73.56860833   ] ,
[-83.97575		,74.11009      ] ,
[-92.2254		,74.2369       ] ,
[-86.99806333	,74.42822667   ] ,
[-75.27019167	,73.92597333   ] ,
[-75.8847		,73.2611       ] ,
[-72.19268833	,76.26021667   ] ,
[-73.27239833	,76.3168       ] ,
[-72.68896667	,78.93360833   ] ,
[-69.2132		,80.15         ] ,
[-78.38091833	,74.700675     ] ,
[-96.23453333	,72.92619167   ] ,
[-99.24270667	,70.09025167   ] ,
]


for file in os.listdir(data_dir):
	if file.startswith('tdump'):
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
		
		
#plottting
###set up the basemap instance  
lat_pt = 75	
lon_pt = -76
map_width = 3000000
map_height = 3000000
#m = Basemap(projection='nplaea',boundinglat=50,lon_0=270,resolution='l')

			
fig = plt.figure(figsize=(12,10))
ax = fig.add_subplot(111)

m = Basemap(width=map_width,height=map_height,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=100.,projection='lcc',
			lat_1=lat_pt-10,lat_2=lat_pt+10,lat_0=lat_pt,lon_0=lon_pt)

m.drawcoastlines()
m.fillcontinents(color='lightgrey',lake_color='white',zorder=0,alpha=0.35)
m.drawcountries()
m.drawmapboundary(fill_color='white')

#ship locn data
lats = [row[1] for row in plot_data]
lons = [row[0] for row in plot_data]
x,y = m(lons,lats)	
plot = m.plot(x,y, marker = 's',color='green', markersize = 8, linestyle = '')

colors = ['r','r','b','b','g','g','c','c','m','m','k','k','grey','grey','orange','orange','brown','brown','indigo','indigo','hotpink','hotpink','wheat','wheat','peru','peru','salmon','salmon','plum','plum','darkgreen','darkgreen',]
i=0
for row in trajs:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	heights = np_endpoints[:,2]
	x,y = m(lons,lats)
	bt = m.plot(x,y,linewidth = 1.5, color=colors[i])
	i+=1
	#bt = m.scatter(x,y, c=heights, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o')
	#lim = bt.get_clim()
	#print lim
	#plt.clim(0,1000)
#cb = plt.colorbar()
#cb.set_label('height (m)', rotation=270)


plt.show()