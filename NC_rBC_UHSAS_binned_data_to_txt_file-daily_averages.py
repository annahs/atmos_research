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



time_interval = 60 #in sec

flight_times = {
##'science 1'  : [datetime(2015,4,5,9,43),  datetime(2015,4,5,13,49) ,''],							   #no UHSAS data	
##'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ,'UHSAS_Polar6_20150406_R0_V1.ict'],  #no flight data 
##'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ,'UHSAS_Polar6_20150406_R0_V2.ict'],  #no flight data
##'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ,'UHSAS_Polar6_20150407_R0_V1.ict'],  #no flight data
'science 3'  : [datetime(2015,4,8,13,51), datetime(2015,4,8,16,44) ,'UHSAS_Polar6_20150408_R0_V1.ict'],  
'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,22,44) ,'UHSAS_Polar6_20150408_R0_V2.ict'],
'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,48) ,'UHSAS_Polar6_20150409_R0_V1.ict'],
'ferry 3'    : [datetime(2015,4,10,14,28),datetime(2015,4,10,16,44),'UHSAS_Polar6_20150410_R0_V1.ict'],
'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,17),'UHSAS_Polar6_20150411_R0_V1.ict'],
'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,53),'UHSAS_Polar6_20150413_R0_V1.ict'],
'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,50),'UHSAS_Polar6_20150420_R0_V1.ict'],
'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,37) ,'UHSAS_Polar6_20150420_R0_V2.ict'],
'science 10' : [datetime(2015,4,21,16,7),datetime(2015,4,21,21,25),'UHSAS_Polar6_20150421_R0_V1.ict'],  ###
##'test'		  : [datetime(2015,4,9,13,50),datetime(2015,4,9,14,10),'UHSAS_Polar6_20150409_R0_V1.ict'],  ###
}



for flight_name, info in flight_times.iteritems():
	new_file = True
	start_time = info[0]
	end_time = info[1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	print start_time, UNIX_start_time
	print end_time, UNIX_end_time

	#database connection
	cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
	cursor = cnx.cursor()

	os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/1Hz-ict-R0/')
	UHSAS_file = info[2]

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
		bin_list = []
		i=0
		for LL_limit in bin_LL_line:
			bin_list.append([float(LL_limit),float(bin_UL_line[i])])
			i+=1
			
	
	file_data = []	
	for bin in bin_list:
		print bin
		bin_LL =  bin[0]
		bin_UL =  bin[1]
		
		
		cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <=%s and binned_property = %s'),(UNIX_start_time, UNIX_end_time, bin_LL,bin_UL,'UHSAS_#'))
		UHSAS_number = cursor.fetchall()
		UHSAS_number_mean = UHSAS_number[0][0] 
		if UHSAS_number_mean == None:
			UHSAS_number_mean_norm = np.nan
		else:
			UHSAS_number_mean_norm = UHSAS_number_mean/(math.log((bin_UL))-math.log(bin_LL))
		
		
		if bin_LL >= 130 and bin_UL <=450:
			cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time, bin_LL,bin_UL,'SP2_coated_#'))
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
			cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time, bin_LL,bin_UL,'mean_coating_th'))
			coat_th = cursor.fetchall()
			coat_th_mean = coat_th[0][0]
			if coat_th_mean == None:
				coat_th_mean = np.nan
		else:
			coat_th_mean = np.nan

			
		if bin_LL >= 70 and bin_UL <220:
			cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'SP2_core_#'))
			SP2_core_number = cursor.fetchall()
			SP2_core_number_mean = SP2_core_number[0][0] 
			if SP2_core_number_mean == None:
				SP2_core_number_mean_norm = np.nan
			else:
				SP2_core_number_mean_norm = SP2_core_number_mean/(math.log((bin_UL))-math.log(bin_LL))
		else:
			SP2_core_number_mean_norm = np.nan

		file_data.append([bin_LL,bin_UL,UHSAS_number_mean_norm,SP2_coated_number_mean_norm,coat_th_mean,SP2_core_number_mean_norm])

	
	cnx.close()

	
	#os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/')
	#file = open(flight_name + ' - UHSAS and SP2 data binned data - by flight.txt', 'w')
	#if new_file == True:
	#	file.truncate(0)
	#	file.write('UHSAS and SP2 data from Netcare POLAR6 flights - Spring 2015\n')
	#	file.write('bin_lower_limit(nm),bin_upper_limit(nm), UHSAS_number_concentration(dN/dlogD #/sccm),SP2_number_concentration_using_core+coating_diamater(dN/dlogD #/sccm),SP2_mean_coating_thickness_for_rBC_cores_in_this_size_bin(nm),SP2_number_concentration_using_core_only_diamater(dN/dlogD #/sccm)\n')
	#for row in file_data:
	#	line = '\t'.join(str(x) for x in row)
	#	file.write(line + '\n')
	#file.close()

	
	
	#plot
	
	bin_LL = [row[0] for row in file_data]
	bin_UL = [row[1] for row in file_data]
	UHSAS_number = [row[2] for row in file_data]
	SP2_coated_number = [row[3] for row in file_data]
	coat_th_mean = [row[4] for row in file_data]
	SP2_core_number = [row[5] for row in file_data]
	
	
	fig = plt.figure(figsize=(10,12))
    
	ax1 = plt.subplot(2, 1, 1)
	ax1.scatter(bin_LL,UHSAS_number, label = 'UHSAS', color = 'b')
	ax1.scatter(bin_LL,SP2_coated_number, label = 'rBC core + coating', color = 'g')
	ax1.scatter(bin_LL,SP2_core_number, label = 'rBC core only', color = 'r')
	ax1.set_ylabel('dN/dlogD #/sccm')
	ax1.set_xlabel('VED (nm)')
	ax1.set_yscale('log')
	ax1.set_xscale('log')
	ax1.set_xlim(80,900)
	ax1.set_ylim(0.5,500)
	plt.xticks(np.arange(80, 900, 10))
	plt.legend()
	
	ax2 = plt.subplot(2, 1, 2)
	ax2.plot(bin_LL,coat_th_mean, label = 'coat_th')
	ax2.set_ylabel('coating thickness (nm)')
	ax2.set_xlabel('rBC core VED (nm)')
	ax2.set_xlim(80,900)
	ax2.set_xscale('log')
	#ax1.set_ylim(0,6000)
	
	plt.show()
