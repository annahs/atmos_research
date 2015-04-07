import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates
from matplotlib import patches
import os
import pickle
from datetime import datetime
import time
from pprint import pprint
import sys
from datetime import timedelta
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

stations_to_use = ['SACRAMENTO EXECUTIVE AIRPORT','MDSTO CTY-CO H SHAM FD APT','FRESNO YOSEMITE INTERNATIONAL','HANFORD MUNICIPAL AIRPORT','VISALIA MUNICIPAL AIRPORT','MEADOWS FIELD AIRPORT']


#location:  USAF,country, lat, long, elev ,daytime RH, nightime RH, timezone, wet season RH avgs, dry season RH avgs
stations = {
'SACRAMENTO EXECUTIVE AIRPORT'  :[724830, 'UNITED STATES', 38.507,  -121.495, 0004.6,{},{},-8,[],[],'red'],
'MDSTO CTY-CO H SHAM FD APT'    :[724926, 'UNITED STATES', 37.624,  -120.951, 0022.3,{},{},-8,[],[],'blue'],
'FRESNO YOSEMITE INTERNATIONAL' :[723890, 'UNITED STATES', 36.780,  -119.719, 0101.5,{},{},-8,[],[],'green'],
'HANFORD MUNICIPAL AIRPORT'     :[723898, 'UNITED STATES', 36.319,  -119.629, 0075.9,{},{},-8,[],[],'cyan'],
'VISALIA MUNICIPAL AIRPORT'     :[723896, 'UNITED STATES', 36.317,  -119.400, 0089.9,{},{},-8,[],[],'black'],
'MEADOWS FIELD AIRPORT'         :[723840, 'UNITED STATES', 35.434,  -119.054, 0149.1,{},{},-8,[],[],'magenta'], #
'UNIVERSITY AIRPORT'			:[720576, 'UNITED STATES', 38.533,  -121.783, 0021.0,{},{},-8,[],[],'b'],
'DAVIS'                         :[720576, 'UNITED STATES', 38.533,  -121.783, 0021.0,{},{},-8,[],[],'b'],
'CASTLE AFB'                    :[724810, 'UNITED STATES', 37.383,  -120.567, 0058.2,{},{},-8,[],[],'b'],
'SACRAMENTO MATHER AIRPORT'     :[724833, 'UNITED STATES', 38.567,  -121.300, 0030.2,{},{},-8,[],[],'b'],
'SACRAMENTO MCCLELLAN AFB'      :[724836, 'UNITED STATES', 38.667,  -121.400, 0023.5,{},{},-8,[],[],'b'],
'SACRAMENTO INTL AIRPORT'       :[724839, 'UNITED STATES', 38.696,  -121.590, 0007.0,{},{},-8,[],[],'b'],
'STOCKTON METROPOLITAN AIRPORT' :[724920, 'UNITED STATES', 37.889,  -121.226, 0007.9,{},{},-8,[],[],'b'],
'MADERA MUNICIPAL AIRPORT'      :[745046, 'UNITED STATES', 36.988,  -120.111, 0077.1,{},{},-8,[],[],'b'],
}


file = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/9450886574294dat.txt'

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
		RHx = float(newline[12])
		
		timezone = stations[stn][7]
	
		date = datetime.strptime(day, '%Y%m%d')
		datetime_local = datetime.strptime(day + ' ' + hour, '%Y%m%d %H%M') + timedelta(hours = timezone)  
		tomorrows_date = date + timedelta(days = 1)
		

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
	print stn
	am_data = stations[stn][5]
	pm_data = stations[stn][6]
	
	summer_am_avgs = stations[stn][8]
	summer_pm_avgs = stations[stn][9]
	
	night_count = 0
	day_count = 0
		
	
	for date, RHs in pm_data.iteritems():
		pm_avg_RH = np.mean(RHs)
		night_count +=1
			
		if date.month in [6,7,8,9]:
			summer_pm_avgs.append(pm_avg_RH)
			
	for date, RHs in am_data.iteritems():
		am_avg_RH = np.mean(RHs)
		day_count +=1
		if date.month in [6,7,8,9]:
			summer_am_avgs.append(am_avg_RH)
			

	
	print 'summer am data points', len(summer_pm_avgs)
	print 'summer pm data points', len(summer_am_avgs)

#Plotting


fig1 = plt.figure(figsize=(12,12))

bins_to_use = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]

label_x_pos = 0.05
label_y_pos = 0.85

see_Y_axis = True
y_upper_lim = 500


ax1w  = plt.subplot2grid((7,4), (0,0), colspan=1)
ax1d  = plt.subplot2grid((7,4), (0,1), colspan=1)
						
ax2w  = plt.subplot2grid((7,4), (1,0), colspan=1)
ax2d  = plt.subplot2grid((7,4), (1,1), colspan=1)
						
ax3w  = plt.subplot2grid((7,4), (2,0), colspan=1)
ax3d  = plt.subplot2grid((7,4), (2,1), colspan=1)
						
ax4w  = plt.subplot2grid((7,4), (3,0), colspan=1)
ax4d  = plt.subplot2grid((7,4), (3,1), colspan=1)
						
ax5w  = plt.subplot2grid((7,4), (4,0), colspan=1)
ax5d  = plt.subplot2grid((7,4), (4,1), colspan=1)
						
ax6w  = plt.subplot2grid((7,4), (5,0), colspan=1)
ax6d  = plt.subplot2grid((7,4), (5,1), colspan=1)
						


											
n,bins,patches = ax1w.hist(stations[stations_to_use[0]][8],bins_to_use, color=stations[stations_to_use[0]][10])
ax1w.yaxis.set_visible(see_Y_axis)
#ax1w.set_ylabel('Frequency\n Summer AM')
ax1w.text(label_x_pos, label_y_pos,'SACRAMENTO', transform=ax1w.transAxes)
ax1w.set_xlim(0,100)
ax1w.xaxis.set_label_position('top')
ax1w.set_xlabel('AM')
ax1w.set_ylim(0,y_upper_lim)
ax1w.xaxis.set_visible(True)
n,bins,patches = ax1d.hist(stations[stations_to_use[0]][9],bins_to_use, color=stations[stations_to_use[0]][10])
ax1d.yaxis.set_visible(see_Y_axis)
#ax1d.set_ylabel('Frequency\nSummer PM')
ax1d.set_xlim(0,100)
ax1d.xaxis.set_label_position('top')
ax1d.set_xlabel('PM')
ax1d.set_ylim(0,y_upper_lim)
ax1d.yaxis.set_visible(False)
ax1d.xaxis.set_visible(True)


n,bins,patches = ax2w.hist(stations[stations_to_use[1]][8],bins_to_use, color=stations[stations_to_use[1]][10])
ax2w.yaxis.set_visible(see_Y_axis)
ax2w.text(label_x_pos, label_y_pos,'MODESTO', transform=ax2w.transAxes)
ax2w.set_xlim(0,100)
ax2w.set_ylim(0,y_upper_lim)
ax2w.xaxis.tick_top()
ax2w.xaxis.set_visible(False)
n,bins,patches = ax2d.hist(stations[stations_to_use[1]][9],bins_to_use, color=stations[stations_to_use[1]][10])
ax2d.xaxis.set_visible(False)
ax2d.yaxis.set_visible(see_Y_axis)
ax2d.set_xlim(0,100)
ax2d.set_ylim(0,y_upper_lim)
ax2d.yaxis.set_visible(False)


n,bins,patches = ax3w.hist(stations[stations_to_use[2]][8],bins_to_use, color=stations[stations_to_use[2]][10])
ax3w.yaxis.set_visible(see_Y_axis)
ax3w.text(label_x_pos, label_y_pos,'FRESNO', transform=ax3w.transAxes)
ax3w.set_xlim(0,100)
ax3w.set_ylim(0,y_upper_lim)
ax3w.xaxis.tick_top()
ax3w.xaxis.set_visible(False)
n,bins,patches = ax3d.hist(stations[stations_to_use[2]][9],bins_to_use, color=stations[stations_to_use[2]][10])
ax3d.xaxis.set_visible(False)
ax3d.yaxis.set_visible(see_Y_axis)
ax3d.set_xlim(0,100)
ax3d.set_ylim(0,y_upper_lim)
ax3d.yaxis.set_visible(False)


n,bins,patches = ax4w.hist(stations[stations_to_use[3]][8],bins_to_use, color=stations[stations_to_use[3]][10])
ax4w.yaxis.set_visible(see_Y_axis)
ax4w.text(label_x_pos, label_y_pos,'HANFORD', transform=ax4w.transAxes)
ax4w.set_xlim(0,100)
ax4w.set_ylim(0,y_upper_lim)
ax4w.xaxis.set_visible(False)
n,bins,patches = ax4d.hist(stations[stations_to_use[3]][9],bins_to_use, color=stations[stations_to_use[3]][10])
ax4d.xaxis.set_visible(False)
ax4d.yaxis.set_visible(see_Y_axis)
ax4w.set_xlabel('%RH')
ax4d.set_xlim(0,100)
ax4d.set_ylim(0,y_upper_lim)
ax4d.yaxis.set_visible(False)


n,bins,patches = ax5w.hist(stations[stations_to_use[4]][8],bins_to_use, color=stations[stations_to_use[4]][10])
ax5w.yaxis.set_visible(see_Y_axis)
ax5w.text(label_x_pos, label_y_pos,'VISALIA', transform=ax5w.transAxes)
ax5w.set_xlim(0,100)
ax5w.set_ylim(0,y_upper_lim)
n,bins,patches = ax5d.hist(stations[stations_to_use[4]][9],bins_to_use, color=stations[stations_to_use[4]][10])
ax5w.xaxis.set_visible(False)
ax5d.yaxis.set_visible(see_Y_axis)
ax5d.set_xlabel('%RH')
ax5d.set_xlim(0,100)
ax5d.set_ylim(0,y_upper_lim)
ax5d.xaxis.set_visible(False)
ax5d.yaxis.set_visible(False)

n,bins,patches = ax6w.hist(stations[stations_to_use[5]][8],bins_to_use, color=stations[stations_to_use[5]][10])
ax6w.yaxis.set_visible(see_Y_axis)
ax6w.text(label_x_pos, label_y_pos,'BAKERSFIELD', transform=ax6w.transAxes)
ax6w.set_xlim(0,100)
ax6w.set_ylim(0,y_upper_lim)
ax6w.set_xlabel('%RH')
n,bins,patches = ax6d.hist(stations[stations_to_use[5]][9],bins_to_use, color=stations[stations_to_use[5]][10])
ax6d.yaxis.set_visible(see_Y_axis)
ax6d.set_xlabel('%RH')
ax6d.set_xlim(0,100)
ax6d.set_ylim(0,y_upper_lim)
ax6d.yaxis.set_visible(False)




#####map


ax9  = plt.subplot2grid((7,4), (0,2), colspan=2, rowspan=7)

#####map

latStart = 33.5
latEnd = 39.5
lonStart = -123
lonEnd = -118
	
#mapping  
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


print np.min(topo_bathySmoothed),np.max(topo_bathySmoothed)


levels_list = []
for x in range(0,3000,100):
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
map.drawmapboundary(fill_color='#81BEF7')
#map.drawcoastlines()
map.drawcountries()
#map.drawstates()
#map.drawrivers()
#map.fillcontinents(color='grey')
map.drawmeridians(np.arange(lons.min(),lons.max(),2),labels=[0,0,0,1])
map.drawparallels(np.arange(lats.min(),lats.max(),2),labels=[1,0,0,0])


CS1 = map.contourf(x,y,topo_bathySmoothed,levels_list,
				cmap=mpl_util.LevelColormap(levels_list,cmap=cm.Greens),
				extend='max',
				alpha=1.,
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

		#if i==0:
		#	xn,yn = map(value[3], value[2]+0.04)
		#	plt.text(xn,yn, 'Benito Juarez Intl')
		#	
		#if i==1:
		#	xn,yn = map(value[3]-0.75, value[2]-0.1)
		#	plt.text(xn,yn, 'Mexico (Central) D.F.')
			
		x,y = map(value[3], value[2])	
		map.plot(x,y, color=stations[key][10], marker='o', linestyle = 'None', markersize = 8)
		i+=1

#####high res shapefiles for presentation purposes
road_info = map.readshapefile('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/shp/NA_road_atlas/road00l_shp/road_l','road',drawbounds=True) #GADM Data http://www.gadm.org/country
urbanarea_info = map.readshapefile('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/shp/Cal_2010_adjusted_urban_area/2010_adjusted_urban_area','urban',drawbounds=True) #US census bureau
USA_info = map.readshapefile('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/shp/US_coast/coastl_usa','USA',drawbounds=True) #GADM Data http://www.gadm.org/country

for nshape,seg in enumerate(map.road):
	xx,yy = zip(*seg)
	color = '#404040' 
	plt.plot(xx,yy,color=color)
	
for nshape,seg in enumerate(map.urban):
	xx,yy = zip(*seg)
	plt.fill(xx,yy,color = 'gray', alpha = 0.35, zorder=1)
	
for nshape,seg in enumerate(map.USA):
	xx,yy = zip(*seg)
	plt.plot(xx,yy,color = 'k', zorder=1)
	
map.drawmapscale(lonStart+0.75, latStart+1, lon_0, latStart, 100, barstyle='simple', units='km', fontsize=9, yoffset=None, labelstyle='simple', fontcolor='k', fillcolor1='w', fillcolor2='k', ax=None, format='%d', zorder=None)

	
#showing
plt.subplots_adjust(hspace=0.15)

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/NOAA NCDC RH Data/Central_Valley_RH.png',  bbox_inches='tight') 

plt.show()

