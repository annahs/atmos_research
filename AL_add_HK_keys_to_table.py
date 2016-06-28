import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import calendar

SP2_ID = 44
start = datetime(2013,7,1)
end =   datetime(2013,8,1)
timestep = 1 #hours
UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute('SELECT id, UNIX_UTC_ts FROM alert_hk_data WHERE UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s',(UNIX_start,UNIX_end))
data = cursor.fetchall()

print 'starting loop'

LOG_EVERY_N = 10
i=0
for data_point in data:
	id = data_point[0]
	start_time = data_point[1]
	end_time = start_time + 60
	
	cursor.execute(('UPDATE alert_mass_number_data_2013 SET HK_id = %s WHERE UNIX_UTC_ts_int_end >= %s AND UNIX_UTC_ts_int_end < %s'),(id,start_time,end_time))	
	cnx.commit()
	
	i+=1
	if (i % LOG_EVERY_N) == 0:
		print 'record: ', i
		
cnx.close()
