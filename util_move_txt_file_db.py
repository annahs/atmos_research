import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar

cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT IGNORE INTO whi_smps_data'
			  '(UNIX_UTC_start_time,UNIX_UTC_end_time,bin_lower_limit_nm,bin_upper_limit_nm,number_per_cc)'
			  'VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(bin_lower_limit_nm)s,%(bin_upper_limit_nm)s,%(number_per_cc)s)')

					  
timezone = timedelta(hours = -8)
list_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/SMPS/whi__smps_v1__1hrAvg_vol_140515 for sarah hanna.txt'
with open(list_file, 'r') as f:
	header = f.readline()
	header_values = header.split('\t')
	
	bin_mids = np.array(header_values[4:108])
	bin_limits = []
	i=0
	first_run = True	
	for value in bin_mids:
		if first_run == True:
			lower_value = 13.5
			first_run = False
		else:
			lower_value = float(bin_mids[i-1])
		
		mid_value = float(value)
		
		if i == 103:
			upper_value = 600
		else:
			upper_value = float(bin_mids[i+1])
		
		#lower_bin_limit = math.exp(math.log(mid_value) - (math.log(mid_value)-math.log(lower_value))/2)
		#upper_bin_limit = math.exp((math.log(upper_value)-math.log(mid_value))/2+math.log(mid_value))
		
		lower_bin_limit = mid_value - ((mid_value-lower_value)/2)
		upper_bin_limit = ((upper_value- mid_value)/2) + mid_value
		
		bin_limits.append([lower_bin_limit,upper_bin_limit])
		
		i+=1
	
	for line in f:
		
		newline = line.split('\t')
		start_time_txt = newline[0]
		start_datetime = datetime.strptime(start_time_txt, '%m/%d/%Y %H:%M') - timezone #PST to UTC
		start_UTC_timestamp = calendar.timegm(start_datetime.timetuple())
		
		end_time_txt = newline[1]
		end_datetime = datetime.strptime(end_time_txt, '%m/%d/%Y %H:%M') - timezone #PST to UTC
		end_UTC_timestamp = calendar.timegm(end_datetime.timetuple())
		
		if datetime(2012,7,1) <= start_datetime < datetime(2012,8,1):
			i = 0
			for conc in newline[3:107]:
				if conc == '':
					smps_conc = None
				else:
					smps_conc = float(conc)
				
				bin_lower = bin_limits[i][0]
				bin_upper = bin_limits[i][1]
				
				interval_data = {
				'UNIX_UTC_start_time': start_UTC_timestamp,
				'UNIX_UTC_end_time': end_UTC_timestamp,
				'bin_lower_limit_nm': bin_lower,
				'bin_upper_limit_nm': bin_upper,
				'number_per_cc': smps_conc,
				}
					
				cursor.execute(add_interval, interval_data)
				cnx.commit()
				
				i += 1
		

cnx.close()			