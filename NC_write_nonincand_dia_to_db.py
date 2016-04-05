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


flight = 'science 1'

flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),  datetime(2015,4,5,14,0) ],	
'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ],  
'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ],
'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ],
'science 3'  : [datetime(2015,4,8,13,0), datetime(2015,4,8,17,0) ],  
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0) ],
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0) ],
'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0)],
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0)],
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0)],
'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0)],
'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0) ],
'science 10' : [datetime(2015,4,21,16,8),datetime(2015,4,21,16,18)],  ###
}



start_time = flight_times[flight][0]
end_time = flight_times[flight][1]
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())
print start_time, UNIX_start_time
print end_time, UNIX_end_time

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/Nonincand_lookup_table_POLAR6_2015_UBCSP2-fullPSLcalib_used_factor204-scaled_for_Alert.lupckl'
lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()	

#get the dia from the lookup table - assuming pure AS                 
scat_amps = sorted(lookup_table.keys())

cursor.execute(('SELECT id,FF_scat_amp FROM polar6_calibration_data where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s'),
	(UNIX_start_time,UNIX_end_time, 'nonincand'))	
data = cursor.fetchall()
print 'fetched'

for row in data:
	row_id = row[0]
	particle_scat = row[1]
	AS_diameter = None
	for scat_amp in scat_amps:
		if scat_amp >= particle_scat:
			AS_diameter = lookup_table[scat_amp]
			break

	cursor.execute(('UPDATE polar6_calibration_data SET particle_dia = %s WHERE id = %s  '),(AS_diameter,row_id))
	cnx.commit()


cnx.close()
