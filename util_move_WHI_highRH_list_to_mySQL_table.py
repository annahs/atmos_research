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


timezone = timedelta(hours=8)  #UTC = PST + 8

list_file = open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/high RH times.pkl', 'r') #inPST
rBC_data_list = pickle.load(list_file)
list_file.close()

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT IGNORE INTO whi_high_rh_times_2009to2012'
              '(high_RH_start_time,high_RH_end_time,high_RH_mid_time_string,RH)'
              'VALUES (%(high_RH_start)s,%(high_RH_end)s,%(high_RH_mid_time)s,%(RH_val)s)')

			  
i = 0
f = open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/whi__met_summer_2009-2012.txt', 'r')  #in PST
f.readline()
for line in f:
	newline = line.split()

	file_date = newline[0].strip()
	file_hour = newline[1].strip()
	try:
		RH = float(newline[3].strip())
	except:
		continue
		
	date = datetime.strptime(file_date, '%d/%m/%Y')    
	hour = datetime.strptime(file_hour, '%H:%M').time()
	date_time = datetime.combine(date, hour)
	
	
	if RH > 90:	
		if (date_time.year == 2009 and date_time.month in [6,7,8]) or (date_time.year == 2010 and date_time.month in [6,7])  or (date_time.year == 2012 and date_time.month in [4,5]):

			#get start and end and convert from PST to UTC
			start = (date_time - timedelta(minutes=30)) + timezone
			end  =  (date_time + timedelta(minutes=30)) + timezone
			
			
			#coinvert to UNIX ts
			start_time = calendar.timegm(start.utctimetuple())
			end_time = calendar.timegm(end.utctimetuple())
			
			
			interval_data = {
			'high_RH_start': start_time,
			'high_RH_end': end_time,
			'high_RH_mid_time': str(date_time+timezone),
			'RH_val': RH
			}
			
			cursor.execute(add_interval, interval_data)
			cnx.commit()

			i +=1
print i	
cnx.close()			