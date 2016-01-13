import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT id, UNIX_UTC_ts from polar6_flight_track_details'))
flight_track_data = cursor.fetchall()

print 'starting loop'

LOG_EVERY_N = 10000
i=0
for flight_data_point in flight_track_data:
	flight_point_id = flight_data_point[0]
	timestamp = flight_data_point[1]
	start_time = timestamp - 0.5
	end_time = timestamp + 0.5
	
	
	cursor.execute(('UPDATE polar6_coating_2015 SET flight_track_data_id = %s WHERE UNIX_UTC_ts >= %s AND UNIX_UTC_ts < %s'),(flight_point_id,start_time,end_time))	
	cnx.commit()
	
	i+=1
	if (i % LOG_EVERY_N) == 0:
		print 'record: ', i
		
cnx.close()