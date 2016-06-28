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
import mysql.connector


timezone = -8
endpointsWHI = []

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

SP2_data_query = ('SELECT UNIX_UTC_6h_midtime FROM whi_gc_and_sp2_6h_mass_concs WHERE RH_threshold = 90 ORDER BY UNIX_UTC_6h_midtime')
cursor.execute(SP2_data_query)
dates = cursor.fetchall()

cnx.close()

date_times = []
for date in dates:
	date_time = datetime.utcfromtimestamp(date[0])
	date_times.append(date_time)



endpoints_LRT  = []
endpoints_SPac = []
endpoints_NPac = []
endpoints_Cont = []


#CLUSLIST_file ='C:/HYSPLIT_argh/WHI_1h_10-day_working/even_hours/CLUSLIST_4'
CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/clustering/CLUSLIST_10'

with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		date = datetime(2000+int(newline[2]),int(newline[3]),int(newline[4]),int(newline[5]))
		if (fire_time1[0] <= date < fire_time1[1]) or (fire_time2[0] <= date < fire_time2[1]):
			continue
		for date_time in date_times:
			if date == date_time:
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
				if cluster in [6,8,9]: #S Pac
					endpoints_SPac.append(endpoints)
				if cluster in [2,7]: # W Pac/Asia (LRT)
					endpoints_LRT.append(endpoints)
				if cluster in [1,3,5,10]: #N Pac
					endpoints_NPac.append(endpoints)

			
print len(endpoints_NPac),len(endpoints_SPac),len(endpoints_Cont),len(endpoints_LRT),

		
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
	
	
fig = plt.figure(figsize=(10,8))



ax1 = fig.add_subplot(221)
ax1.set_xlabel('Northern Pacific')
ax1.xaxis.set_label_position('top')
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
ax1.text(0.6, 0.05,'88 trajectories', transform=ax1.transAxes)
for row in endpoints_NPac:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='b')	
	
ax2 = fig.add_subplot(222)
ax2.set_xlabel('Southern Pacific')
ax2.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
ax2.text(0.6, 0.05,'34 trajectories', transform=ax2.transAxes)
for row in endpoints_SPac:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='g')


ax4 = fig.add_subplot(223)
ax4.set_xlabel('Western Pacific/Asia')
ax4.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
ax4.text(0.6, 0.05,'18 trajectories', transform=ax4.transAxes)
for row in endpoints_LRT:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='orange')	
	
ax5 = fig.add_subplot(224)
ax5.set_xlabel('Northern Canada')
ax5.xaxis.set_label_position('top') 
m.drawmapboundary(fill_color='white') 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=0)
m.drawcountries()
ax5.text(0.6, 0.05,'14 trajectories', transform=ax5.transAxes)
for row in endpoints_Cont:
	np_endpoints = np.array(row)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	x,y = m(lons,lats)
	bt = m.plot(x,y,color='r')
	
	
plt.subplots_adjust(hspace=0.15)
plt.subplots_adjust(wspace=0.1)

#labels = ['Western Pacific/Asia (15%)','Southern Pacific (19%)','Georgia Basin/Puget Sound (4%)','Northern Pacific (48%)','Northern Canada (5%)']

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/')
plt.savefig('WHI_FT_all_6h_HYSPLIT_BTs-4clusters.png', bbox_inches='tight') 
#plt.savefig('WHI_FT_all_2h_HYSPLIT_BTs_sep_maps_by_cluster.png', bbox_inches='tight') 

plt.show()