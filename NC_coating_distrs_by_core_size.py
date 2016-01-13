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


flight = 'science 10'

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
'science 10' : [datetime(2015,4,21,17,8),datetime(2015,4,21,18,18),'UHSAS_Polar6_20150421_R0_V1.ict'],  ###
}

start_time = flight_times[flight][0]
end_time = flight_times[flight][1]
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())
print start_time, UNIX_start_time
print end_time, UNIX_end_time


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/1Hz-ict-R0/')
UHSAS_file = flight_times[flight][2]

no_prev_particle = False

with open(UHSAS_file, 'r') as f:
	print UHSAS_file
	file_date = UHSAS_file[13:21]
	date = datetime.strptime(file_date, '%Y%m%d')

	##get bin limits
	i=0
	while i < 9:  #indep_var_number is always on line 10
		f.readline()
		i+=1
	indep_var_number = float(f.readline()) 
	i=0
	while i < (indep_var_number + 11): #check that 11 is right for each set of files
		f.readline()
		i+=1
	bin_LL_line = (f.readline()).split() 
	f.readline() #skip this line 
	bin_UL_line = (f.readline()).split() 
	
	
	##create bins dict
	bin_dict = {}
	i=0
	for LL_limit in bin_LL_line:
		bin_dict[i] = [float(LL_limit),float(bin_UL_line[i])]
		i+=1
		

	
plot_data = []	
for bin in bin_dict:
	bin_LL =  bin_dict[bin][0]
	bin_UL =  bin_dict[bin][1]
	print bin_LL, bin_UL
	
	if bin_UL < 130:
		continue
	bin_MP = bin_LL + (bin_UL-bin_LL)/2
		
	cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <=%s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'UHSAS_#'))
	UHSAS_number = cursor.fetchall()
	UHSAS_number_mean = UHSAS_number[0][0] 
	if UHSAS_number_mean == None:
		print UHSAS_number_mean
		UHSAS_number_mean_norm = np.nan
	else:
		UHSAS_number_mean_norm = UHSAS_number_mean/(math.log((bin_UL))-math.log(bin_LL))
	
			
	cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'SP2_core_#'))
	SP2_core_number = cursor.fetchall()
	SP2_core_number_mean = SP2_core_number[0][0] 
	if SP2_core_number_mean == None:
		print SP2_core_number_mean
		SP2_core_number_mean_norm = np.nan
	else:
		SP2_core_number_mean_norm = SP2_core_number_mean/(math.log((bin_UL))-math.log(bin_LL))

	if bin_LL >= 70:
		cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'SP2_coated_#'))
		SP2_coated_number = cursor.fetchall()
		SP2_coated_number_mean = SP2_coated_number[0][0] 
		if SP2_coated_number_mean == None:
			SP2_coated_number_mean_norm = np.nan
		else:
			SP2_coated_number_mean_norm = SP2_coated_number_mean/(math.log((bin_UL))-math.log(bin_LL))
	else:
		SP2_coated_number_mean = np.nan
		SP2_coated_number_mean_norm = np.nan
	
	
	if bin_LL >= 130:
		cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'SP2_coated_#'))
		SP2_coated_number_130 = cursor.fetchall()
		SP2_coated_number_mean_130 = SP2_coated_number_130[0][0] 
		if SP2_coated_number_mean_130 == None:
			SP2_coated_number_mean_norm_130 = np.nan
		else:
			SP2_coated_number_mean_norm_130 = SP2_coated_number_mean_130/(math.log((bin_UL))-math.log(bin_LL))
	else:
		SP2_coated_number_mean_130 = np.nan
		SP2_coated_number_mean_norm_130 = np.nan
	
	cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'mean_core_dia'))
	core_dia = cursor.fetchall()
	core_dia_mean = core_dia[0][0] 
	if core_dia_mean == None:
		core_dia_mean_norm = np.nan
	else:
		core_dia_mean_norm = core_dia_mean/(math.log((bin_UL))-math.log(bin_LL))
    
	if bin_LL >= 70:
		cursor.execute(('SELECT value FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'mean_coating_th'))
		coat_ths = cursor.fetchall()
		data = []
		for coat in coat_ths:
			th = coat[0]
			data.append(th)
		coat_th_mean = np.mean(data)
		print 'mean', coat_th_mean
		print 'median', np.median(data)
		fig = plt.figure()
		ax1 = plt.subplot(1, 1, 1)
		n, bins, patches = ax1.hist(data, 50, normed=1, facecolor='green', alpha=0.75)
		plt.show()

		if coat_th_mean == None:
			coat_th_mean_norm = np.nan
		else:
			coat_th_mean_norm = coat_th_mean/(math.log((bin_UL))-math.log(bin_LL))
	else:
		coat_th_mean = np.nan
		coat_th_mean_norm = np.nan
	
	
	
	plot_data.append([bin_MP,UHSAS_number_mean,UHSAS_number_mean_norm,SP2_coated_number_mean,SP2_coated_number_mean_norm,SP2_core_number_mean,SP2_core_number_mean_norm,core_dia_mean,core_dia_mean_norm,coat_th_mean,coat_th_mean_norm,SP2_coated_number_mean_norm_130])
	
cnx.close()
	
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/')
file = open(flight + ' UHSAS and SP2 data comparison - 70nm and up cores.txt', 'w')
file.write('particle_event_start_time(UNIXtime UTC)'+ '\t' + 'particle_event_end_time(UNIXtime UTC)'+ '\t' + 'incand_flag'+ '\t' + 'incand_sat_flag'+ '\t' + 'BC_mass(fg)' + '\t' + 'incand_height(au)' + '\t' +'NB_incand_height(au)' + '\n')
for row in plot_data:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()
			
	

##plotting

bin_midpoint   	    = [row[0] for row in plot_data]
UHSAS_num      		= [row[1] for row in plot_data]
UHSAS_num_norm 		= [row[2] for row in plot_data]
SP2_coated_num 		= [row[3] for row in plot_data]
SP2_coated_num_norm = [row[4] for row in plot_data]
SP2_core_num  		= [row[5] for row in plot_data]
SP2_core_num_norm   = [row[6] for row in plot_data]
core_dia  		    = [row[7] for row in plot_data]
core_dia_norm		= [row[8] for row in plot_data]
coat_th      	    = [row[9] for row in plot_data]
coat_th_norm  	    = [row[10] for row in plot_data]
SP2_coated_130 	    = [row[11] for row in plot_data]


fig = plt.figure(figsize=(10,12))


ax1 = plt.subplot(2, 1, 1)
ax1.plot(bin_midpoint,UHSAS_num_norm, label = 'UHSAS')
ax1.plot(bin_midpoint,SP2_coated_num_norm, label = 'rBC core + coating')
ax1.plot(bin_midpoint,SP2_core_num_norm, label = 'rBC core only')
ax1.plot(bin_midpoint,SP2_coated_130, label = 'rBC core only')
ax1.set_ylabel('dN/dlogD #/sccm')
ax1.set_xlabel('VED (nm)')
ax1.set_yscale('log')
ax1.set_xscale('log')
ax1.set_xlim(80,900)
ax1.set_ylim(0.5,500)
plt.xticks(np.arange(80, 900, 10))
plt.legend()

ax2 = plt.subplot(2, 1, 2)
ax2.plot(bin_midpoint,coat_th, label = 'coat_th')
ax2.set_ylabel('coating thickness (nm)')
ax2.set_xlabel('rBC core VED (nm)')
ax2.set_xlim(80,900)
ax2.set_xscale('log')
#ax1.set_ylim(0,6000)




plt.show()


	
	