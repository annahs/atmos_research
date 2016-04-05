import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
from datetime import datetime
import mysql.connector



start_time = datetime(2012,7,27,22,24)
end_time = datetime(2012,7,28,8,0)
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())
print start_time, UNIX_start_time
print end_time, UNIX_end_time

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/lookup files/Nonincand_lookup_table_WHI_2012_UBCSP2-used_factor225.lupckl'
lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()	

#get the dia from the lookup table - assuming pure AS                 
scat_amps = sorted(lookup_table.keys())

cursor.execute(('SELECT id,actual_scat_amp FROM whi_calibration_data where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and particle_dia IS NULL'),
	(UNIX_start_time,UNIX_end_time, 'nonincand'))	
data = cursor.fetchall()
print 'fetched ', len(data)

for row in data:
	row_id = row[0]
	particle_scat = row[1]
	AS_diameter = None
	for scat_amp in scat_amps:
		if scat_amp >= particle_scat:
			AS_diameter = lookup_table[scat_amp]
			break

	cursor.execute(('UPDATE whi_calibration_data SET particle_dia = %s WHERE id = %s  '),(AS_diameter,row_id))
	cnx.commit()


cnx.close()
