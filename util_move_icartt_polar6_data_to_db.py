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
add_interval = ('INSERT INTO polar6_flight_track_details'
              '(UNIX_UTC_ts,temperature_C,RH,BP_Pa,WSN,WSE,lat,lon,alt,SProbN,SProbE,SProbD,roll,pitch,heading,TAS,WSD,SideslipAngle,AOA,SideslipDiff,SysStatFlag,WS,WSW,WD)'
              'VALUES (%(time)s,%(temperature_C)s,%(RH)s,%(BP_Pa)s,%(WSN)s,%(WSE)s,%(lat)s,%(lon)s,%(alt)s,%(SProbN)s,%(SProbE)s,%(SProbD)s,%(roll)s,%(pitch)s,%(heading)s,%(TAS)s,%(WSD)s,%(SideslipAngle)s,%(AOA)s,%(SideslipDiff)s,%(SysStatFlag)s,%(WS)s,%(WSW)s,%(WD)s)')


######get data
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/icartt/'
os.chdir(data_dir)

for file in os.listdir(data_dir):
	if file.endswith('.ict'):
		print file
		with open(file, 'r') as f:
			file_date = file[21:29]
			date = datetime.strptime(file_date, '%Y%m%d')

			data_start = False
			
			for line in f:
				newline = line.split(',')
				
				if newline[0] == 'TimeWave' and newline[1] == 'Time_Hr' :
					data_start = True			
					continue
					
				if data_start == True:
					time_stamp = date + timedelta(seconds = float(newline[0]))
					UNIX_time_stamp = calendar.timegm(time_stamp.utctimetuple())
					
					interval_data = {
					'time': UNIX_time_stamp,
					'temperature_C': float(newline[2]), 
					'RH':  float(newline[3]),
					'BP_Pa':float(newline[4]),
					'WSN':float(newline[5]),
					'WSE':float(newline[6]),
					'lat':float(newline[7]),
					'lon':float(newline[8]),
					'alt':float(newline[9]),
					'SProbN': float(newline[10]), 
					'SProbE':float(newline[11]),
					'SProbD':float(newline[12]),  
					'roll':float(newline[13]),
					'pitch':  float(newline[14]),
					'heading': float(newline[15]), 
					'TAS':  float(newline[16]),
					'WSD': float(newline[17]), 
					'SideslipAngle': float(newline[18]), 
					'AOA': float(newline[19]), 
					'SideslipDiff':  float(newline[20]),
					'SysStatFlag':float(newline[21]),  
					'WS':  float(newline[22]),
					'WSW':  float(newline[23]),
					'WD': float(newline[24]),
					}
	
					cursor.execute(add_interval, interval_data)
					cnx.commit()


cnx.close()			