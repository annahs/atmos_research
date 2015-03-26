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

CLUSLIST_file = 'C:/hysplit4/working/WHI/CLUSLIST_10'
with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
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
		
		endpointsWHI.append([endpoints,cluster_no]) 



		
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

colors = ['r','#6600FF','#996633','b','m','c','k','#663300','grey','y','#336699']
labels = ['Western Pacific/Asia (15%)','Southern Pacific (19%)','Georgia Basin/Puget Sound (4%)','Northern Pacific (48%)','Northern Canada (5%)']
for row in endpointsWHI:
	np_endpoints = np.array(row[0])
	cluster = row[1]
	if cluster == 9:
		BT_color = 'r'
	if cluster == 4:
		BT_color = 'm'
	if cluster in [6,8]:
		BT_color = 'g'
	if cluster in [2,7]:
		BT_color = 'b'
	if cluster in [1,3,5,10]:
		BT_color = 'c'
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color=BT_color)
	
	
red_line = mlines.Line2D([], [], color='r')
mag_line = mlines.Line2D([], [], color='m')
gre_line = mlines.Line2D([], [], color='g')
blu_line = mlines.Line2D([], [], color='b')
cya_line = mlines.Line2D([], [], color='c')

legend = plt.legend([blu_line,gre_line,red_line,cya_line,mag_line,],['W. Pacific/Asia','S. Pacific','Georgia Basin/Puget Sound','N. Pacific','N. Canada'], loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3,)
	
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
plt.savefig('WHI_FT_all_6h_HYSPLIT_BTs_colored_by_cluster.png', bbox_extra_artists=(legend,), bbox_inches='tight') 

plt.show()