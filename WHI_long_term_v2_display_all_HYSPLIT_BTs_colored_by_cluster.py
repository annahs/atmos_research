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

timezone = -8
endpointsWHI = []

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST

endpoints_GBPS = []
endpoints_LRT  = []
endpoints_SPac = []
endpoints_NPac = []
endpoints_Cont = []



CLUSLIST_file = 'C:/hysplit4/working/WHI/CLUSLIST_10'
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
		
		if cluster in [4]: #N Can (Cont)
			endpoints_Cont.append(endpoints)
		if cluster in [6,8]: #S Pac
			endpoints_SPac.append(endpoints)
		if cluster in [2,7]: # W Pac/Asia (LRT)
			endpoints_LRT.append(endpoints)
		if cluster in [1,3,5,10]: #N Pac
			endpoints_NPac.append(endpoints)
		if cluster in [9]: #GBPS
			endpoints_GBPS.append(endpoints)
	


		
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
	
	
fig = plt.figure(figsize=(10,11))



ax1 = fig.add_subplot(321)
ax1.set_xlabel('Northern Pacific')
ax1.xaxis.set_label_position('top')
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
for row in endpoints_NPac:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='c')	
	
ax2 = fig.add_subplot(322)
ax2.set_xlabel('Southern Pacific')
ax2.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
for row in endpoints_SPac:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='g')

	
ax3 = fig.add_subplot(323)
ax3.set_xlabel('Georgia Basin/Puget Sound')
ax3.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
for row in endpoints_GBPS:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='r')

ax4 = fig.add_subplot(324)
ax4.set_xlabel('Western Pacific/Asia')
ax4.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
for row in endpoints_LRT:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='b')	
	
ax5 = fig.add_subplot(325)
ax5.set_xlabel('Northern Canada')
ax5.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
for row in endpoints_Cont:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='m')
	
	
plt.subplots_adjust(hspace=0.15)
plt.subplots_adjust(wspace=0.1)

#labels = ['Western Pacific/Asia (15%)','Southern Pacific (19%)','Georgia Basin/Puget Sound (4%)','Northern Pacific (48%)','Northern Canada (5%)']

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
#plt.savefig('WHI_FT_all_6h_HYSPLIT_BTs_SPac.png', bbox_extra_artists=(legend,), bbox_inches='tight') 
plt.savefig('WHI_FT_all_6h_HYSPLIT_BTs_sep_maps_by_cluster.png', bbox_inches='tight') 

plt.show()