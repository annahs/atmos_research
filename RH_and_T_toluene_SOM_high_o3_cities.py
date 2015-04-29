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

afternoon_start = 15
afternoon_end = 17

night_start_time = 18
night_end_time = 6


#location:  USAF,city, lat, long, elev ,daytime RH and T, nightime RH and T, timezone
stations = {

'DOWNTOWN L.A./USC CAMPUS':				[722874,	'Los Angeles-Long Beach',		 	34.024,  -118.291,   0054.6,	{},	{},	-8  ], 
'BRACKETT FIELD AIRPORT':      			[722887,	'Los Angeles-Long Beach',		 	34.100,  -117.783,   0308.2,	{},	{},	-8  ],
'BRACKETT FLD':			      			[722887, 	'Los Angeles-Long Beach',		 	34.083,  -117.783,   0308.0,	{},	{},	-8  ],
'LOS ANGELES INTERNATIONAL AIRP':		[722950, 	'Los Angeles-Long Beach',		 	33.938,  -118.389,   0029.6,	{},	{},	-8  ],
'LONG BEACH / DAUGHERTY FIELD /':		[722970, 	'Los Angeles-Long Beach',	 		33.812,  -118.146,   0009.5,	{},	{},	-8  ],
'FULLERTON MUNICIPAL ARPT':      		[722976, 	'Los Angeles-Long Beach',	 		33.872,  -117.979,   0029.3,	{},	{},	-8  ],
'FULLERTON MUNICIPAL':           		[722976, 	'Los Angeles-Long Beach',	 		33.867,  -117.983,   0029.0,	{},	{},	-8  ],
'J. WAYNE APT-ORANGE CO APT':   		[722977, 	'Los Angeles-Long Beach',	 		33.680,  -117.866,   0016.5,	{},	{},	-8  ],

'PORTERVILLE MUNICIPAL ARPT':			[723895,	'Visalia-Porterville-Hanford',	 	36.029,  -119.063,   0134.7,	{},	{},	-8  ], 
'PORTERVILLE MUNI': 					[723895,	'Visalia-Porterville-Hanford',	 	36.033,  -119.067,   0135.0,	{},	{},	-8  ],
'VISALIA MUNICIPAL AIRPORT':			[723896, 	'Visalia-Porterville-Hanford',	 	36.317,  -119.400,   0089.9,	{},	{},	-8  ],
'VISALIA MUNI':							[723896, 	'Visalia-Porterville-Hanford',	 	36.317,  -119.400,   0090.0,	{},	{},	-8  ],
'HANFORD MUNICIPAL AIRPORT':			[723898, 	'Visalia-Porterville-Hanford',	 	36.319,  -119.629,   0075.9,	{},	{},	-8  ],
'HANFORD MUNI':             			[723898, 	'Visalia-Porterville-Hanford',	 	36.317,  -119.633,   0074.0,	{},	{},	-8  ],

'MEADOWS FIELD AIRPORT':	  			[723840, 	'Bakersfield',		 				35.434,  -119.054,   0149.1,	{},	{},	-8  ],

'FRESNO YOSEMITE INTERNATIONAL':   		[723890, 	'Fresno-Madera',	 				36.780,  -119.719,   0101.5,	{},	{},	-8  ],
'MADERA MUNICIPAL AIRPORT':		  		[745046, 	'Fresno-Madera',	 				36.988,  -120.111,   0077.1,	{},	{},	-8  ],
'MADERA MUNI':                     		[745046, 	'Fresno-Madera',	 				36.987,  -120.113,   0077.0,	{},	{},	-8  ],

'SACRAMENTO EXECUTIVE AIRPORT': 		[724830, 	'Sacramento-Roseville',	 			38.507,  -121.495,   0004.6,	{},	{},	-8  ],
'SACRAMENTO MATHER AIRPORT':     		[724833, 	'Sacramento-Roseville',	 			38.567,  -121.300,   0030.2,	{},	{},	-8  ],
'SACRAMENTO INTL AIRPORT':        		[724839, 	'Sacramento-Roseville',	 			38.696,  -121.590,   0007.0,	{},	{},	-8  ],

'HOOKS MEMORIAL AIRPT':        			[723896, 	'Houston-The Woodlands',	 		30.068,  -095.556,	 0046.3,	{},	{},	-6  ],
'HOUSTON/D.W. HOOKS':          			[723896, 	'Houston-The Woodlands',	 		30.067,  -095.550,	 0046.0,	{},	{},	-6  ],
'G BUSH INTERCONTINENTAL AP/HOU':		[723898, 	'Houston-The Woodlands',	 		29.980,  -095.360,	 0029.0,	{},	{},	-6  ],
'WILLIAM P HOBBY':		    			[723898, 	'Houston-The Woodlands',	 		29.638,  -095.282,	 0014.3,	{},	{},	-6  ],
'WILLIAM P. HOBBY AIRPORT':           	[723898, 	'Houston-The Woodlands',	 		29.638,  -095.282,	 0013.4,	{},	{},	-6  ],

'CASTLE AFB':			          		[724810, 	'Modesto-Merced',	 				37.383,  -120.567,   0058.2,	{},	{},	-8  ],
'MRCD MUNI/MACREADY FLD APT':			[724815, 	'Modesto-Merced',	 				37.285,  -120.513,   0046.3,	{},	{},	-8  ],
'MERCED MUNI MACREADY':					[724815, 	'Modesto-Merced',	 				37.285,  -120.514,   0048.0,	{},	{},	-8  ],
'MDSTO CTY-CO H SHAM FD APT':		 	[724926, 	'Modesto-Merced',	 				37.624,  -120.951,   0022.3,	{},	{},	-8  ],

'DALLAS LOVE FIELD AIRPORT':       		[722580, 	'Dallas-Fort Worth',	 			32.852,  -096.856,	 0134.1,	{},	{},	-6  ],
'DALLAS/FT WORTH INTERNATIONAL':		[722590, 	'Dallas-Fort Worth',	 			32.898,  -097.019,	 0170.7,	{},	{},	-6  ],
'FORT WORTH ALLIANCE ARPT':    			[722594, 	'Dallas-Fort Worth',	 			32.973,  -097.318,	 0208.8,	{},	{},	-6  ],
'FORT WORTH ALLIANCE':         		 	[722594, 	'Dallas-Fort Worth',	 			32.983,  -097.317,	 0220.0,	{},	{},	-6  ],

'COLLEGE PARK':                    		[722244, 	'Washington-Baltimore-Arlington',	38.981,  -076.922,   0014.6,	{},	{},	-5  ],
'WASHINGTON DULLES INTERNATIONA':		[724030, 	'Washington-Baltimore-Arlington',	38.941,  -077.464,   0088.4,	{},	{},	-5  ],
'BALTIMORE-WASHINGTON INTL AIRP':		[724060, 	'Washington-Baltimore-Arlington',	39.167,  -076.683,   0047.6,	{},	{},	-5  ],
'BALTIMORE DOWNTOWN':	         	 	[745944, 	'Washington-Baltimore-Arlington',	39.281,  -076.609,   0006.1,	{},	{},	-5  ],

'HENDERSON EXECUTIVE ARPT':      		[722096, 	'Las Vegas-Henderson',				35.976,  -115.133,   0749.2,	{},	{},	-8  ],
'HENDERSON EXECUTIVE':           		[722096, 	'Las Vegas-Henderson',				35.967,  -115.134,   0760.0,	{},	{},	-8  ],
'MCCARRAN INTERNATIONAL AIRPORT':		[723860, 	'Las Vegas-Henderson',				36.072,  -115.163,   0664.5,	{},	{},	-8  ],
'NELLIS AFB AIRPORT':            	 	[723865, 	'Las Vegas-Henderson',				36.250,  -115.033,   0570.0,	{},	{},	-8  ],

'PHOENIX SKY HARBOR INTL AIRPOR':		[722780, 	'Phoenix-Mesa-Scottsdale',			33.428,  -112.004,   0337.4,	{},	{},	-7  ],
'WILLIAMS GATEWAY AIRPORT':      		[722786, 	'Phoenix-Mesa-Scottsdale',			33.300,  -111.667,   0421.2,	{},	{},	-7  ],
'SCOTTSDALE AIRPORT':            		[722789, 	'Phoenix-Mesa-Scottsdale',			33.623,  -111.911,   0449.0,	{},	{},	-7  ],
'SCOTTSDALE':                    	 	[722789, 	'Phoenix-Mesa-Scottsdale',			33.623,  -111.911,   0460.0,	{},	{},	-7  ],

'NEWARK LIBERTY INTERNATIONAL A':      	[725020, 	'New York-Newark',					40.683,  -074.169,   0002.1,	{},	{},	-5  ],
'LA GUARDIA AIRPORT':                  	[725030, 	'New York-Newark',					40.779,  -073.880,   0003.4,	{},	{},	-5  ],
'JOHN F KENNEDY INTERNATIONAL A':      	[744860, 	'New York-Newark',					40.639,  -073.762,   0003.4,	{},	{},	-5  ],

'SCOTT AIR FORCE BASE/MIDAMERIC':		[724338, 	'St. Louis-St. Charles-Farmington',	38.550,  -089.850,	 0139.9,	{},	{},	-6  ],
'LAMBERT-ST LOUIS INTERNATIONAL':		[724340, 	'St. Louis-St. Charles-Farmington',	38.753,  -090.374,	 0161.9,	{},	{},	-6  ],
'ST CHARLES CO SMARTT ARPT':     		[724347, 	'St. Louis-St. Charles-Farmington',	38.929,  -090.428,	 0132.9,	{},	{},	-6  ],
'ST CHARLES CO SMARTT':          	 	[724347, 	'St. Louis-St. Charles-Farmington',	38.933,  -090.433,	 0133.0,	{},	{},	-6  ],

'TULSA INTERNATIONAL AIRPORT':			[723560, 	'Tulsa-Muskogee-Bartlesville',		36.199,  -095.887,   0198.1,	{},	{},	-6  ],
'RICHARD LLOYD JONES JR APT': 			[723564, 	'Tulsa-Muskogee-Bartlesville',		36.039,  -095.984,   0194.5,	{},	{},	-6  ],
'RICHARD LLOYD JONES':        	 		[723564, 	'Tulsa-Muskogee-Bartlesville',		36.033,  -095.983,   0194.0,	{},	{},	-6  ],

'CINCINNATI/NORTHERN KENTUCKY I': 		[724210, 	'Cincinnati-Wilmington-Maysville',	39.043,  -084.672,   0264.9,	{},	{},	-5  ],
'CINA MUNI APT/LUKN FD APT':      	 	[724297, 	'Cincinnati-Wilmington-Maysville',	39.103,  -084.419,   0149.4,	{},	{},	-5  ],

}

#city: monthly RH data, monthly temp data
cities = {
'Los Angeles-Long Beach': 			[{},{}],
'Visalia-Porterville-Hanford': 		[{},{}],
'Bakersfield':						[{},{}],
'Fresno-Madera':					[{},{}],
'Sacramento-Roseville':	 			[{},{}],			
'Houston-The Woodlands':	 		[{},{}],	
'Modesto-Merced':	 				[{},{}],
'Dallas-Fort Worth':	 			[{},{}],			
'Washington-Baltimore-Arlington':	[{},{}],
'Las Vegas-Henderson':				[{},{}],		
'Phoenix-Mesa-Scottsdale':			[{},{}],	
'New York-Newark':					[{},{}],			
'St. Louis-St. Charles-Farmington':	[{},{}],
'Tulsa-Muskogee-Bartlesville':		[{},{}],		
'Cincinnati-Wilmington-Maysville':  [{},{}],
}               

low_RH_city_ordered_list = ['Visalia-Porterville-Hanford','Bakersfield','Fresno-Madera','Sacramento-Roseville','Modesto-Merced','Las Vegas-Henderson','Phoenix-Mesa-Scottsdale']		
				
high_RH_city_ordered_list = ['Los Angeles-Long Beach','Houston-The Woodlands','Dallas-Fort Worth','Washington-Baltimore-Arlington','New York-Newark','St. Louis-St. Charles-Farmington','Tulsa-Muskogee-Bartlesville','Cincinnati-Wilmington-Maysville']		


data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/high o3 cities NOAA NCDC data/'
os.chdir(data_dir)
for file in os.listdir(data_dir):
	if file.endswith('dat.txt'):
		print file
		with open(file, 'r') as f:
			f.readline()
			f.readline()

			for line in f:
				
				newline = line.split(',')
				stn = newline[0].rstrip() 
				if stn in stations.keys():
				
					day = newline[3]
					hour = newline[4]	# in UTC
					temp = float(newline[8])
					temp_qc = newline[9]
					dewp_qc = newline[11]
					RHx = float(newline[12])
					timezone = stations[stn][7]
				
					date = datetime.strptime(day, '%Y%m%d')
					datetime_local = datetime.strptime(day + ' ' + hour, '%Y%m%d %H%M') + timedelta(hours = timezone)  #std time 
					date_local = datetime(datetime_local.year, datetime_local.month, datetime_local.day)

					#data QC
					if temp_qc in ['1','5'] and dewp_qc in ['1','5']:  #data has 'Passed all quality control checks'  
						
						daytime_data = stations[stn][5]
						nighttime_data = stations[stn][6]
						
						#get afternoon-only data
						if datetime_local.hour >= afternoon_start and datetime_local.hour < afternoon_end:
							if date_local in daytime_data:
								daytime_data[date_local].append([RHx,temp])
							else:
								daytime_data[date_local] = [[RHx,temp]]
											
						
						
						##get daytime data
						#if datetime_local.hour >= night_end_time and datetime_local.hour < night_start_time:
						#	if date_local in daytime_data:
						#		daytime_data[date_local].append([RHx,temp])
						#	else:
						#		daytime_data[date_local] = [[RHx,temp]]
						#		
						##get nighttime data up to midnight
						#if datetime_local.hour >= night_start_time and datetime_local.hour < 24:
						#	if date_local in nighttime_data:
						#		nighttime_data[date_local].append([RHx,temp])
						#	else:
						#		nighttime_data[date_local] = [[RHx,temp]]
						#	
						##get nighttime data after midnight
						#if datetime_local.hour >= 0 and datetime_local.hour < night_end_time:
						#	date_to_use = date_local - timedelta(days = 1)
						#	
						#	if date_to_use in nighttime_data:
						#		nighttime_data[date_to_use].append([RHx,temp])
						#	else:
						#		nighttime_data[date_to_use] = [[RHx,temp]]


		
for stn in stations:
	print stn
	night_count = 0
	day_count = 0
	
	daytime_data = stations[stn][5]
	nighttime_data = stations[stn][6]
	city = stations[stn][1]
	city_RHs = cities[city][0]
	city_Ts  = cities[city][1]
	
	
	#for date, data in nighttime_data.iteritems():
	#	RHs = [row[0] for row in data]
	#	Ts  = [row[1] for row in data]
	#	nighttime_avg_RH = np.mean(RHs)
	#	nighttime_avg_T  = np.mean(Ts)
	#	night_count += 1
	#	
	#	if date.month in city_RHs:
	#		city_RHs[date.month].append(nighttime_avg_RH)
	#	else:
	#		city_RHs[date.month] = [nighttime_avg_RH]
    #
	#	if date.month in city_Ts:
	#		city_Ts[date.month].append(nighttime_avg_T)
	#	else:
	#		city_Ts[date.month] = [nighttime_avg_T]
    #
	#print 'night_count', night_count
	
	for date, data in daytime_data.iteritems():
		RHs = [row[0] for row in data]
		Ts  = [row[1] for row in data]
		daytime_avg_RH = np.mean(RHs)
		daytime_avg_T  = np.mean(Ts)
		
		#if day_count <= night_count:
		day_count += 1
		if date.month in city_RHs:
			city_RHs[date.month].append(daytime_avg_RH)
		else:
			city_RHs[date.month] = [daytime_avg_RH]
		
		if date.month in city_Ts:
			city_Ts[date.month].append(daytime_avg_T)
		else:
			city_Ts[date.month] = [daytime_avg_T]
	
	print 'day_count', day_count


                                                                                        
#Plotting                                                                                   
                                                                                            

label_x_pos = 0.3
label_y_pos = 0.86
RH_lim = 107
T_lim = 58
T_min = -7
months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
span_color = 'red'
span_alpha_25 = 0.1
span_alpha_med = 0.2
RH_color = 'black'
temp_color = 'blue'


fig, axes = plt.subplots(4,2, figsize=(12, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)
axes[-1, -1].axis('off')


axs = axes.ravel()

i=0
for city in low_RH_city_ordered_list:
	RH_plot_data = []
	T_plot_data = []
	for month in range (1,13):                                                                  
		RH_plot_data.append(cities[city][0][month])                                    
		T_plot_data.append(cities[city][1][month]) 
	
	T_RH = axs[i].boxplot(RH_plot_data, whis=[10,90],sym='')
	plt.setp(T_RH['boxes'], color=RH_color)
	plt.setp(T_RH['whiskers'], color=RH_color,linestyle='-')
	plt.setp(T_RH['caps'], color=RH_color)
	plt.setp(T_RH['medians'], color=RH_color)
	axs[i].set_ylim(0,RH_lim)
	axs[i].set_ylabel('')
	axs[i].text(label_x_pos, label_y_pos,city,transform=axs[i].transAxes)
	axs[i].yaxis.grid(True, linestyle='-', which='major', color='grey', alpha=1)
	if i in [0,1]:
		axs[i].xaxis.tick_top()
		axs[i].set_xticklabels(months)	
	if i in [0,2,4,6]:
		axs[i].set_ylabel('%RH', color = RH_color)
	else:
		axs[i].set_yticklabels([])
	if city == 'Visalia-Porterville-Hanford':
		axs[i].axvspan(4.5,9.5, facecolor=span_color, alpha=span_alpha_med)
		axs[i].axvspan(3.5,4.5, facecolor=span_color, alpha=span_alpha_25)
		axs[i].axvspan(9.5,10.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Bakersfield':
		axs[i].axvspan(3.5,9.5, facecolor=span_color, alpha=span_alpha_med)
		axs[i].axvspan(2.5,3.5, facecolor=span_color, alpha=span_alpha_25)
		axs[i].axvspan(9.5,10.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Fresno-Madera':
		axs[i].axvspan(4.5,9.5, facecolor=span_color, alpha=span_alpha_med)
		axs[i].axvspan(3.5,4.5, facecolor=span_color, alpha=span_alpha_25)
		axs[i].axvspan(9.5,10.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Sacramento-Roseville':
		axs[i].axvspan(5.5,9.5, facecolor=span_color, alpha=span_alpha_med)
		axs[i].axvspan(3.5,5.5, facecolor=span_color, alpha=span_alpha_25)
		axs[i].axvspan(9.5,10.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Modesto-Merced':
		axs[i].axvspan(4.5,9.5, facecolor=span_color, alpha=span_alpha_med)
		axs[i].axvspan(3.5,4.5, facecolor=span_color, alpha=span_alpha_25)
		axs[i].axvspan(9.5,10.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Las Vegas-Henderson':
		axs[i].axvspan(0.5,11.5, facecolor=span_color, alpha=span_alpha_med)
		axs[i].axvspan(11.5,12.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Phoenix-Mesa-Scottsdale':
		axs[i].axvspan(0.5,12.5, facecolor=span_color, alpha=span_alpha_med)
	if i in [6]:
		axs[i].set_xlabel('month')

	
	axT = axs[i].twinx()		
	T_T = axT.boxplot(T_plot_data, whis=[10,90],sym='')
	plt.setp(T_T['boxes'], color=temp_color)
	plt.setp(T_T['whiskers'], color=temp_color,linestyle='-')
	plt.setp(T_T['caps'], color=temp_color)
	plt.setp(T_T['medians'], color=temp_color)
	axT.set_ylim(T_min,T_lim)
	axT.yaxis.grid(True, linestyle=':', which='major', color='grey', alpha=1)
	axT.set_ylabel('')
	axT.yaxis.set_visible(True)
	axT.set_xticklabels(months)
	if i in [1,3,5]:
		axT.set_ylabel('Temperature (C)', color = temp_color)
	else:
		axT.set_yticklabels([])
		
	i+=1


plt.savefig(data_dir + 'RH_and_T_for_high_O3_cities-low_RH_cities.png',  bbox_inches='tight') 

plt.show()

##

fig, axes = plt.subplots(4,2, figsize=(12, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)

axs = axes.ravel()

i=0
for city in high_RH_city_ordered_list:
	RH_plot_data = []
	T_plot_data = []
	for month in range (1,13):                                                                  
		RH_plot_data.append(cities[city][0][month])                                    
		T_plot_data.append(cities[city][1][month]) 
	
	T_RH = axs[i].boxplot(RH_plot_data, whis=[10,90],sym='')
	plt.setp(T_RH['boxes'], color=RH_color)
	plt.setp(T_RH['whiskers'], color=RH_color,linestyle='-')
	plt.setp(T_RH['caps'], color=RH_color)
	plt.setp(T_RH['medians'], color=RH_color)
	axs[i].set_ylim(0,RH_lim)
	axs[i].set_ylabel('')
	axs[i].text(label_x_pos, label_y_pos,city,transform=axs[i].transAxes)
	axs[i].yaxis.grid(True, linestyle='-', which='major', color='grey', alpha=1)
	if i in [0,1]:
		axs[i].xaxis.tick_top()
		axs[i].set_xticklabels(months)	
	if i in [0,2,4,6]:
		axs[i].set_ylabel('%RH', color = RH_color)
	else:
		axs[i].set_yticklabels([])
	if city == 'Los Angeles-Long Beach':
		axs[i].axvspan(0.5,1.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Dallas-Fort Worth':
		axs[i].axvspan(0.5,3.5, facecolor=span_color, alpha=span_alpha_25)
		axs[i].axvspan(6.5,11.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Washington-Baltimore-Arlington':
		axs[i].axvspan(2.5,4.5, facecolor=span_color, alpha=span_alpha_25)
	if city == 'Tulsa-Muskogee-Bartlesville':
		axs[i].axvspan(1.5,4.5, facecolor=span_color, alpha=span_alpha_25)
	if i in [6,7]:
		axs[i].set_xlabel('month')
	
	
	
	axT = axs[i].twinx()		
	T_T = axT.boxplot(T_plot_data, whis=[10,90],sym='')
	plt.setp(T_T['boxes'], color=temp_color)
	plt.setp(T_T['whiskers'], color=temp_color,linestyle='-')
	plt.setp(T_T['caps'], color=temp_color)
	plt.setp(T_T['medians'], color=temp_color)
	axT.set_ylim(T_min,T_lim)
	axT.yaxis.grid(True, linestyle=':', which='major', color='grey', alpha=1)
	axT.set_ylabel('')
	axT.yaxis.set_visible(True)
	axT.set_xticklabels(months)
	if i in [1,3,5,7]:
		axT.set_ylabel('Temperature (C)', color = temp_color)
	else:
		axT.set_yticklabels([])
		
	i+=1


plt.savefig(data_dir + 'RH_and_T_for_high_O3_cities-high_RH_cities.png',  bbox_inches='tight') 

plt.show()


