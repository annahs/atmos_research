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



timezone = 1
endpointsPARIS = []

clusters = []
cluster_endpoints={}
for number in [1,2,3,4]:
	cluster_endpoints[number]=[]
	clusters.append(number)
	
	
#CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/French_campaign/Backtrajectories_biodetect-working/CLUSLIST_11'

#48 hour files
CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/French_campaign/Biodetect_48hours-working/CLUSLIST_4'
mn_height = []
with open(CLUSLIST_file,'r') as f:
	
	for line in f:
		newline = line.split()
		cluster = int(newline[0])
		file = newline[7]

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
			
				if cluster == 1 and i == 48:
					mn_height.append(height)
			
				endpoint = [lat, lon,height]
				endpoints.append(endpoint)
				i+=1
			if newline[1] == 'PRESSURE':
				data_start = True
			
			
		tdump_file.close() 
		
		cluster_endpoints[cluster].append(endpoints)
		
print np.mean(mn_height)

		
#plottting
###set up the basemap instance  
lat_pt = 52.
lon_pt = 0.
	
#5-day bts
m = Basemap(width=5500000,height=5500000,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=1000.,projection='lcc',
			lat_1=47.,lat_2=55,lat_0=lat_pt,lon_0=lon_pt)
			
#48 hour bts	
m = Basemap(width=2600000,height=2600000,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=1000.,projection='lcc',
			lat_1=47.,lat_2=55,lat_0=lat_pt,lon_0=lon_pt)



			
fig, axes = plt.subplots(2,3, figsize=(12, 10), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0.1, wspace=0.25)

axs = axes.ravel()

for i in [-1,-2,-3]:
	axes[-1, i].axis('off')
	axes[-2, i].axis('off')
	#axes[-3, i].axis('off')
	

colors = ['b','b','g','r','c','m','k','y','#DF7401','#585858','grey','#663300']

for cluster_no in clusters:
	print cluster_no,colors[cluster_no]
	list = cluster_endpoints[cluster_no]
	#subplot_num = 4,3,cluster_no
	axs[cluster_no] = fig.add_subplot(2,3,cluster_no)
	#m.drawmapboundary(fill_color='white') 
	m.bluemarble()
	m.drawcoastlines()
	#m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
	m.drawcountries()
	parallels = np.arange(0.,81,10.)
	m.drawparallels(parallels,labels=[False,True,False,False])
	meridians = np.arange(10.,351.,20.)
	m.drawmeridians(meridians,labels=[False,False,False,True])
	plt.text(0.1,0.8,str(cluster_no), fontsize=20, transform=axs[cluster_no].transAxes)

	for row in list:
		np_endpoints = np.array(row)
		lats = np_endpoints[:,0] 
		lons = np_endpoints[:,1]
		heights = np_endpoints[:,2]
		x,y = m(lons,lats)
		#bt = m.plot(x,y,color=colors[cluster_no])
		bt = m.scatter(x,y, c=heights, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o')
		#lim = bt.get_clim()
		#print lim
		plt.clim(0,1000)
	cb = plt.colorbar()
	cb.set_label('height (m)', rotation=270)

dir = 'C:/Users/Sarah Hanna/Documents/Data/French_campaign/'
os.chdir(dir)

plt.savefig('PARIS_all_trajectories_colored_by_cluster_48_hour_backtrajectories -4clusters.png', bbox_inches='tight') 

plt.show()