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



timezone = 1
endpointsPARIS = []

clusters = []
cluster_endpoints={}
for number in [1,2,3,4,5,6,7,8,9,10,11]:
	cluster_endpoints[number]=[]
	clusters.append(number)
		
CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/French_campaign/Backtrajectories_biodetect-working/CLUSLIST_11'
with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster = int(newline[0])
		file = newline[7]

		tdump_file = open(file, 'r')
		endpoints = []
		data_start = False

		for line in tdump_file:
			newline = line.split()

			if data_start == True:
				lat = float(newline[9])
				lon = float(newline[10])
			
				endpoint = [lat, lon]
				endpoints.append(endpoint)
				
			if newline[1] == 'PRESSURE':
				data_start = True
		
		tdump_file.close() 
		
		cluster_endpoints[cluster].append(endpoints)
		

		
#plottting
###set up the basemap instance  
lat_pt = 55.
lon_pt = 0.
	
m = Basemap(width=5500000,height=5500000,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=1000.,projection='lcc',
			lat_1=47.,lat_2=55,lat_0=lat_pt,lon_0=lon_pt)


			
fig, axes = plt.subplots(4,3, figsize=(12, 16), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0.1, wspace=0.2)

axs = axes.ravel()

for i in [-1,-2,-3]:
	axes[-1, i].axis('off')
	axes[-2, i].axis('off')
	axes[-3, i].axis('off')
	axes[-4, i].axis('off')

colors = ['b','b','g','r','c','m','k','y','#DF7401','#585858','grey','#663300']

for cluster_no in clusters:
	print cluster_no,colors[cluster_no]
	list = cluster_endpoints[cluster_no]
	#subplot_num = 4,3,cluster_no
	axs[cluster_no] = fig.add_subplot(4,3,cluster_no)
	m.drawmapboundary(fill_color='white') 
	m.drawcoastlines()
	m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
	m.drawcountries()
	parallels = np.arange(0.,81,10.)
	m.drawparallels(parallels,labels=[False,True,False,False])
	meridians = np.arange(10.,351.,20.)
	m.drawmeridians(meridians,labels=[False,False,False,True])
	
	for row in list:
		np_endpoints = np.array(row)
		lats = np_endpoints[:,0] 
		lons = np_endpoints[:,1]
		x,y = m(lons,lats)
		bt = m.plot(x,y,color=colors[cluster_no])


dir = 'C:/Users/Sarah Hanna/Documents/Data/French_campaign/'
os.chdir(dir)

plt.savefig('PARIS_all_trajectories_colored_by_cluster_11.png', bbox_inches='tight') 

plt.show()