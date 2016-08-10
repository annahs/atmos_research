import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
from mpl_toolkits.basemap import Basemap
import mysql.connector
import calendar



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

add_data = ('INSERT INTO whi_hysplit_hourly_data'
			  '(UNIX_UTC_start_time,UNIX_UTC_end_time,1h_cluster_number,6h_cluster_number,precip_total,precip_first_72h,precip_last_72h)'
			  'VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(1h_cluster_number)s,%(6h_cluster_number)s,%(precip_total)s,%(precip_first_72h)s,%(precip_last_72h)s)'
			  )


			  
CLUSLIST_file = 'C:/HYSPLIT_argh/WHI_1h_10-day_working/all_hours/CLUSLIST_5'

i=1
multiple_records = []


with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		date = datetime(2000+int(newline[2]),int(newline[3]),int(newline[4]),int(newline[5]))
		UNIX_UTC_ts = calendar.timegm(date.utctimetuple())
		cluster = int(newline[0])
		if cluster == 3:
			cluster = 1
		
		file = newline[7]

		tdump_file = open(file, 'r')
		data_start = False
		precips = []
		sig_precip_hours = 0
		for line in tdump_file:
			newline = line.split()

			if data_start == True:
				precip = float(newline[13])
				if precip >= 1.0:
					sig_precip_hours += 1
				precips.append(precip)
				
			if newline[1] == 'PRESSURE':
				data_start = True
		
		total_precip = float(np.sum(precips))
		early_precip = float(np.sum(precips[:72]))
		late_precip = float(np.sum(precips[-72:]))
		
		
		cursor.execute('''UPDATE whi_hysplit_hourly_data
							SET total_hrs_with_sig_precip = %s
							WHERE UNIX_UTC_start_time = %s''',
							(sig_precip_hours,UNIX_UTC_ts))
		cnx.commit()
		#single_record ={
		#	'UNIX_UTC_start_time':UNIX_UTC_ts,
		#	'UNIX_UTC_end_time':(UNIX_UTC_ts+3600),
		#	'1h_cluster_number': cluster,
		#	'6h_cluster_number': None,
		#	'precip_total': total_precip, 
		#	'precip_first_72h': early_precip,
		#	'precip_last_72h': late_precip,
		#}		  
		#	
		#multiple_records.append((single_record))
        
		##bulk insert to db table
		#if i%2000 == 0:
		#	cursor.executemany(add_data, multiple_records)
		#	cnx.commit()
		#	multiple_records = []
		#	
		##increment count 
		#i+= 1
		
		tdump_file.close()
		
#bulk insert of remaining records to db
if multiple_records != []:
	cursor.executemany(add_data, multiple_records)
	cnx.commit()
	multiple_records = []		



cnx.close()




		
 

		