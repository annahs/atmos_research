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

night_start_time = 17
night_end_time = 15


#location:  USAF,city, lat, long, elev ,daytime RH and T, nightime RH and T, timezone
stations = {

'JINNAH INTL':							[417800,	'Karachi',	 	24.907,		067.161,	0030.5,	{},	{},	 5  ], 
'LA GUARDIA AIRPORT': 					[725030,	'New York',	 	40.779,		-073.880,	0003.4,	{},	{},	-5  ],
'JOHN F KENNEDY INTERNATIONAL A':		[744860, 	'New York',	 	40.639,		-073.762,	0003.4,	{},	{},	-5  ],
'CAIRO INTL':							[623660, 	'Cairo',	 	30.122,		031.406,	0116.4,	{},	{},	 2  ],
#'JAKARTA/OBSERVATORY':					[967450, 	'Jakarta',	 	-06.183,	106.833,	0008.0,	{},	{},	 7  ],
#'HALIM PERDANAKUSUMA INTL':			[967470, 	'Jakarta',	 	-06.267,	106.891,	0026.0,	{},	{},	 7  ],
'BEIJING - CAPITAL INTERNATIONA': 		[545110, 	'Beijing',	 	40.080,	 	116.585,	0035.4,	{},	{},	 8  ],
'LICENCIADO BENITO JUAREZ INTL':		[766793, 	'Mexico City',	19.436,		-099.072,	2229.9,	{},	{},	-6  ],
'MEXICO (CENTRAL)   D.F.':				[766800, 	'Mexico City',	19.400,	 	-099.183,	2303.0,	{},	{},	-6  ],
'MARTE':								[837790, 	'Sao Paulo',	-23.509,	-046.638,	0721.8,	{},	{},	-3  ],
'CONGONHAS':							[837800, 	'Sao Paulo',	-23.627,	-046.655,	0801.9,	{},	{},	-3  ],
'CHHATRAPATI SHIVAJI INTL':				[430030, 	'Mumbai',		19.089,		072.868,	0011.3,	{},	{},	 5.5],
'TOKYO':								[476620, 	'Tokyo',		35.683, 	139.767,	0036.0,	{},	{},	 9  ],
'TOKYO INTL':							[476710, 	'Tokyo',		35.552,		139.780,	0010.7,	{},	{},	 9  ],
'INDIRA GANDHI INTL':					[421810, 	'Delhi',		28.567, 	077.103,	0236.8,	{},	{},	 5.5],
'SAFDARJUNG':							[421820, 	'Delhi',		28.585,		077.206,	0214.9,	{},	{},	 5.5],
#'SEOUL CITY':							[471080, 	'Seoul',		37.567, 	126.967,	0087.0,	{},	{},	 9  ],
#'GIMPO':								[471100, 	'Seoul',		37.558,		126.791,	0017.7,	{},	{},	 9  ],
'PUDONG':								[583211, 	'Shanghai',		31.143, 	121.805,	0004.0,	{},	{},	 8	],
'HONGQIAO INTL':						[583670, 	'Shanghai',		31.198,		121.336,	0003.0,	{},	{},	 8	],
#'MURTALA MUHAMMED':					[652010, 	'Lagos',		06.577, 	003.321,	0041.1,	{},	{},	 1	],
#'MANILA':								[984250, 	'Manila',		14.583,		120.983,	0013.0,	{},	{},	 8	],
#'NINOY AQUINO INTL':					[984290, 	'Manila',		14.509, 	121.020,	0022.9,	{},	{},	 8	],
'OSAKA INTL':							[477710, 	'Osaka',		34.786,		135.438,	0015.2,	{},	{},	 9	],
'OSAKA':								[477720, 	'Osaka',		34.683, 	135.517,	0083.0,	{},	{},	 9  ],
'HAZRAT SHAHJALAL INTL':				[419220, 	'Dhaka',		23.843,		090.398,	0009.1,	{},	{},	 6	],
'TEJGAON':								[477720, 	'Dhaka',		23.779, 	090.383,	0007.3,	{},	{},	 6  ],
'NETAJI SUBHASH CHANDRA BOSE IN':		[428090, 	'Kolkata',		22.655,		088.447,	0004.9,	{},	{},	 5.5],
'ATATURK':								[170600, 	'Istanbul',		40.977,		028.821,	0049.7,	{},	{},	 2	],
'SABIHA GOKCEN':						[170674, 	'Istanbul',		40.899, 	029.309,	0095.1,	{},	{},	 2  ],
'MINISTRO PISTARINI':					[875760, 	'Buenos Aires',	-34.822,	-058.536,	0020.4,	{},	{},	 -3	],
'AEROPARQUE JORGE NEWBERY':				[875820, 	'Buenos Aires',	-34.559, 	-058.416,	0005.5,	{},	{},	 -3  ],
}

#city: monthly RH data, monthly temp data
cities = {
'Tokyo': 		[{},{}],
'Delhi': 		[{},{}],
'Buenos Aires':	[{},{}],
'Shanghai':		[{},{}],
'Mumbai':		[{},{}],
'Mexico City':	[{},{}],
'Beijing':		[{},{}],
'Dhaka':		[{},{}],
'Sao Paulo': 	[{},{}],
'Istanbul':		[{},{}],
'New York':		[{},{}],
'Karachi':		[{},{}],
'Osaka':		[{},{}],	
'Kolkata':		[{},{}],
'Cairo':		[{},{}],
}




data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/megacities NOAA NCDC data/'
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
					temp = float(newline[8]) + 273.15
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
						
						#get daytime data
						if datetime_local.hour >= 15 and datetime_local.hour < 17:
							if date_local in daytime_data:
								daytime_data[date_local].append([RHx,temp])
							else:
								daytime_data[date_local] = [[RHx,temp]]
								
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
	#print stn
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
	
	#print 'day_count', day_count


low_RH_city_ordered_list = ['Delhi','Mexico City','Beijing','Karachi','Cairo']		
high_RH_city_ordered_list = ['Tokyo','Seoul','Shanghai','Mumbai','Lagos','Sao Paulo','Jakarta','New York','Osaka','Manila']		
 
	                                                                                        
#Plotting                                                                                   
                                                                                            

label_x_pos = 0.55
label_y_pos = 0.1
RH_lim = 100
T_lim = 63 + 273.15
T_min = -7 + 273.15
months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
span_color = 'red'
span_alpha_25 = 0.1
span_alpha_med = 0.2
RH_color = 'black'
temp_color = 'blue'


###plotting 2


city_ordered_list = ['Tokyo','Delhi','Shanghai','Mexico City','Sao Paulo','Mumbai','Osaka','Beijing','New York','Cairo','Dhaka','Karachi', 'Buenos Aires','Kolkata','Istanbul']


high_RH_color = 'green'
low_RH_color = 'red'
span_alpha = 0.2


fig, axes = plt.subplots(5,3, figsize=(12, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)

axs = axes.ravel()

i=0
file_data = []
for city in city_ordered_list:
	RH_plot_data = []
	T_plot_data = []
	for month in range (1,13):                                                                  
		RH_plot_data.append(cities[city][0][month]) 
		RH_10 = np.percentile(cities[city][0][month],10)
		RH_25 = np.percentile(cities[city][0][month],25)
		RH_50 = np.percentile(cities[city][0][month],50)
		RH_75 = np.percentile(cities[city][0][month],75)
		RH_90 = np.percentile(cities[city][0][month],90)
		
		T_plot_data.append(cities[city][1][month]) 
		T_10 = np.percentile(cities[city][1][month],10)
		T_25 = np.percentile(cities[city][1][month],25)
		T_50 = np.percentile(cities[city][1][month],50)
		T_75 = np.percentile(cities[city][1][month],75)
		T_90 = np.percentile(cities[city][1][month],90)
		file_data.append([city,month,RH_10,RH_25,RH_50,RH_75,RH_90,T_10,T_25,T_50,T_75,T_90])

	T_RH = axs[i].boxplot(RH_plot_data, whis=[10,90],sym='')
	plt.setp(T_RH['boxes'], color=RH_color)
	plt.setp(T_RH['whiskers'], color=RH_color,linestyle='-')
	plt.setp(T_RH['caps'], color=RH_color)
	plt.setp(T_RH['medians'], color=RH_color)
	axs[i].set_ylim(0,RH_lim)
	axs[i].set_ylabel('')
	axs[i].text(label_x_pos, label_y_pos,city,transform=axs[i].transAxes)
	axs[i].yaxis.grid(True, linestyle='-', which='major', color='grey', alpha=1)
	if i in [0,1,2]:
		axs[i].xaxis.tick_top()
		axs[i].set_xticklabels(months)	
	if i in [0,3,6,9,12]:
		axs[i].set_ylabel('%RH', color = RH_color)
	else:
		axs[i].set_yticklabels([])
	if i in [13]:
		axs[i].set_xlabel('month')
	#if i == 5:
	#	axs[i].axes.get_yaxis().set_visible(False)
	#	axs[i].axes.get_xaxis().set_visible(False)
	
	if city == 'Tokyo':
		axs[i].axvspan(5.5,6.5, facecolor=high_RH_color, alpha=span_alpha)
		axs[i].axvspan(8.5,9.5, facecolor=high_RH_color, alpha=span_alpha)
	#if city == 'Dhaka':
	#	axs[i].axvspan(5.5,10.5, facecolor=high_RH_color, alpha=span_alpha)
	#if city == 'Kolkata':
	#	axs[i].axvspan(4.5,10.5, facecolor=high_RH_color, alpha=span_alpha)
	#if city == 'Delhi':
	#	axs[i].axvspan(2.5,6.5, facecolor=low_RH_color, alpha=span_alpha)
	if city == 'Shanghai':
		axs[i].axvspan(5.5,6.5, facecolor=high_RH_color, alpha=span_alpha)
		axs[i].axvspan(8.5,9.5, facecolor=high_RH_color, alpha=span_alpha)
	if city == 'Karachi':
		#axs[i].axvspan(5.5,8.5, facecolor=high_RH_color, alpha=span_alpha)
		axs[i].axvspan(0.5,1.5, facecolor=low_RH_color, alpha=span_alpha)
		axs[i].axvspan(11.5,12.5, facecolor=low_RH_color, alpha=span_alpha)
	if city == 'New York':
		print city
	if city == 'Mexico City':
		axs[i].axvspan(0.5,5.5, facecolor=low_RH_color, alpha=span_alpha)
		axs[i].axvspan(11.5,12.5, facecolor=low_RH_color, alpha=span_alpha)
	if city == 'Beijing':
		axs[i].axvspan(3.5,5.5, facecolor=low_RH_color, alpha=span_alpha)
		#axs[i].axvspan(10.5,12.5, facecolor=low_RH_color, alpha=span_alpha)
	if city == 'Sao Paulo':
		axs[i].axvspan(0.5,1.5, facecolor=high_RH_color, alpha=span_alpha)
	if city == 'Istanbul':
		#axs[i].axvspan(0.5,2.5, facecolor=high_RH_color, alpha=span_alpha)
		axs[i].axvspan(9.5,10.5, facecolor=high_RH_color, alpha=span_alpha)
	#if city == 'Mumbai':
	#	axs[i].axvspan(4.5,9.5, facecolor=high_RH_color, alpha=span_alpha)
	#if city == 'Osaka':
	#	axs[i].axvspan(6.5,7.5, facecolor=high_RH_color, alpha=span_alpha)
	if city == 'Cairo':
		axs[i].axvspan(2.5,4.5, facecolor=low_RH_color, alpha=span_alpha)

	
	
	
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
	if i in [2,5,8,11,14]:
		axT.set_ylabel('Temperature (K)', color = temp_color)
	else:
		axT.set_yticklabels([])
	#axT.axhline(290, color= 'g',)
	#axT.axhline(300, color= 'r',)

		
	i+=1
	
	
#plt.savefig(data_dir + 'RH_and_T_for_global_megacities-UNlist - temp limited.png',  bbox_inches='tight') 

#save to file
file_data

file_name = 'megacity RH and Temperature'
file = open('C:/Users/Sarah Hanna/Documents/Data/Toluene SOM/megacities NOAA NCDC data/' + file_name +'.txt', 'w')
file.write('Calculated RH and measured temperature data from NOAA NCDC database (https://gis.ncdc.noaa.gov/map/viewer/#app=cdo), values for 1500-1700 local time \n')
file.write('city \t month \t 10th_percentile_RH \t 25th_percentile_RH \t 50th_percentile_RH \t 75th_percentile_RH \t 90th_percentile_RH \t 10th_percentile_T(K) \t 25th_percentile_T(K) \t 50th_percentile_T(K) \t 75th_percentile_T(K) \t 90th_percentile_T(K) \n')
for row in file_data:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()



plt.show()



