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
from coating_info_from_raw_signal import CoatingData


flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200]	,	
##'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
##'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
##'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014]    ,
#'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014]    ,
#'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014]   ,
#'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0]   ,
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
#'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5] ,
#'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1] ,
#'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1],
#'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617] ,
#'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55],
#'tscience 10' : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617] ,
#'hscience 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,18,0),-131, 69.55],
##'gscience 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,18,0),-131, 69.55],
}

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

binned_data = []
i = 70  
while i < 220:
	binned_data.append(i)
	i+=10

plot_data = []
for flight in flight_times:
	print flight
	
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	
	for bin in binned_data:
		bin_LL = bin
		bin_UL = bin +10
		print bin_LL, ' to ', bin_UL
		
		cursor.execute(('SELECT (POW(rBC_mass_fg,(1/3.0))*101.994391398), coat_thickness_nm FROM polar6_coating_2015 where (POW(rBC_mass_fg,(1/3.0))*101.994391398) >= %s and (POW(rBC_mass_fg,(1/3.0))*101.994391398) < %s and particle_type = %s and instrument = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and coat_thickness_nm IS NOT NULL'),(bin_LL,bin_UL,'incand','UBCSP2',UNIX_start_time,UNIX_end_time))
		coating_data = cursor.fetchall()
		
		#for row in coating_data:
		#	if coat_thickness_nm == None:
		#		coat_thickness_nm = 0
		
		median_core_VED = np.median([row[0] for row in coating_data])
		median_coat_th =  np.median([row[1] for row in coating_data])
		err25_coat_th = median_coat_th-np.percentile([row[1] for row in coating_data],25)
		err75_coat_th = np.percentile([row[1] for row in coating_data],75)-median_coat_th
		
		core_vol = (4/3)*math.pi*((median_core_VED/2)**3)
		particle_vol = (4/3)*math.pi*(((median_core_VED/2)+2*median_coat_th)**3)
		med_coat_volfrac = (particle_vol-core_vol)/particle_vol*1.0
		err25_coat_volfrac = 0#((4/3)*math.pi*(((median_core_VED/2)+2*np.percentile([row[1] for row in coating_data],25))**3)-core_vol)/(4/3)*math.pi*(((median_core_VED/2)+2*np.percentile([row[1] for row in coating_data],25))**3)
		err75_coat_volfrac = 0#((4/3)*math.pi*(((median_core_VED/2)+2*np.percentile([row[1] for row in coating_data],75))**3)-core_vol)/(4/3)*math.pi*(((median_core_VED/2)+2*np.percentile([row[1] for row in coating_data],75))**3)

		
		
		plot_data.append([median_core_VED,median_coat_th,err25_coat_th,err75_coat_th,med_coat_volfrac,err25_coat_volfrac,err75_coat_volfrac])
		

core = [row[0] for row in plot_data]
coat_th = [row[1] for row in plot_data]
coat_th_minerr = [row[2] for row in plot_data]
coat_th_maxerr = [row[3] for row in plot_data]
med_coat_volfrac = [row[4] for row in plot_data]
med_coat_minerr = [row[5] for row in plot_data]
med_coat_maxerr = [row[6] for row in plot_data]



fig = plt.figure()

ax1  = plt.subplot2grid((2,1), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,1), (1,0), colspan=1)					

ax1.errorbar(core,coat_th,yerr = [coat_th_minerr,coat_th_maxerr],fmt='o',linestyle='-')
ax1.set_ylabel('coat thickness (nm)')
ax1.set_xlabel('core VED (nm)')
ax1.set_xlim(70,220)
ax1.set_ylim(0,80)

ax2.errorbar(core,med_coat_volfrac,yerr = [med_coat_minerr,med_coat_maxerr],fmt='o',linestyle='-', color = 'grey')
ax2.set_xlabel('core VED (nm)')
ax2.set_ylabel('coating volume fraction')
ax2.set_xlim(70,220)
ax2.set_ylim(0,1)

#ax3.errorbar(mass_med,altitudes,xerr = [mass_25,mass_75],fmt='o',linestyle='-', color = 'green')
#ax3.set_xlabel('total mass conc (ng/m3 - STP)')
#ax3.set_ylabel('altitude (m)')
#ax3.set_xlim(0,180)
#ax3.set_ylim(0,6000)


fig.suptitle(flight, fontsize=20)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

#plt.savefig('.png', bbox_inches='tight') 

plt.show()

