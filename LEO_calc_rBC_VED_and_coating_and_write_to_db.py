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
from coating_info_from_raw_signal import CoatingData

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

instrument = 'UBCSP2'
instrument_locn = 'POLAR6'
type_particle = 'incand'
start_date = datetime(2015,4,6)
end_date =   datetime(2015,4,22)
lookup_file = 'C:\Users\Sarah Hanna\Documents\Data\Alert Data\lookup_tables'
#lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor204-scaled_for_Alert.lupckl'
rBC_density = 1.8 
incand_sat = 3750


UNIX_time_stamp_start = calendar.timegm(start_date.utctimetuple())
UNIX_time_stamp_end   = calendar.timegm(end_date.utctimetuple())

cursor.execute(('SELECT id, incand_amp, LF_scat_amp, UNIX_UTC_ts from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and instrument = %s and incand_amp <=%s'),
	(UNIX_time_stamp_start,UNIX_time_stamp_end, type_particle, instrument, incand_sat))	
data = cursor.fetchall()
coating_record = CoatingData(lookup_file)
print 'onward'
LOG_EVERY_N = 10000
i = 0
for row in data:
	row_id = row[0]
	incand_amp = row[1]
	LF_amp = row[2]
	event_time = datetime.utcfromtimestamp(row[3])
	
	rBC_mass = coating_record.get_rBC_mass(incand_amp, instrument,event_time.year)
	rBC_VED = (((rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7
	if rBC_VED >= 65 and rBC_VED <=220 and LF_amp < 45000 and LF_amp > 0:
		coat_th = coating_record.get_coating_thickness(rBC_VED,LF_amp)
	else:
		rBC_VED = None
		coat_th = None

	cursor.execute(('UPDATE polar6_coating_2015 SET coat_thickness_nm_jancalib = %s, rBC_mass_fg_jancalib = %s WHERE id = %s'),(coat_th,rBC_mass,row_id))	
	cnx.commit()

	i+=1
	if (i % LOG_EVERY_N) == 0:
		print 'record: ', i
	
cnx.close()


