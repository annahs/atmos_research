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
add_interval = ('INSERT IGNORE INTO whi_ft_cluster_times_2012_with_precip'
              '(cluster_start_time,cluster_end_time,cluster_number,cluster_mid_time_string,precip_day1_back,precip_day2_back,precip_day3_back,precip_day4_back,precip_day5_back,precip_day6_back,precip_day7_back,precip_day8_back,precip_day9_back,precip_day10_back)'
              'VALUES (%(cluster_start_time)s,%(cluster_end_time)s,%(cluster_number)s,%(cluster_mid_time_string)s,%(precip_day1_back)s,%(precip_day2_back)s,%(precip_day3_back)s,%(precip_day4_back)s,%(precip_day5_back)s,%(precip_day6_back)s,%(precip_day7_back)s,%(precip_day8_back)s,%(precip_day9_back)s,%(precip_day10_back)s)')

cluster_half_range = 1

CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip'

with open(CLUSLIST_file,'r') as f:
	
	for line in f:
		newline = line.split()
		cluster = int(newline[0])
		file = newline[7]
		
		
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5]))
		traj_start = traj_time - timedelta(hours=cluster_half_range)
		traj_end = traj_time + timedelta(hours=cluster_half_range)

		#coinvert to UNIX ts
		start_time = calendar.timegm(traj_start.utctimetuple())
		end_time = calendar.timegm(traj_end.utctimetuple())
		mid_time = datetime.strftime(traj_time,'%Y%m%d %H:%M:%S')		

		data_start = False
		precip_amt = 0
		precip_list = []
		
		tdump_file = open(file, 'r')
		for line in tdump_file:
			newline = line.split()

			if data_start == True:
				hours_back = float(newline[8])
				height = float(newline[11])
				precip = float(newline[13])
				
				precip_amt += precip
				
				if hours_back % 24 == 0 and hours_back != 0 :
					precip_list.append(precip_amt)
					precip_amt = 0

			if newline[1] == 'PRESSURE':
				data_start = True
			
		tdump_file.close() 
		

		interval_data = {
		'cluster_start_time': start_time,
		'cluster_end_time': end_time,
		'cluster_number': cluster,
		'cluster_mid_time_string': mid_time,
		'precip_day1_back' :precip_list[0],
		'precip_day2_back' :precip_list[1],
		'precip_day3_back' :precip_list[2],
		'precip_day4_back' :precip_list[3],
		'precip_day5_back' :precip_list[4],
		'precip_day6_back' :precip_list[5],
		'precip_day7_back' :precip_list[6],
		'precip_day8_back' :precip_list[7],
		'precip_day9_back' :precip_list[8],
		'precip_day10_back':precip_list[9],
		}
		
		cursor.execute(add_interval, interval_data)
		cnx.commit()


cnx.close()			