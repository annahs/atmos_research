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
from mpl_toolkits.basemap import Basemap

night_start_time = 18
night_end_time = 6

stations_to_use = ['TABATINGA','BARCELOS','ITAITUBA','MONTE DOURADO','CORONEL FRANCISCO SECADA VIGNE','LABREA','MANICORE','EDUARDO GOMES INTL']


#location:  USAF,country, lat, long, elev ,daytime RH, nightime RH, timezone, wet season RH avgs, dry season RH avgs
stations = {

'IAUARETE':  [820670,				       		'BRAZIL', 00.608,  -069.186,   0105.2,{},{},-4,[],[]],
'BARCELOS':  [821130,                      		'BRAZIL',-00.981 , -062.920,   0034.1,{},{},-4,[],[]],
'LABREA':  [827230,                        	   	'BRAZIL',-07.250,  -064.833,   0060.0,{},{},-4,[],[]],
'ITAITUBA':  [824450,                      		'BRAZIL',-04.267,  -055.983,   0045.0,{},{},-4,[],[]],
'MANICORE':  [825330,                     		'BRAZIL',-05.811,  -061.278,   0053.0,{},{},-4,[],[]],
'MONTE DOURADO':  [829170,            			'BRAZIL',-00.883 , -052.600,   0206.0,{},{},-3,[],[]],
'CORONEL FRANCISCO SECADA VIGNE':  [843770,		'PERU',  -03.785,  -073.309,   0093.3,{},{},-5,[],[]], #IQUITOS
'EDUARDO GOMES INTL': [821110,               	'BRAZIL',-03.039,  -060.050,   0080.5,{},{},-4,[],[]], #Manaus
'ITAITUBA AIRPORT': [824440,	                'BRAZIL',-04.242,  -056.001,   0033.5,{},{},-4,[],[]],
'TABATINGA': [824110,		                    'BRAZIL',-04.256,  -069.936,   0085.0,{},{},-4,[],[]],
}


file = 'C:/Users/Sarah Hanna/Documents/Data/Amazon RH/AmazonRHdat_combined_7420206406984_and_2327276533340_and_5960276533675.txt'

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
				
				daytime_data = stations[stn][5]
				nighttime_data = stations[stn][6]
				
				#get daytime data
				if datetime_local.hour >= night_end_time and datetime_local.hour < night_start_time:
					if date in daytime_data:
						daytime_data[date].append(RHx)
					else:
						daytime_data[date] = [RHx]
						
				#get nighttime data up to midnight
				if datetime_local.hour >= night_start_time and datetime_local.hour < 24:
					if date in nighttime_data:
						nighttime_data[date].append(RHx)
					else:
						nighttime_data[date] = [RHx]
					
				#get nighttime data after midnight
				if datetime_local.hour >= 0 and datetime_local.hour < night_end_time:
					date_to_use = date - timedelta(days = 1)
					
					if date_to_use in nighttime_data:
						nighttime_data[date_to_use].append(RHx)
					else:
						nighttime_data[date_to_use] = [RHx]


file_data = []		
combined_seasonal_and_station_data = []			
for stn in stations:
	if stn in stations_to_use:
		print stn
		daytime_data = stations[stn][5]
		nighttime_data = stations[stn][6]
		
		wet_season_avgs = stations[stn][8]
		dry_season_avgs = stations[stn][9]
		
		night_count = 0
		day_count = 0
			
		test_d = 0
		test_n = 0
			
		for date, RHs in nighttime_data.iteritems():
			nighttime_avg_RH = np.mean(RHs)
			night_count +=1
			test_n +=1
			if date.month in [12,1,2,3]:
				wet_season_avgs.append(nighttime_avg_RH)
				combined_seasonal_and_station_data.append(nighttime_avg_RH)
				
			if date.month in [6,7,8,9]:
				dry_season_avgs.append(nighttime_avg_RH)
				combined_seasonal_and_station_data.append(nighttime_avg_RH)
				
		for date, RHs in daytime_data.iteritems():
			daytime_avg_RH = np.mean(RHs)
			day_count +=1
			if day_count <= night_count:
				test_d +=1
				if date.month in [12,1,2,3]:
					wet_season_avgs.append(daytime_avg_RH)
					combined_seasonal_and_station_data.append(daytime_avg_RH)
					
				if date.month in [6,7,8,9]:
					dry_season_avgs.append(daytime_avg_RH)
					combined_seasonal_and_station_data.append(daytime_avg_RH)
					
		print test_n,test_d
		
		print 'wet seasons data points', len(wet_season_avgs)
		print 'dry seasons data points', len(dry_season_avgs)
		
		

#save to file

for stn in ['BARCELOS','LABREA','ITAITUBA','MANICORE','MONTE DOURADO','CORONEL FRANCISCO SECADA VIGNE','EDUARDO GOMES INTL', 'TABATINGA']:
	print stn 
	wet_season_data = stations[stn][8]
	dry_season_data = stations[stn][9]
	
	file_data.append([stn,'wet_season',np.percentile(wet_season_data,10),np.percentile(wet_season_data,25),np.percentile(wet_season_data,50),np.percentile(wet_season_data,75),np.percentile(wet_season_data,90)])
	file_data.append([stn,'dry_season',np.percentile(dry_season_data,10),np.percentile(dry_season_data,25),np.percentile(dry_season_data,50),np.percentile(dry_season_data,75),np.percentile(dry_season_data,90)])

file_name = 'Amazon RH'
file = open('C:/Users/Sarah Hanna/Documents/Data/Amazon RH/' + file_name +'.txt', 'w')
file.write('Calculated RH from NOAA NCDC database (https://gis.ncdc.noaa.gov/map/viewer/#app=cdo), values are based on 12h averages (1800-0600 local time and 0600-1800 local time) \n')
file.write('Wet season is Dec, Jan, Feb, Mar.  Dry season is June, July, Aug, Sept.\n')
file.write('City \t Season \t 10th_percentile_RH \t 25th_percentile_RH \t 50th_percentile_RH \t 75th_percentile_RH \t 90th_percentile_RH \n')
for row in file_data:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()		
		
		
#Plotting

fig1 = plt.figure(figsize=(12,12))

bins_to_use = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]

label_x_pos = 0.05
label_y_pos = 0.85

see_Y_axis = True
y_upper_lim = 500


ax1w  = plt.subplot2grid((7,4), (0,0), colspan=1)
ax1d  = plt.subplot2grid((7,4), (1,0), colspan=1)
						
ax2w  = plt.subplot2grid((7,4), (0,1), colspan=1)
ax2d  = plt.subplot2grid((7,4), (1,1), colspan=1)
						
ax3w  = plt.subplot2grid((7,4), (0,2), colspan=1)
ax3d  = plt.subplot2grid((7,4), (1,2), colspan=1)
						
ax4w  = plt.subplot2grid((7,4), (0,3), colspan=1)
ax4d  = plt.subplot2grid((7,4), (1,3), colspan=1)
						
ax5w  = plt.subplot2grid((7,4), (5,0), colspan=1)
ax5d  = plt.subplot2grid((7,4), (6,0), colspan=1)
						
ax6w  = plt.subplot2grid((7,4), (5,1), colspan=1)
ax6d  = plt.subplot2grid((7,4), (6,1), colspan=1)
						
ax7w  = plt.subplot2grid((7,4), (5,2), colspan=1)
ax7d  = plt.subplot2grid((7,4), (6,2), colspan=1)
						
ax8w  = plt.subplot2grid((7,4), (5,3), colspan=1)
ax8d  = plt.subplot2grid((7,4), (6,3), colspan=1)

											
n,bins,patches = ax1w.hist(stations['TABATINGA'][8],bins_to_use, color='blue')
ax1w.yaxis.set_visible(see_Y_axis)
ax1w.set_ylabel('Frequency\nWet season')
ax1w.text(label_x_pos, label_y_pos,'TABATINGA', transform=ax1w.transAxes)
ax1w.set_xlim(0,100)
ax1w.set_yticks(np.arange(0, 900, 200))
ax1w.xaxis.tick_top()
ax1w.xaxis.set_label_position('top')
ax1w.set_xlabel('%RH')
n,bins,patches = ax1d.hist(stations['TABATINGA'][9],bins_to_use, color='r')
ax1d.xaxis.set_visible(False)
ax1d.yaxis.set_visible(see_Y_axis)
ax1d.set_ylabel('Frequency\nDry season')
ax1d.set_xlim(0,100)
ax1d.set_yticks(np.arange(0, 900, 200))



n,bins,patches = ax2w.hist(stations['BARCELOS'][8],bins_to_use, color='blue')
ax2w.yaxis.set_visible(see_Y_axis)
ax2w.text(label_x_pos, label_y_pos,'BARCELOS', transform=ax2w.transAxes)
ax2w.set_xlim(0,100)
ax2w.set_ylim(0,y_upper_lim)
ax2w.xaxis.tick_top()
ax2w.xaxis.set_label_position('top')
ax2w.set_xlabel('%RH')
n,bins,patches = ax2d.hist(stations['BARCELOS'][9],bins_to_use, color='r')
ax2d.xaxis.set_visible(False)
ax2d.yaxis.set_visible(see_Y_axis)
ax2d.set_xlim(0,100)
ax2d.set_ylim(0,y_upper_lim)



n,bins,patches = ax3w.hist(stations['ITAITUBA'][8],bins_to_use, color='blue')
ax3w.yaxis.set_visible(see_Y_axis)
ax3w.text(label_x_pos, label_y_pos,'ITAITUBA', transform=ax3w.transAxes)
ax3w.set_xlim(0,100)
ax3w.set_ylim(0,y_upper_lim)
ax3w.xaxis.tick_top()
ax3w.xaxis.set_label_position('top')
ax3w.set_xlabel('%RH')
n,bins,patches = ax3d.hist(stations['ITAITUBA'][9],bins_to_use, color='r')
ax3d.xaxis.set_visible(False)
ax3d.yaxis.set_visible(see_Y_axis)
ax3d.set_xlim(0,100)
ax3d.set_ylim(0,y_upper_lim)



n,bins,patches = ax4w.hist(stations['MONTE DOURADO'][8],bins_to_use, color='blue')
ax4w.yaxis.set_visible(see_Y_axis)
ax4w.text(label_x_pos, label_y_pos,'MONTE DOURADO', transform=ax4w.transAxes)
ax4w.set_xlim(0,100)
ax4w.set_ylim(0,y_upper_lim)
ax4w.xaxis.tick_top()
ax4w.xaxis.set_label_position('top') 
n,bins,patches = ax4d.hist(stations['MONTE DOURADO'][9],bins_to_use, color='r')
ax4d.xaxis.set_visible(False)
ax4d.yaxis.set_visible(see_Y_axis)
ax4w.set_xlabel('%RH')
ax4d.set_xlim(0,100)
ax4d.set_ylim(0,y_upper_lim)



n,bins,patches = ax5w.hist(stations['CORONEL FRANCISCO SECADA VIGNE'][8],bins_to_use, color='blue')
ax5w.yaxis.set_visible(see_Y_axis)
ax5w.set_ylabel('Frequency\nWet season')
ax5w.text(label_x_pos, label_y_pos,'IQUITOS', transform=ax5w.transAxes)
ax5w.set_xlim(0,100)
#ax5w.set_ylim(0,850)
ax5w.set_yticks(np.arange(0, 900, 200))
n,bins,patches = ax5d.hist(stations['CORONEL FRANCISCO SECADA VIGNE'][9],bins_to_use, color='r')
ax5w.xaxis.set_visible(False)
ax5d.yaxis.set_visible(see_Y_axis)
ax5d.set_ylabel('Frequency\nDry season')
ax5d.set_xlabel('%RH')
ax5d.set_xlim(0,100)
#ax5d.set_ylim(0,850)
ax5d.set_yticks(np.arange(0, 900, 200))



n,bins,patches = ax6w.hist(stations['LABREA'][8],bins_to_use, color='blue')
ax6w.yaxis.set_visible(see_Y_axis)
ax6w.text(label_x_pos, label_y_pos,'LABREA', transform=ax6w.transAxes)
ax6w.set_xlim(0,100)
ax6w.set_ylim(0,y_upper_lim)
n,bins,patches = ax6d.hist(stations['LABREA'][9],bins_to_use, color='r')
ax6w.xaxis.set_visible(False)
ax6d.yaxis.set_visible(see_Y_axis)
ax6d.set_xlabel('%RH')
ax6d.set_xlim(0,100)
ax6d.set_ylim(0,y_upper_lim)


n,bins,patches = ax7w.hist(stations['MANICORE'][8],bins_to_use, color='blue')
ax7w.yaxis.set_visible(see_Y_axis)
ax7w.text(label_x_pos, label_y_pos,'MANICORE', transform=ax7w.transAxes)
ax7w.set_xlim(0,100)
#ax7w.set_ylim(0,y_upper_lim)
ax7w.set_yticks(np.arange(0, 600, 100))
n,bins,patches = ax7d.hist(stations['MANICORE'][9],bins_to_use, color='r')
ax7w.xaxis.set_visible(False)
ax7d.yaxis.set_visible(see_Y_axis)
ax7d.set_xlabel('%RH')
ax7d.set_xlim(0,100)
#ax7d.set_ylim(0,y_upper_lim)
ax7d.set_yticks(np.arange(0, 600, 100))

n,bins,patches = ax8w.hist(stations['EDUARDO GOMES INTL'][8],bins_to_use, color='blue')
ax8w.yaxis.set_visible(see_Y_axis)
ax8w.text(label_x_pos, label_y_pos,'MANAUS', transform=ax8w.transAxes)
ax8w.set_xlim(0,100)
ax8w.set_ylim(0,600)
ax8w.set_yticks(np.arange(0, 900, 200))
n,bins,patches = ax8d.hist(stations['EDUARDO GOMES INTL'][9],bins_to_use, color='r')
ax8w.xaxis.set_visible(False)
ax8d.yaxis.set_visible(see_Y_axis)
ax8d.set_xlabel('%RH')
ax8d.set_xlim(0,100)
ax8d.set_ylim(0,600)
ax8d.set_yticks(np.arange(0, 900, 200))



#####map
ax9  = plt.subplot2grid((7,4), (2,0), colspan=4, rowspan=3)
lat_pt = 0.5
lon_pt = -60.
plt_lat_min = -13.
plt_lat_max = 7.
plt_lon_min = -82.
plt_lon_max = -40.
	
#mapping  
m = Basemap(
			projection = 'lcc',
			llcrnrlat=plt_lat_min, urcrnrlat=plt_lat_max,
			llcrnrlon=plt_lon_min, urcrnrlon=plt_lon_max,
			rsphere=(6378137.00,6356752.3142), resolution='l', area_thresh=100.,
			lat_1 = lat_pt,lon_0 = lon_pt
			)  

m.drawmapboundary(fill_color='white') 

#rough shapes 
m.drawcoastlines()
#m.fillcontinents(color='#FFFFBF',lake_color='#ABD9E9',zorder=1)
m.drawcountries()
m.bluemarble()


stn_lons = []
stn_lats = []
for key, value in stations.iteritems():
	if key in stations_to_use:	
		stn_lons.append(value[3])
		stn_lats.append(value[2])

x,y = m(stn_lons, stn_lats)
m.plot(x,y, color='red', marker='o', linestyle = 'None', markersize = 8)
		
plt.subplots_adjust(hspace=0.15)

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Amazon RH/Amazon_RH.png',  bbox_inches='tight') 

plt.show()





###next plot 

fig2 = plt.figure(figsize = (8,8))

bin_number = 20
bin_range = (0,100)

label_x_pos = 0.05
label_y_pos = 0.85


ax1  = plt.subplot2grid((1,1), (0,0), colspan=1)

						

											
n,bins,patches = ax1.hist(combined_seasonal_and_station_data,bins = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100],  color='blue')
ax1.yaxis.set_visible(True)
ax1.set_ylabel('Frequency')
#ax1.text(label_x_pos, label_y_pos,'ALL STATIONS', transform=ax1.transAxes)
ax1.set_xlim(0,100)
ax1.xaxis.set_label_position('bottom')
ax1.set_xlabel('12-hr averaged %RH')




plt.subplots_adjust(hspace=0.05)

#plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Amazon RH/Amazon_RH_all_stations - combined seasons - 12hr avgs.png',  bbox_inches='tight') 



#save data to file 
stn_list = ', '.join(stations_to_use)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Amazon RH/')

file = open('Amazon Basin RH - combined wet and dry seasons for all stations - 12hr avgs.txt', 'w')
file.write('Amazon Basin %RH - combined wet and dry seasons for all stations  - 12hr avgs (' + stn_list + ')' +  '\n')
file.write('0-5%' + '\t' + '5-10%' + '\t' + '10-15%' + '\t' + '15-20%' + '\t' +'20-25%' + '\t' +'25-30%' + '\t' +'30-35%' + '\t' +'35-40%' + '\t' + '40-45%' + '\t' +'45-50%' + '\t' +'50-55%' + '\t' +'55-60%' + '\t' +'60-65%' + '\t' +'65-70%' + '\t' + '70-75%' + '\t' +'75-80%' + '\t' +'80-85%' + '\t' +'85-90%' + '\t' +'90-95%' + '\t' +'95-100%'+'\n')
for row in n: 
	file.write(str(row) + '\t')
file.close()

plt.show()


