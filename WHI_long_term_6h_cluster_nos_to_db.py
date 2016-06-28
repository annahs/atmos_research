import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import calendar

cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def get_6h_cluster(hourly_start_time):
	cursor.execute('''SELECT cluster_number,cluster_start_time,cluster_end_time
					  FROM whi_ft_cluster_times_2009to2012
					  WHERE (cluster_start_time <= %s AND cluster_end_time > %s)
					  ''',
					  (hourly_start_time,hourly_start_time))
		
	hy_id_list = cursor.fetchall()
	if hy_id_list == []:
		hy_id = None
		cluster_start = None
		cluster_end = None
	else:
		hy_id = hy_id_list[0][0]
		cluster_start = hy_id_list[0][1]
		cluster_end = hy_id_list[0][2]
	#print '6h', datetime.utcfromtimestamp(cluster_start),datetime.utcfromtimestamp(cluster_end)
	return hy_id

cursor.execute('''SELECT id,UNIX_UTC_start_time,UNIX_UTC_end_time
					  FROM whi_hysplit_hourly_data''')
hourly_data = cursor.fetchall()


for row in hourly_data:
	hourly_id = row[0]
	hourly_start = row[1]
	hourly_end = row[2]
	
	cluster_6h = get_6h_cluster(hourly_start)
	#print '1h',datetime.utcfromtimestamp(hourly_start), datetime.utcfromtimestamp(hourly_end)
	#print cluster_6h
	
	cursor.execute('''UPDATE whi_hysplit_hourly_data
						SET 6h_cluster_number = %s 
						WHERE id = %s ''',
						(cluster_6h,hourly_id))
	cnx.commit()
	
cnx.close()