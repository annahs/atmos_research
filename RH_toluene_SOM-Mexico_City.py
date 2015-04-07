import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates
from matplotlib import patches
import pickle
from datetime import datetime
import time
from pprint import pprint
from datetime import timedelta
import os
import sys
from netCDF4 import Dataset
import numpy.ma as ma
from mpl_toolkits.basemap import Basemap, shiftgrid
import Etopo1map
import laplaceFilter
import mpl_util
from matplotlib import cm

am_start_time = 3
am_end_time = 6

pm_start_time = 15
pm_end_time = 18

dry_season_months = [2,3,4]
wet_season_months = [7,8,9]

stations_to_use = ['LICENCIADO BENITO JUAREZ INTL','MEXICO (CENTRAL)   D.F.']



#location:  USAF,country, lat, long, elev ,daytime RH, nightime RH, timezone, wet season RH avgs, dry season RH avgs
stations = {
'LICENCIADO BENITO JUAREZ INTL' :[766793, 'MEXICO', 19.436,  -099.072, 2229.9,{},{},-6,[],[],[],[],'k'],
'MEXICO (CENTRAL)   D.F.'    	:[766800, 'MEXICO', 19.400,  -099.183, 2303.0,{},{},-6,[],[],[],[],'k'],
'GEOGRAFIA UNAM' 				:[766810, 'MEXICO', 19.317,  -099.183, 2278.0,{},{},-6,[],[],[],[],'green'],
}


file = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/8975896585411dat.txt'

with open(file, 'r') as f:
	f.readline()
	f.readline()

	for line in f:
		
		newline = line.split(',')
		stn = newline[0].rstrip() 
		day = newline[3]
		hour = newline[4]	# in UTC	
		temp_qc = newline[9]
		dewp_qc = newline[11]
		temp = float(newline[8]) 
		RHx = float(newline[12])
		
		timezone = stations[stn][7]
	
		date = datetime.strptime(day, '%Y%m%d') 
		datetime_local = datetime.strptime(day + ' ' + hour, '%Y%m%d %H%M') + timedelta(hours = timezone)  
		

		if stn in stations.keys():
				
			#data QC
			if temp_qc in ['1','5'] and dewp_qc in ['1','5']:  #data has 'Passed all quality control checks'
				
				am_data = stations[stn][5]
				pm_data = stations[stn][6]
				
				#get am data
				if datetime_local.hour >= am_start_time and datetime_local.hour < am_end_time:
					if date in am_data:
						am_data[date].append(RHx)
					else:
						am_data[date] = [RHx]
						
				#get pm data 
				if datetime_local.hour >= pm_start_time and datetime_local.hour < pm_end_time:
					if date in pm_data:
						pm_data[date].append(RHx)
					else:
						pm_data[date] = [RHx]
					


		
for stn in stations:
	print '\n'
	print stn
	am_data = stations[stn][5]
	pm_data = stations[stn][6]
	
	dry_season_am_avgs = stations[stn][8]
	dry_season_pm_avgs = stations[stn][9]
	
	wet_season_am_avgs = stations[stn][10]
	wet_season_pm_avgs = stations[stn][11]
	
	night_count = 0
	day_count = 0
		
	
	for date, RHs in pm_data.iteritems():
		pm_avg_RH = np.mean(RHs)
		night_count +=1
			
		if date.month in dry_season_months:
			dry_season_pm_avgs.append(pm_avg_RH)
			
		if date.month in wet_season_months:
			wet_season_pm_avgs.append(pm_avg_RH)
			
	for date, RHs in am_data.iteritems():
		am_avg_RH = np.mean(RHs)
		day_count +=1
		
		if date.month in dry_season_months:
			dry_season_am_avgs.append(am_avg_RH)
			
		if date.month in wet_season_months:
			wet_season_am_avgs.append(am_avg_RH)
			

		

	print 'dry season am data points', len(dry_season_am_avgs)
	print 'dry season am median', np.median(dry_season_am_avgs)

	print 'dry season pm data points', len(dry_season_pm_avgs)
	print 'dry season pm median', np.median(dry_season_pm_avgs)
	
	print 'wet season am data points',  len(wet_season_am_avgs)
	print 'wet season am median', np.median(wet_season_am_avgs)
                                            
	print 'wet season pm data points',  len(wet_season_pm_avgs)
	print 'wet season pm median', np.median(wet_season_pm_avgs)
	

#Plotting


fig1 = plt.figure(figsize=(16,8))

bins_to_use = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]

label_x_pos = 0.05
label_y_pos = 0.85

see_Y_axis = True
y_upper_lim = 260


ax1w  = plt.subplot2grid((2,6), (0,0), colspan=1)
ax1d  = plt.subplot2grid((2,6), (0,1), colspan=1)	
			                
ax2w  = plt.subplot2grid((2,6), (0,4), colspan=1)
ax2d  = plt.subplot2grid((2,6), (0,5), colspan=1)	
					        
ax3w  = plt.subplot2grid((2,6), (1,0), colspan=1)
ax3d  = plt.subplot2grid((2,6), (1,1), colspan=1)
				            
ax4w  = plt.subplot2grid((2,6), (1,4), colspan=1)
ax4d  = plt.subplot2grid((2,6), (1,5), colspan=1)	
						  
						

#dry season
											
n,bins,patches = ax1w.hist(stations[stations_to_use[0]][8],bins_to_use, color='red', alpha = 0.6)
ax1w.yaxis.set_visible(see_Y_axis)
ax1w.text(label_x_pos, label_y_pos,'BENITO JUAREZ INTL', transform=ax1w.transAxes)
ax1w.set_xlim(0,100)
ax1w.xaxis.set_label_position('top')
ax1w.set_xlabel('AM')
ax1w.set_ylabel('Dry Season Frequency (FMA)')
ax1w.set_ylim(0,y_upper_lim)
ax1w.xaxis.set_visible(True)
n,bins,patches = ax1d.hist(stations[stations_to_use[0]][9],bins_to_use, color='red')
ax1d.set_xlim(0,100)
ax1d.xaxis.set_label_position('top')
ax1d.set_xlabel('PM')
ax1d.set_ylim(0,y_upper_lim)
ax1d.yaxis.set_visible(False)


n,bins,patches = ax2w.hist(stations[stations_to_use[1]][8],bins_to_use, color='red', alpha = 0.6)
ax2w.yaxis.set_visible(see_Y_axis)
ax2w.text(label_x_pos, label_y_pos,'MEXICO (CENTRAL) D.F.', transform=ax2w.transAxes)
ax2w.set_xlim(0,100)
ax2w.set_ylim(0,y_upper_lim)
ax2w.xaxis.set_visible(True)
ax2w.yaxis.set_visible(False)
ax2w.xaxis.set_label_position('top')
ax2w.set_xlabel('AM')
n,bins,patches = ax2d.hist(stations[stations_to_use[1]][9],bins_to_use, color='red')
ax2d.xaxis.set_visible(True)
ax2d.set_xlim(0,100)
ax2d.set_ylim(0,y_upper_lim)
ax2d.xaxis.set_label_position('top')
ax2d.set_xlabel('PM')
ax2d.yaxis.set_visible(True)
ax2d.yaxis.tick_right()
ax2d.set_ylabel('Dry Season Frequency (FMA)')
ax2d.yaxis.set_label_position('right')

#wet season

n,bins,patches = ax3w.hist(stations[stations_to_use[0]][10],bins_to_use, color='blue', alpha = 0.6)
ax3w.yaxis.set_visible(see_Y_axis)
ax3w.set_xlim(0,100)
ax3w.xaxis.set_label_position('top')
ax3w.set_ylabel('Wet Season Frequency (JAS)')
ax3w.set_ylim(0,y_upper_lim)
ax3w.xaxis.set_visible(True)
n,bins,patches = ax3d.hist(stations[stations_to_use[0]][11],bins_to_use, color='blue')
ax3d.set_xlim(0,100)
ax3d.xaxis.set_label_position('top')
ax3d.set_ylim(0,y_upper_lim)
ax3d.yaxis.set_visible(False)
ax3d.xaxis.set_visible(True)


n,bins,patches = ax4w.hist(stations[stations_to_use[1]][10],bins_to_use, color='blue', alpha = 0.6)
ax4w.yaxis.set_visible(see_Y_axis)
ax4w.set_xlim(0,100)
ax4w.set_ylim(0,y_upper_lim)
ax4w.yaxis.set_visible(False)
ax4w.xaxis.set_visible(True)
n,bins,patches = ax4d.hist(stations[stations_to_use[1]][11],bins_to_use, color='blue')
ax4d.xaxis.set_visible(True)
ax4d.set_xlim(0,100)
ax4d.set_ylim(0,y_upper_lim)
ax4d.yaxis.set_visible(True)
ax4d.yaxis.tick_right()
ax4d.set_ylabel('Wet Season Frequency (JAS)')
ax4d.yaxis.set_label_position('right')

	
#mapping  


ax9  = plt.subplot2grid((2,6), (0,2), colspan=2, rowspan=7)


latStart = 18.2
latEnd = 20.3
lonStart = -100.
lonEnd = -98


#Get the etopo2 data#
etopo1name='C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/etopo/ETOPO1_Ice_g_gmt4.grd'
etopo1 = Dataset(etopo1name,'r')

#print type(etopo1.variables)
#for item, value in etopo1.variables.iteritems():
#	print item, value

lons = etopo1.variables['x'][:]
lats = etopo1.variables['y'][:]

res = Etopo1map.findSubsetIndices(latStart-5,latEnd+5,lonStart-40,lonEnd+10,lats,lons)

lon,lat=np.meshgrid(lons[res[0]:res[1]],lats[res[2]:res[3]])    
#topo_bathy = etopo1.variables['z'][int(res[2]):int(res[3]),int(res[0]):int(res[1])]  #z is in meters
#topo_bathySmoothed = laplaceFilter.laplace_filter(topo_bathy,M=None)
topo_bathySmoothed = etopo1.variables['z'][int(res[2]):int(res[3]),int(res[0]):int(res[1])]  #z is in meters

levels_list = []
for x in range(0,4000,400):
	levels_list.append(x)

if lonStart< 0 and lonEnd < 0:
	lon_0= - (abs(lonEnd)+abs(lonStart))/2.0
else:
	lon_0=(abs(lonEnd)+abs(lonStart))/2.0
	
print 'Center longitude ',lon_0


map = Basemap(llcrnrlat=latStart,urcrnrlat=latEnd,\
			llcrnrlon=lonStart,urcrnrlon=lonEnd,\
			rsphere=(6378137.00,6356752.3142),\
			resolution='l',area_thresh=100.,projection='lcc',\
			lat_1=latStart,lon_0=lon_0)

x, y = map(lon,lat) 
map.drawcoastlines()
map.drawcountries()
#map.drawstates()
#map.drawrivers()
#map.fillcontinents(color='grey')
map.drawmeridians(np.arange(lons.min(),lons.max(),1),labels=[0,0,0,1])
map.drawparallels(np.arange(lats.min(),lats.max(),1),labels=[1,0,0,0])


CS1 = map.contourf(x,y,topo_bathySmoothed,levels_list,
				cmap=mpl_util.LevelColormap(levels_list,cmap=cm.gist_earth),
				extend='both',
				alpha=1.0,
				origin='lower')

CS1.axis='tight'

cbar = plt.colorbar(CS1, orientation = 'horizontal', use_gridspec = True)
cbar.set_label('Altitude (m asl)')

i=0
stn_lons = []
stn_lats = []
for key, value in stations.iteritems():
	if key in stations_to_use:	
		stn_lons.append(value[3])
		stn_lats.append(value[2])

		if i==0:
			xn,yn = map(value[3], value[2]+0.04)
			plt.text(xn,yn, 'Benito Juarez Intl')
			
		if i==1:
			xn,yn = map(value[3]-0.75, value[2]-0.1)
			plt.text(xn,yn, 'Mexico (Central) D.F.')
			
		x,y = map(value[3], value[2])	
		map.plot(x,y, color=stations[key][12], marker='o', linestyle = 'None', markersize = 8, label = 'MEXICO (CENTRAL) D.F.')
		i+=1

#####high res shapefiles for presentation purposes
MEX_info = map.readshapefile('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/shp/NA_road_atlas/road00l_shp/road_l','MEX',drawbounds=True) #GADM Data http://www.gadm.org/country

for nshape,seg in enumerate(map.MEX):
	xx,yy = zip(*seg)
	color = '#404040' 
	plt.plot(xx,yy,color=color)

map.drawmapscale(-99.7, 18.55, lon_0, latStart, 50, barstyle='simple', units='km', fontsize=12, yoffset=None, labelstyle='simple', fontcolor='k', fillcolor1='w', fillcolor2='k', ax=None, format='%d', zorder=None)

		
#showing
#showing
	
plt.subplots_adjust(wspace=0.3)
plt.subplots_adjust(hspace=0.2)

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/Mexico_City_RH.png',  bbox_inches='tight') 

plt.show()



