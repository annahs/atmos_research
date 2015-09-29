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


list_file = open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI_rBC_record_2009to2013-spikes_removed.rbcpckl', 'r')
rBC_data_list = pickle.load(list_file)
list_file.close()


cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT IGNORE INTO whi_sp2_rbc_record_2009to2012_spikes_removed'
              '(interval_mid_time,incand_number_conc,BC_mass_conc,BC_mass_conc_LL,BC_mass_conc_UL,interval_sampling_duration,interval_incand_count,UNIX_GMT_ts)'
              'VALUES (%(interval_mid_time)s,%(incand_number_conc)s,%(BC_mass_conc)s,%(BC_mass_conc_LL)s,%(BC_mass_conc_UL)s,%(interval_sampling_duration)s,%(interval_incand_count)s,%(UNIX_GMT_ts)s)')

			  
			  
for row in rBC_data_list:
	
	interval_data = {
	'interval_mid_time': str(row[0]),
	'incand_number_conc': row[1],
	'BC_mass_conc': row[2],
	'BC_mass_conc_LL': row[3],
	'BC_mass_conc_UL': row[4],
	'interval_sampling_duration': row[5],
	'interval_incand_count': row[6],
	'UNIX_GMT_ts': row[7],
	}
		
	cursor.execute(add_interval, interval_data)
	cnx.commit()

			

cnx.close()			