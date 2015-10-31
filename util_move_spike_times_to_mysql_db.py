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



######get spike times these are in local time
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times_full = pickle.load(file)
file.close()

spike_times = []
for spike in spike_times_full:
	if spike < datetime(2012,06,01):
		spike_times.append(spike + timedelta(hours = 8))# timezone correction to UTC made here (+8hrs = PST->UTC)


pprint(spike_times)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT IGNORE INTO whi_spike_times_2009to2012'
              '(spike_start_UTC,spike_end_UTC,spike_mid_time_string)'
              'VALUES (%(spike_start)s,%(spike_end)s,%(spike_mid_time)s)')


for time in spike_times:
	spike_start = time - timedelta(minutes = 1)
	spike_end   = time + timedelta(minutes = 1)

	#coinvert to UNIX ts
	start_time = calendar.timegm(spike_start.utctimetuple())
	end_time = calendar.timegm(spike_end.utctimetuple())
	mid_time = datetime.strftime(time,'%Y%m%d %H:%M:%S')

	interval_data = {
	'spike_start': start_time,
	'spike_end': end_time,
	'spike_mid_time':mid_time
	}
	
	cursor.execute(add_interval, interval_data)
	cnx.commit()


cnx.close()			