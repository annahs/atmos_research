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

cursor.execute('SELECT id, UNIX_UTC_ts FROM polar6_fssp_cloud_data')
data = cursor.fetchall()

print 'starting loop'

LOG_EVERY_N = 100
i=0
for data_point in data:
	id = data_point[0]
	flight_deets_time = data_point[1]

	cursor.execute(('UPDATE polar6_uhsas_total_number SET fssp_id = %s WHERE UNIX_UTC_ts = %s'),(id,flight_deets_time))	
	cnx.commit()
	
	i+=1
	if (i % LOG_EVERY_N) == 0:
		print 'record: ', i
		
cnx.close()
