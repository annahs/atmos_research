import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import os
import sys
import matplotlib.colors
import colorsys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import mmap

GBPS_lat_min = 48.0
GBPS_lat_max = 49.4
GBPS_lon_min = -123.5
GBPS_lon_max = -122

GBPS_lat_min_2 = 47.0
GBPS_lat_max_2 = 48
GBPS_lon_min_2 = -122.75
GBPS_lon_max_2 = -122

timezone = timedelta(hours = -8)

endpointsWHI =  {}

dir ='C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/clustering/'
os.chdir(dir)


cluster_no = 0	
for file in os.listdir('.'):
	if file.endswith('1mean.tdump'):
		
		tdump_file = open(file, 'r')
		print file
		endpoints = []
		data_start = False
	
		
		for line in tdump_file:
			newline = line.split()
			
			
			
			if data_start == True:
				lat = float(newline[9])
				lon = float(newline[10])
				hr_back =  float(newline[8])
				pressure = float(newline[11]) #in hPa
				year =  int(newline[2])
				month = int(newline[3])
				day = int(newline[4])
				hour = int(newline[5])
				Py_datetime_UTC = datetime(year, month, day, hour)
				Py_datetime = Py_datetime_UTC + timezone
				
				endpoint = [lat, lon, hr_back]
				endpoints.append(endpoint)
				

			if newline[1] == 'PRESSURE':
				data_start = True
		
		tdump_file.close() 
		
		endpointsWHI[cluster_no]=endpoints
		cluster_no +=1



#plottting
###set up the basemap instance  
lat_pt = 55.06
lon_pt = -160
plt_lat_min = -10
plt_lat_max = 90#44.2
plt_lon_min = -250#-125.25
plt_lon_max = -100

m = Basemap(width=6000000,height=5500000,
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



linewidth = 2
pre_linewidth = 2
alphaval = 1

S = 1.0#0.1
hue = 0#0.65
i=0

color_maps = ['Blues','Greens','Reds','Greys','Purples','Oranges']
colors = ['r','orange','b','g','m','k','y','#DF7401','#585858']
#labels = ['1','2','3','4','5','6','7','>24hrs in GBPS']
labels = ['N. Canada (14)','W. Pacific/Asia (18)','N. Pacific (88)','S. Pacific (34)',]
#labels = ['Bering (18%)','Northern Coastal/Continental (9%)','Northern Pacific (24%)','Southern Pacific (14%)','Western Pacific/Asia (17%)']
for cluster_no, endpoints in endpointsWHI.items():
	print cluster_no
	np_endpoints = np.array(endpoints)
	lats = np_endpoints[:,0] 
	lons = np_endpoints[:,1]
	pressure = np_endpoints[:,2]
	x,y = m(lons,lats)
	#bt = m.scatter(x,y, c=pressure, cmap=plt.get_cmap('jet'),edgecolors='none', marker='o', label = str(cluster_no+1) ) #marker = '$'+str(cluster_no+1)+'$' 
	bt = m.plot(x,y,linewidth = linewidth, color =colors[cluster_no], label= labels[i])
	
	i+=1
#cb = plt.colorbar()
plt.legend(loc = 3)

##draw 200km radius around whistler
#rad_lons = [-122.95731899999998, -122.76210307991437, -122.56783823216847, -122.3754708955729, -122.18593826445493, -122.0001637227416, -121.81905234532621,-121.64348648863421, -121.47432149187159, -121.31238150989822, -121.15845549802805, -121.01329336831839, -120.87760233607344, -120.75204347436284, -120.63722849333953, -120.53371676005008, -120.44201257325398, -120.36256270653126, -120.29575423164636, -120.24191263277328, -120.20130022076967, -120.17411485522439, -120.16048898050582, -120.16048898050582, -120.17411485522439, -120.20130022076967, -120.24191263277328, -120.29575423164636, -120.36256270653126, -120.44201257325398, -120.53371676005008, -120.63722849333953, -120.75204347436284, -120.87760233607344, -121.01329336831839, -121.15845549802805, -121.31238150989822, -121.47432149187159, -121.64348648863421, -121.81905234532621, -122.0001637227416, -122.18593826445493, -122.3754708955729, -122.56783823216847, -122.76210307991437, -122.95731899999998, -123.1525349200856, -123.3467997678315, -123.53916710442707, -123.72869973554504, -123.91447427725836, -124.09558565467376, -124.27115151136576, -124.44031650812838, -124.60225649010175, -124.75618250197192, -124.90134463168158, -125.03703566392653, -125.16259452563713, -125.27740950666043, -125.38092123994988, -125.47262542674599, -125.5520752934687, -125.61888376835361, -125.67272536722669, -125.7133377792303, -125.74052314477558, -125.75414901949415, -125.75414901949415, -125.74052314477558, -125.7133377792303, -125.67272536722669, -125.61888376835361, -125.5520752934687, -125.47262542674599, -125.38092123994988, -125.27740950666043, -125.16259452563713, -125.03703566392653, -124.90134463168158, -124.75618250197192, -124.60225649010175, -124.44031650812838, -124.27115151136576, -124.09558565467376, -123.91447427725836, -123.72869973554504, -123.53916710442707, -123.3467997678315, -123.1525349200856, -122.95731899999998]
#rad_lats = [51.85601099067367, 51.85163446351925, 51.83852620405636, 51.81675007440746, 51.786412165687274, 51.74766028113753, 51.70068321604443, 51.645709837946995, 51.5830079716174, 51.51288309424564, 51.43567684718534, 51.35176537151143, 51.261557475498655, 51.165492642948706, 51.06403889206937, 50.957690495336834, 50.84696557144988, 50.73240356110765, 50.614562598908805, 50.49401679417584, 50.371353433952194, 50.247170121798796, 50.1220718663296, 49.99666813367041, 49.87156987820121, 49.74738656604781, 49.62472320582416, 49.5041774010912, 49.38633643889235, 49.271774428550124, 49.16104950466317, 49.05470110793063, 48.953247357051296, 48.85718252450135, 48.76697462848857, 48.68306315281466, 48.605856905754365, 48.535732028382604, 48.47303016205301, 48.41805678395557, 48.371079718862475, 48.33232783431273, 48.301989925592544, 48.280213795943645, 48.267105536480756, 48.262729009326335, 48.267105536480756, 48.280213795943645, 48.301989925592544, 48.33232783431273, 48.371079718862475, 48.41805678395557, 48.47303016205301, 48.535732028382604, 48.605856905754365, 48.68306315281466, 48.76697462848857, 48.85718252450135, 48.953247357051296, 49.05470110793063, 49.16104950466317, 49.271774428550124, 49.38633643889235, 49.5041774010912, 49.62472320582416, 49.74738656604781, 49.87156987820121, 49.996668133670404, 50.1220718663296, 50.247170121798796, 50.371353433952194, 50.49401679417584, 50.614562598908805, 50.73240356110765, 50.84696557144988,50.957690495336834, 51.06403889206937, 51.165492642948706, 51.26155747549865, 51.35176537151143, 51.43567684718534, 51.51288309424564, 51.5830079716174, 51.645709837946995, 51.70068321604443, 51.74766028113753, 51.786412165687274, 51.81675007440746, 51.83852620405636, 51.85163446351925, 51.85601099067367]
#rad_x,rad_y = m(rad_lons, rad_lats)
#m.plot(rad_x,rad_y,linestyle='--', marker='None', color = 'b')


##GBPS box 1
#lats = [GBPS_lat_max,GBPS_lat_min,GBPS_lat_min,GBPS_lat_max, GBPS_lat_max]
#lons = [GBPS_lon_max,GBPS_lon_max,GBPS_lon_min,GBPS_lon_min, GBPS_lon_max]
#x,y = m(lons,lats)
#hb = m.plot(x,y, color = 'red',linewidth = 2.0)
#
##GBPS box 2
#lats = [GBPS_lat_max_2,GBPS_lat_min_2,GBPS_lat_min_2,GBPS_lat_max_2, GBPS_lat_max_2]
#lons = [GBPS_lon_max_2,GBPS_lon_max_2,GBPS_lon_min_2,GBPS_lon_min_2, GBPS_lon_max_2]
#x,y = m(lons,lats)
#hb = m.plot(x,y, color = 'red',linewidth = 2.0)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/')

plt.savefig('cluster_means_from_HYSPLIT-4clusters.png', bbox_inches='tight') 
plt.show()




