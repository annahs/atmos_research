import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates
from mpl_toolkits.basemap import Basemap
import calendar
from scipy.optimize import curve_fit


flight = 'test'

flight_times = {
#'science 1'  : [datetime(2015,4,5,9,0),  datetime(2015,4,5,14,0) ,''],	
#'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ,'UHSAS_Polar6_20150406_R0_V1.ict'],  
#'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ,'UHSAS_Polar6_20150406_R0_V2.ict'],
#'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ,'UHSAS_Polar6_20150407_R0_V1.ict'],
#'science 3'  : [datetime(2015,4,8,13,0), datetime(2015,4,8,17,0) ,'UHSAS_Polar6_20150408_R0_V1.ict'],  
#'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0) ,'UHSAS_Polar6_20150408_R0_V2.ict'],
#'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0) ,'UHSAS_Polar6_20150409_R0_V1.ict'],
#'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),'UHSAS_Polar6_20150410_R0_V1.ict'],
#'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),'UHSAS_Polar6_20150411_R0_V1.ict'],
#'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),'UHSAS_Polar6_20150413_R0_V1.ict'],
#'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),'UHSAS_Polar6_20150420_R0_V1.ict'],
#'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0) ,'UHSAS_Polar6_20150420_R0_V2.ict'],
#'science 10' : [datetime(2015,4,21,16,8),datetime(2015,4,21,16,18),'UHSAS_Polar6_20150421_R0_V1.ict'],  ###
'test'    : [datetime(2015,4,5,16,0),datetime(2015,4,21,18,0),'UHSAS_Polar6_20150421_R0_V1.ict'],  ###
}

scat_lim_70 = 44
scat_lim_80 = 55
scat_lim_90 = 70
scat_lim_100 = 92
scat_lim_110 = 120
scat_lim_120 = 156
scat_lim_130 = 200


lims = [
scat_lim_70,
scat_lim_80 ,
scat_lim_90 ,
scat_lim_100,
scat_lim_110,
scat_lim_120,
scat_lim_130,
#200,200,200,200,200,200,200,200,200,
30,30,30,30,30,30,30,30,30,
]

lims = [
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
40,
]

start_time = flight_times[flight][0]
end_time = flight_times[flight][1]
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())
print start_time, UNIX_start_time
print end_time, UNIX_end_time


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()



bin_list = []
j=0
i = 70
while i < 220:
	temp = [i, i+10,lims[j]]
	bin_list.append(temp)
	i+=10
	j+=1
	

	
plot_data = []	
for bin in bin_list:
	bin_LL =  bin[0]
	mass_LL = ((bin_LL/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
	bin_UL =  bin[1]
	mass_UL = ((bin_UL/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
	bin_MP = ((bin_UL-bin_LL)/2) + bin_LL
	scat_lim = bin[2]
	print bin_LL, mass_LL,bin_UL,mass_UL,scat_lim
		
	
	cursor.execute(('SELECT LF_scat_amp FROM polar6_coating_2015 WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND rBC_mass_fg >= %s and rBC_mass_fg <%s and actual_scat_amp > %s LIMIT 10000'),(UNIX_start_time, UNIX_end_time,mass_LL,mass_UL,scat_lim))
	LF_data = cursor.fetchall()
	successful_fits = 0
	for row in LF_data:
		LF_scat_amp = row[0]
		if LF_scat_amp > 0:
			successful_fits +=1
	fraction_success = successful_fits*1.0/len(LF_data)
	plot_data.append([bin_MP,fraction_success])
	print len(LF_data)
	
##plotting

bin_midpoint   	    = [row[0] for row in plot_data]
fraction_successful	= [row[1] for row in plot_data]


fig = plt.figure()


ax1 = plt.subplot(1, 1, 1)
ax1.scatter(bin_midpoint,fraction_successful)
ax1.set_ylabel('fraction successful LEO fits (total particle dia >=130nm)')
ax1.set_xlabel('core VED (nm)')
#ax1.set_yscale('log')
#ax1.set_xscale('log')
ax1.set_xlim(60,240)
ax1.set_ylim(0,1.1)
#plt.xticks(np.arange(80, 900, 10))
#plt.legend()


plt.show()


	
	