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
import shutil

GBPS_lat_min = 48.0
GBPS_lat_max = 49.4
GBPS_lon_min = -123.5
GBPS_lon_max = -122

GBPS_lat_min_2 = 47.0
GBPS_lat_max_2 = 48
GBPS_lon_min_2 = -122.75
GBPS_lon_max_2 = -122

timezone = 1
endpointsPARIS = []

clusters = []
cluster_endpoints={}
for number in [1,2,3,4,5,6,7]:
	cluster_endpoints[number]=[]
	clusters.append(number)


GBPS_count = []	
CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip'
CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/clustering/CLUSLIST_10'

new_cluslist_data = []

with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline_c = line.split()
		cluster = int(newline_c[0])
		file = newline_c[7]

		if cluster == 6:
			cluster = 4
		
		tdump_file = open(file, 'r')
		endpoints = []
		data_start = False
		i = 0
		significant_rainfall = 0
		GBPS = 0
		rainy = False
		total_rainfall = 0
		for line in tdump_file:
			newline = line.split()

			if data_start == True:
				lat = float(newline[9])
				lon = float(newline[10])
				pressure = float(newline[11])
				rainfall = float(newline[13]) #in mm/hour
				total_rainfall = total_rainfall + rainfall
				
				if (GBPS_lat_min <= lat <=GBPS_lat_max) and (GBPS_lon_min <= lon <= GBPS_lon_max):
					GBPS+=1
				if (GBPS_lat_min_2 <= lat <=GBPS_lat_max_2) and (GBPS_lon_min_2 <= lon <= GBPS_lon_max_2):
					GBPS+=1
					
				if rainfall >= 1. and i <= 72:
					significant_rainfall +=1
				else:
					significant_rainfall = 0

				
				if significant_rainfall >= 2:
					rainy = True
					
				endpoint = [lat, lon, rainfall]
				endpoints.append(endpoint)
				i+=1
			
			if newline[1] == 'PRESSURE':
				data_start = True
		
		tdump_file.close() 

		newline_c.append(total_rainfall)
		new_cluslist_data.append(newline_c)
		
		if rainy == True:
			cluster_endpoints[7].append(endpoints)
			
		elif GBPS >= 24:
			#cluster_endpoints[cluster].append(endpoints)
			#shutil.move(file, 'C:/hysplit4/working/WHI/2hrly_GBPS_tdump/')
			cluster_endpoints[6].append(endpoints)
			GBPS_count.append(GBPS)
			
		else:
			cluster_endpoints[cluster].append(endpoints)
			
print len(GBPS_count)
print 'mean hours in GBPS', np.mean(GBPS_count)
	
#save new cluslist data to file 
os.chdir('C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/')
file = open('CLUSLIST_6-mod-precip_amount_added', 'w')
for row in new_cluslist_data:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()	
	
#plottting
###set up the basemap instance  
lat_pt = 52.
lon_pt = -162.
	
m = Basemap(width=7000000,height=5500000,
			rsphere=(6378137.00,6356752.3142),
			resolution='l',area_thresh=1000.,projection='lcc',
			lat_1=48.,lat_2=55,lat_0=lat_pt,lon_0=lon_pt)


			
fig, axes = plt.subplots(4,2, figsize=(10, 10), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0.00, wspace=0.00)

axs = axes.ravel()

for i in [-1,-2]:
	axes[-1, i].axis('off')
	axes[-2, i].axis('off')
	axes[-3, i].axis('off')
	axes[-4, i].axis('off')

colors = ['b','g','r','c','m','k','y','#DF7401','#585858','grey','#663300']
air_mass_labels = ['Bering','Northern Coastal/Continental','Northern Pacific','Southern Pacific','Western Pacific/Asia','>= 24hrs in GBPS', 'rainy']
for cluster_no in clusters:
	list = cluster_endpoints[cluster_no]
	print cluster_no, len(list)
	axs[cluster_no-1] = fig.add_subplot(4,2,cluster_no)
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
		pressure = np_endpoints[:,2]
		x,y = m(lons,lats)
		bt = m.scatter(x,y, c=pressure, cmap=plt.get_cmap('jet'),edgecolors='none', marker = 'o' )
		#bt = m.plot(x,y,color=colors[cluster_no-1])
	cb = plt.colorbar()
	plt.text(0.05,0.05,air_mass_labels[cluster_no-1], transform=axs[cluster_no-1].transAxes)
		
		
	#GBPS box 1
	lats = [GBPS_lat_max,GBPS_lat_min,GBPS_lat_min,GBPS_lat_max, GBPS_lat_max]
	lons = [GBPS_lon_max,GBPS_lon_max,GBPS_lon_min,GBPS_lon_min, GBPS_lon_max]
	x,y = m(lons,lats)
	hb = m.plot(x,y, color = 'red',linewidth = 2.0)
	
	#GBPS box 2
	lats = [GBPS_lat_max_2,GBPS_lat_min_2,GBPS_lat_min_2,GBPS_lat_max_2, GBPS_lat_max_2]
	lons = [GBPS_lon_max_2,GBPS_lon_max_2,GBPS_lon_min_2,GBPS_lon_min_2, GBPS_lon_max_2]
	x,y = m(lons,lats)
	hb = m.plot(x,y, color = 'red',linewidth = 2.0)

dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/HYSPLIT/'
os.chdir(dir)

#plt.savefig('WHI_2012_all_trajectories_colored_by_cluster_6.png', bbox_inches='tight') 

plt.show()