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

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT INTO polar6_awi_sp2_mass_concs'
              '(UNIX_UTC_ts,BC_mass_conc)'
              'VALUES (%(time)s,%(mass_conc)s)')


######get data
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/AWI_SP2/'
os.chdir(data_dir)

for file in os.listdir(data_dir):
	if file.endswith('.ict'):
		print file
		with open(file, 'r') as f:
			file_date = file[11:19]
			
			date = datetime.strptime(file_date, '%Y%m%d')

			data_start = False
			
			for line in f:
				newline = line.split(',')
				if newline[0] == 'Time_UTC' and newline[1] == ' BC_mass_conc\n' : 
					data_start = True
					continue
					
				if data_start == True:
					time_stamp = date + timedelta(seconds = float(newline[0]))
					UNIX_time_stamp = calendar.timegm(time_stamp.utctimetuple())
					
					interval_data = {
					'time': UNIX_time_stamp,
					'mass_conc': float(newline[1]), 					
					}
	
					cursor.execute(add_interval, interval_data)
					cnx.commit()


cnx.close()			