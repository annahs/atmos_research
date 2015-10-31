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



#list_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/clustering/CLUSLIST_10' #in UTC
#list_file = 'C:/HYSPLIT_argh/WHI_1h_10-day_working/odd_hours/CLUSLIST_5' #in UTC
list_file = 'C:/HYSPLIT_argh/WHI_1h_10-day_working/even_hours/CLUSLIST_4' #in UTC
cluster_half_range = 1
		
		

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT IGNORE INTO whi_ft_cluster_times_2009to2012_2hr_resolution_evenhrs'
              '(cluster_start_time,cluster_end_time,cluster_number,cluster_mid_time_string)'
              'VALUES (%(cluster_start)s,%(cluster_end)s,%(cluster)s,%(traj_time_str)s)')

			  
i = 0

with open(list_file, 'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5]))
		traj_start = traj_time - timedelta(hours=cluster_half_range)
		traj_end = traj_time + timedelta(hours=cluster_half_range)

		#coinvert to UNIX ts
		start_time = calendar.timegm(traj_start.utctimetuple())
		end_time = calendar.timegm(traj_end.utctimetuple())
		

		interval_data = {
		'cluster_start': start_time,
		'cluster_end': end_time,
		'cluster':cluster_no,
		'traj_time_str':str(traj_time)
		}
		
		cursor.execute(add_interval, interval_data)
		cnx.commit()

		i +=1

print i
cnx.close()			