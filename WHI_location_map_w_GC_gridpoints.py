import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
import os
import sys
import matplotlib.colors
import colorsys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
from scipy.io import netcdf
from matplotlib.patches import Polygon



os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record')
    

###set up the basemap instance  

lat_pt = 50.06
lon_pt = -142.96
plt_lat_min = 46
plt_lat_max = 55#44.2
plt_lon_min = -136
plt_lon_max = -114

#m = Basemap(projection='npstere',boundinglat=30,lon_0=270,resolution='l')

#get CanAM4 locations
file_name = 'sc_vef12_2008_m01_concbc_2009010100-2013120100.nc'
f = netcdf.netcdf_file('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/CCMA data/full_runs/' + file_name, 'r')

variableNames = f.variables.keys()

vef12_lats = f.variables['lat'].data
vef12_lons = f.variables['lon'].data


###set up the basemap boundaries  



#set up grid points to map
lon_min = -126
lon_max = -120
coords = []
for lat in vef12_lats:
	if lat >= 48 and lat <=  52:
		for lon in vef12_lons:
			if lon >= 360+lon_min and lon <=  360+lon_max:
				print lon-360, np.where(vef12_lons==lon), lat, np.where(vef12_lats==lat)
				new_coord = [lon, lat]
				coords.append(new_coord)
	
	
#mapping  
m = Basemap(
            projection = 'lcc',
            llcrnrlat=plt_lat_min, urcrnrlat=plt_lat_max,
            llcrnrlon=plt_lon_min, urcrnrlon=plt_lon_max,
            rsphere=(6378137.00,6356752.3142), resolution='l', area_thresh=100.,
            lat_1 = lat_pt,lon_0 = lon_pt
            )  

    


			
# make plot 
fig = plt.figure()
ax = fig.add_subplot(111)
m.drawmapboundary(fill_color='white') 

#rough shapes 
m.drawcoastlines()
m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=1)
m.drawcountries()

parallels = np.arange(0.,81,5.)
# labels = [left,right,top,bottom]
m.drawparallels(parallels,labels=[False,True,True,False])
meridians = np.arange(10.,351.,5.)
m.drawmeridians(meridians,labels=[True,False,False,True])


####other data

#label WHI
WHI_lon = -122.96
WHI_lat = 50.06
WHI_x,WHI_y = m(WHI_lon, WHI_lat)
plt.text(WHI_x-33000,WHI_y+25000,'WHI')
m.plot(WHI_x,WHI_y, color='red', marker='*', linestyle = 'None',markersize = 10, label = 'WHI')

##CanAM4 gridpoints
#lons_inarea = [row[0] for row in coords]
#lats_inarea = [row[1] for row in coords]
#
#x,y = m(lons_inarea, lats_inarea)
#m.plot(x,y, color='green', marker='o', linestyle = 'None', label = 'CanAM4 grid points',markersize = 8)

#GEOS-Chem grid point
GC_lon = -122.500
GC_lat = 50.000
x,y = m(GC_lon, GC_lat)
#m.plot(x,y, color='green', marker='o', linestyle = 'None', label = 'GEOS-Chem grid point',markersize = 8)

def draw_screen_poly( lats, lons, m):
    x, y = m( lons, lats )
    xy = zip(x,y)
    poly = Polygon( xy, facecolor='grey', alpha=0.4 )
    plt.gca().add_patch(poly)

#GEOS-Chem grid box
lats = [51,51,49,49,51]
lons = [-125,-120,-120,-125,-125]
draw_screen_poly( lats, lons, m)

#label Vancouer and Seattle
Van_lon = -123.1
Van_lat = 49.25
Van_x,Van_y = m(Van_lon, Van_lat)
plt.text(Van_x-5000,Van_y+10000,'Vancouver')
m.plot(Van_x,Van_y, color='blue', linestyle = 'None',marker='^', label = 'Nearby Cities',markersize = 10)

Sea_lon = -122.333056
Sea_lat = 47.609722
Sea_x,Sea_y = m(Sea_lon, Sea_lat)
plt.text(Sea_x-5000,Sea_y+10000,'Seattle')
m.plot(Sea_x,Sea_y, color='blue',linestyle = 'None', marker='^',markersize = 10)

#north arrow
#arrow_lon = -130
#arrow_lat = 48
#arrow_x,arrow_y = m(arrow_lon, arrow_lat)
#m.quiver(arrow_x,arrow_y,100, 100)




#draw map scale
scale_lat = 46
scale_lon = -132
m.drawmapscale(scale_lon, scale_lat, -122, 50, 200, barstyle='simple', units='km', fontsize=9, yoffset=None, labelstyle='simple', fontcolor='k', fillcolor1='w', fillcolor2='k', ax=None, format='%d', zorder=None)



plt.legend(numpoints=1)
plt.savefig('WHI_location.png') 
plt.show()