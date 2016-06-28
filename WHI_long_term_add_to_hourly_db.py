import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import calendar
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib import dates

lag_threshold_2009 = 0.1
lag_threshold_2010 = 0.25
lag_threshold_2012 = 1.5

sample_min = 117  #117 for all 2009-2012
sample_max = 123  #123 for all 2009-2012
yag_min = 3.8  #3.8 for all 2009-2012
yag_max = 6	 #6  for all 2009-2012
BC_VED_min = 70
BC_VED_max = 220
min_scat_pkht = 20
mass_min = ((BC_VED_min/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
mass_max = ((BC_VED_max/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
print 'mass limits', mass_min, mass_max

cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()
 
def check_spike_times(particle_start_time,particle_end_time):
	cursor.execute('''SELECT count(*)
					  FROM whi_spike_times_2009to2012
					  WHERE (spike_start_UTC <= %s AND spike_end_UTC > %s)
					  OR (spike_start_UTC <= %s AND spike_end_UTC > %s)
					  ''',
					  (particle_start_time,particle_start_time,particle_end_time,particle_end_time))
		
	spike_count = cursor.fetchall()[0][0]
	return spike_count
	

#query to add 1h mass conc data
add_data = ('''INSERT INTO whi_sp2_hourly_data
			  (UNIX_UTC_start_time,UNIX_UTC_end_time,number_particles,rBC_mass,rBC_mass_err,volume_air_sampled,mean_lag_time,sample_factor,hysplit_hourly_id,whi_sampling_cond_id,gc_hourly_id)
			  VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(number_particles)s,%(rBC_mass)s,%(rBC_mass_err)s,%(volume_air_sampled)s,%(mean_lag_time)s,%(sample_factor)s,%(hysplit_hourly_id)s,%(whi_sampling_cond_id)s,%(gc_hourly_id)s)'''
			  )
	
#
cursor.execute('''(SELECT 
	UNIX_UTC_start_time,
	UNIX_UTC_end_time,
	id
	FROM whi_sp2_hourly_data 
	)''',)
hours = cursor.fetchall()


for hour in hours:
	long_lags = 0
	short_lags = 0
	
	UNIX_start = hour[0]
	UNIX_end = hour[1]
	hour_id = hour[2]
	start_dt =  datetime.utcfromtimestamp(UNIX_start)

	if start_dt < datetime(2012,4,7):
		continue
	print start_dt
	#filter individ particle data on hk data here
	cursor.execute('''(SELECT 
	mn.BB_incand_pk_pos,
	mn.BB_scat_pk_pos,
	mn.BB_scat_pkht,
	hk.sample_flow,
	mn.UNIX_UTC_ts_int_start,
	mn.UNIX_UTC_ts_int_end
	FROM whi_sp2_particle_data mn
	FORCE INDEX (hourly_binning)
	JOIN whi_hk_data hk on mn.HK_id = hk.id
	WHERE
	mn.UNIX_UTC_ts_int_start >= %s
	AND mn.UNIX_UTC_ts_int_end < %s
	AND mn.rBC_mass_fg_BBHG >= %s
	AND mn.rBC_mass_fg_BBHG <= %s
	AND hk.sample_flow >= %s
	AND hk.sample_flow < %s
	AND hk.yag_power >= %s
	AND hk.yag_power < %s)''',
	(UNIX_start,UNIX_end,mass_min,mass_max,sample_min,sample_max,yag_min,yag_max))
	
	ind_data = cursor.fetchall()
			
	for row in ind_data:
		BB_incand_pk_pos = float(row[0])
		BB_scat_pk_pos = float(row[1])	
		BB_scat_pk_ht = float(row[2])	
		sample_flow = float(row[3])  #in vccm
		ind_start_time = float(row[4])  
		ind_end_time = float(row[5])  
		
		#filter spike times here 
		if check_spike_times(ind_start_time,ind_end_time):
			print 'spike'
			continue
		
		#skip the long interval
		if (ind_end_time - ind_start_time) > 540:
			print 'long interval'
			continue
				
		#skip if no sample flow
		if sample_flow == None:
			print 'no flow'
			continue
		
		if BB_scat_pk_ht > min_scat_pkht:
			lag_time = (BB_incand_pk_pos-BB_scat_pk_pos)*0.2  #us
			if (-10 < lag_time < 10):			
				if start_dt.year == 2009 and lag_time > lag_threshold_2009:
					long_lags += 1
				elif start_dt.year == 2010 and lag_time > lag_threshold_2010:
					long_lags += 1
				elif start_dt.year == 2012 and lag_time > lag_threshold_2012:
					long_lags += 1
				else:
					short_lags += 1
		
	
	
	cursor.execute('''UPDATE whi_sp2_hourly_data
						SET number_long_lag = %s,
						number_short_lag = %s
						WHERE id = %s''',
						(long_lags,short_lags,hour_id))
	cnx.commit()
	
cnx.close()
