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
#'science 1'  : [datetime(2015,4,5,9,43),  datetime(2015,4,5,13,49) ,''],							   #no UHSAS data	
#'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ,'UHSAS_Polar6_20150406_R0_V1.ict'],  #no flight data 
#'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ,'UHSAS_Polar6_20150406_R0_V2.ict'],  #no flight data
#'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ,'UHSAS_Polar6_20150407_R0_V1.ict'],  #no flight data
'science 3'  : [datetime(2015,4,8,13,51), datetime(2015,4,8,16,44) ,'UHSAS_Polar6_20150408_R0_V1.ict'],  
'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,22,44) ,'UHSAS_Polar6_20150408_R0_V2.ict'],
'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,48) ,'UHSAS_Polar6_20150409_R0_V1.ict'],
'ferry 3'    : [datetime(2015,4,10,14,28),datetime(2015,4,10,16,44),'UHSAS_Polar6_20150410_R0_V1.ict'],
'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,17),'UHSAS_Polar6_20150411_R0_V1.ict'],
'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,53),'UHSAS_Polar6_20150413_R0_V1.ict'],
'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,50),'UHSAS_Polar6_20150420_R0_V1.ict'],
'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,37) ,'UHSAS_Polar6_20150420_R0_V2.ict'],
'science 10' : [datetime(2015,4,21,16,7),datetime(2015,4,21,21,25),'UHSAS_Polar6_20150421_R0_V1.ict'],  ###
}



for flight_name, info in flight_times.iteritems():

	start_time = info[0]
	end_time = info[1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	print start_time, UNIX_start_time
	print end_time, UNIX_end_time
	test = []

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
			
	first_file = True
	file_data = []	
	current_ts = UNIX_start_time
	while (current_ts+time_interval) <= UNIX_end_time:
		UHSAS_line = []
		core_and_coating_line = []
		mean_coating_line = []
		lines= [UHSAS_line,core_and_coating_line,mean_coating_line]
		for line in lines:
			line.append(current_ts)
			line.append((current_ts+time_interval))
		
		for bin in bin_list:
			bin_LL =  bin[0]
			bin_UL =  bin[1]

			
			cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <=%s and binned_property = %s'),(current_ts, (current_ts+time_interval),bin_LL,bin_UL,'UHSAS_#'))
			UHSAS_number = cursor.fetchall()
			UHSAS_number_mean = UHSAS_number[0][0] 
			if UHSAS_number_mean == None:
				UHSAS_number_mean_norm = np.nan
			else:
				UHSAS_number_mean_norm = UHSAS_number_mean/(math.log((bin_UL))-math.log(bin_LL))
			
		
			if bin_LL >= 130:
				cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(current_ts, (current_ts+time_interval),bin_LL,bin_UL,'SP2_coated_#'))
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
				cursor.execute(('SELECT avg(value) FROM polar6_uhsas_rbc_binned_data WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s AND bin_LL >= %s and bin_UL <= %s and binned_property = %s'),(current_ts, (current_ts+time_interval),bin_LL,bin_UL,'mean_coating_th'))
				coat_th = cursor.fetchall()
				coat_th_mean = coat_th[0][0]
				if coat_th_mean == None:
					coat_th_mean = np.nan
			else:
				coat_th_mean = np.nan
			
			###
			if bin_LL >=197 and  bin_LL < 204:
				test.append(coat_th_mean)
			####
			
			UHSAS_line.append(UHSAS_number_mean_norm)
			core_and_coating_line.append(SP2_coated_number_mean_norm)
			mean_coating_line.append(coat_th_mean)
			
			
		file_data.append(UHSAS_line)
		file_data.append(core_and_coating_line)
		file_data.append(mean_coating_line)
		current_ts += time_interval
		
	cnx.close()
		
	#fig = plt.figure(figsize=(10,12))
    #
	#plt.hist(test, bins=40, range = (0,100),normed=True)
    #
	#plt.show()
		
	
	
	os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/')
	file = open(flight_name + ' - UHSAS and SP2 data binned data.txt', 'w')
	if first_file == True:
		file.truncate(0)
		file.write('UHSAS and SP2 data from Netcare POLAR6 flights - Spring 2015\n')
		file.write('Time is given as UNIX timestamps in UTC\n')
		file.write('The first line with each timestamp is the UHSAS number concentration - dN/dlogD #/sccm\n')
		file.write('The second line with each timestamp is the SP2 number concentration using core+coating diamater - dN/dlogD #/sccm\n')
		file.write('The third line with each timestamp is the SP2 mean coating thickness for rBC cores in that size bin - nm\n')
		bin_LLs = [row[0] for row in bin_list]
		bin_LLs_string = '\t'.join(str(x) for x in bin_LLs)
		bin_ULs = [row[1] for row in bin_list]
		bin_ULs_string = '\t'.join(str(x) for x in bin_ULs)
		file.write('lower bin limits\n')
		file.write(bin_LLs_string+'\n')
		file.write('upper bin limits\n')
		file.write(bin_ULs_string+'\n')
		header_line = 'interval_start_time,interval_end_time'
		for value in range(1,101):
			bin_string = ',bin_'+str(value)
			header_line = header_line + bin_string
		file.write(header_line+'\n')
		first_file = False
	for row in file_data:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()

