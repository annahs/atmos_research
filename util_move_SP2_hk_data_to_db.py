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
add_interval = ('INSERT INTO polar6_hk_data_2015'
              '(UNIX_UTC_ts,sample_flow,yag_power,sheath_flow,yag_xtal_temp)'
              'VALUES (%(time)s,%(sample_flow)s,%(yag_power)s,%(sheath_flow)s,%(yag_xtal_temp)s)')


######get data
data_dir = 'D:/2015/NETCARE_UBC_SP2/flight data/20150421/'
os.chdir(data_dir)

for file in os.listdir(data_dir):
	if file.endswith('.hk'):
		print file
		with open(file, 'r') as f:

			f.readline()
			
			for line in f:
				newline = line.split()
				
				labview_time_stamp = float(newline[1])
				UNIX_time_stamp = labview_time_stamp-2082844800 #UNIX epoch is 1 Jan 1970, Labview epoch is 1 Jan 1904 therefore LVts_to_UNIXts = -2082844800 
				
				date_time = datetime.utcfromtimestamp(UNIX_time_stamp)
				
				
				interval_data = {
				'time': UNIX_time_stamp,
				'sample_flow': float(newline[3]), 
				'yag_power':  float(newline[8]),
				'sheath_flow':float(newline[5]),
				'yag_xtal_temp':float(newline[9]),
				}

				cursor.execute(add_interval, interval_data)
				cnx.commit()


cnx.close()			