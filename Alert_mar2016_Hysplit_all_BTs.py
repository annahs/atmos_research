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
for number in [1,2,3]:
	cluster_endpoints[number]=[]
	clusters.append(number)
	
	


mn_height = []
with open('C:/HYSPLIT_argh/Alert_march2016_working/CLUSLIST_3','r') as f:
	
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
		
		
#plottting
###set up the basemap instance  
lat_pt = 82.
lon_pt = -62.
	
m = Basemap(projection='nplaea',boundinglat=50,lon_0=270,resolution='l')

			
fig, axes = plt.subplots(2,3,figsize=(12, 4), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0.1, wspace=0.25)

axs = axes.ravel()

for i in [-1,-2,-3]:
	axes[-1, i].axis('off')
	axes[-2, i].axis('off')
#	#axes[-3, i].axis('off')
	

colors = ['b','orange','g','r','c','m','k','y','#DF7401','#585858','grey','#663300']

for cluster_no in clusters:
	print cluster_no,colors[cluster_no]
	list = cluster_endpoints[cluster_no]
	#subplot_num = 4,3,cluster_no
	axs[cluster_no] = fig.add_subplot(1,3,cluster_no)
	#m.drawmapboundary(fill_color='white') 
	m.bluemarble()
	m.drawcoastlines()
	#m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
	m.drawcountries()
	parallels = np.arange(0.,81,10.)
	m.drawparallels(parallels,labels=[False,True,False,False])
	meridians = np.arange(10.,351.,20.)
	m.drawmeridians(meridians,labels=[False,False,False,True])
	plt.text(0.1,0.8,str(cluster_no), fontsize=20, transform=axs[cluster_no].transAxes,color = 'white')

	for row in list:
		np_endpoints = np.array(row)
		lats = np_endpoints[:,0] 
		lons = np_endpoints[:,1]
		heights = np_endpoints[:,2]
		x,y = m(lons,lats)
		bt = m.plot(x,y,color=colors[cluster_no],linewidth=2)
		#bt = m.scatter(x,y, c=heights, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o')
		#lim = bt.get_clim()
		#print lim
		#plt.clim(0,1000)
	#cb = plt.colorbar()
	#cb.set_label('height (m)', rotation=270)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert-March 2016/'
os.chdir(dir)

plt.savefig('ALERT_cluster_all_trajs_from_HYSPLIT_240hr_backtrajectories-3clusters.png', bbox_inches='tight') 

plt.show()