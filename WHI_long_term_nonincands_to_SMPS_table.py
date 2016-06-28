import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates
from mpl_toolkits.basemap import Basemap
import calendar
from scipy.optimize import curve_fit


bin_min = 245
bin_max = 265

start_time = datetime(2012,7,28,8,0)
end_time = datetime(2012,7,29,8,0)
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())
print start_time, UNIX_start_time
print end_time, UNIX_end_time



R = 8.3144621 # in m3*Pa/(K*mol)
sample_flow_lower_limit = 100

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#MySQL data insert statement
add_data = ('INSERT INTO whi_smps_data'
	  '(UNIX_UTC_start_time, UNIX_UTC_end_time, bin_lower_limit_nm, bin_upper_limit_nm, binned_property, value)'
	  'VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(binLL)s,%(binUL)s,%(property)s,%(prop_value)s)')


no_prev_particle = False
printcounter = 0

cursor.execute(('SELECT UNIX_UTC_start_time,UNIX_UTC_end_time,bin_lower_limit_nm,bin_upper_limit_nm FROM whi_smps_data WHERE UNIX_UTC_start_time >= %s and UNIX_UTC_end_time <= %s and bin_lower_limit_nm >= %s and bin_upper_limit_nm <= %s'),
(UNIX_start_time,UNIX_end_time, 198,320))	
data = cursor.fetchall()
for row in data:
	start_ts = row[0]
	end_ts = row[1]
	bin_LL = row[2]
	bin_UL = row[3]

	interval_sampling_time = end_ts-start_ts
	interval_sampled_volume = 120*interval_sampling_time/60 #factor of 60 to convert minutes to secs (flow is sccm), result is in cc
	
	
	#get T and P for correction to STP/SCCM
	cursor.execute(('SELECT outside_temp_C,pressure_Pa from whi_sampling_conditions where UNIX_UTC_start_time >= %s and UNIX_UTC_end_time <= %s'),(start_ts,end_ts))
	TandP_data = cursor.fetchall()

				
	##### SP2 data	
	#get nonincand data 
	cursor.execute(('SELECT count(*) from whi_calibration_data where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and particle_dia >=%s and particle_dia <=%s'),
		(start_ts,end_ts, 'nonincand', bin_LL,bin_UL))
	nonincand_count = cursor.fetchall()[0][0]	


	temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
	pressure = TandP_data[0][1]
	correction_factor_for_STP = (101325/pressure)*(temperature/273.15)
	nonincand_number_conc = nonincand_count*correction_factor_for_STP/interval_sampled_volume  #dN/sccm

	binned_data = {
	'UNIX_UTC_start_time': start_ts,
	'UNIX_UTC_end_time': end_ts,
	'binLL':  bin_LL,
	'binUL':  bin_UL,
	'property': 'nonincand_number_per_cc',
	'prop_value': nonincand_number_conc,
	}
	cursor.execute(add_data, binned_data)
	cnx.commit()



cnx.close()
