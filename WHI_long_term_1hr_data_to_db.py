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


start = datetime(2009,6,28)  #2009 - 20090628  2010 - 20100610   2012 - 20100405
end =   datetime(2012,6,1)  #2009 - 20090816  2010 - 20100726   2012 - 20100601
timestep = 1 #hours
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
	
def get_hysplit_id(particle_start_time):
	cursor.execute('''SELECT id
					  FROM whi_hysplit_hourly_data
					  WHERE (UNIX_UTC_start_time <= %s AND UNIX_UTC_end_time > %s)
					  ''',
					  (particle_start_time,particle_start_time))
		
	hy_id_list = cursor.fetchall()
	if hy_id_list == []:
		hy_id = None
	else:
		hy_id = hy_id_list[0][0]

	return hy_id
	
def get_met_id(particle_start_time):
	cursor.execute('''SELECT id
					  FROM whi_sampling_conditions
					  WHERE (UNIX_UTC_start_time <= %s AND UNIX_UTC_end_time > %s)
					  ''',
					  (particle_start_time,particle_start_time))
		
	met_id_list = cursor.fetchall()
	if met_id_list == []:
		met_id = None
	else:
		met_id = met_id_list[0][0]

	return met_id
	
def get_gc_id(particle_start_time):
	cursor.execute('''SELECT id
					  FROM whi_gc_hourly_bc_data
					  WHERE (UNIX_UTC_start_time <= %s AND UNIX_UTC_end_time > %s)
					  ''',
					  (particle_start_time,particle_start_time))
		
	gc_id_list = cursor.fetchall()
	if gc_id_list == []:
		gc_id = None
	else:
		gc_id = gc_id_list[0][0]
	return gc_id
	
	
def get_sample_factor(UNIX_start):
	date_time = datetime.utcfromtimestamp(UNIX_start)
	
	sample_factors_2012 = [
		[datetime(2012,4,4,19,43,4), datetime(2012,4,5,13,47,9),   3.0],
		[datetime(2012,4,5,13,47,9), datetime(2012,4,10,3,3,25),   1.0],
		[datetime(2012,4,10,3,3,25), datetime(2012,5,16,6,9,13),   3.0],
		[datetime(2012,5,16,6,9,13), datetime(2012,6,7,18,14,39), 10.0],
		]
	
	if date_time.year in [2009,2010]:
		sample_factor = 1.0
	if date_time.year == 2012:
		for date_range in sample_factors_2012:
			start_date = date_range[0]
			end_date = date_range[1]
			range_sample_factor = date_range[2]
			if start_date<= date_time < end_date:
				sample_factor = range_sample_factor
				
	return sample_factor
	
	
#query to add 1h mass conc data
add_data = ('''INSERT INTO whi_sp2_hourly_data
			  (UNIX_UTC_start_time,UNIX_UTC_end_time,number_particles,rBC_mass,rBC_mass_err,volume_air_sampled,mean_lag_time,sample_factor,hysplit_hourly_id,whi_sampling_cond_id,gc_hourly_id)
			  VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(number_particles)s,%(rBC_mass)s,%(rBC_mass_err)s,%(volume_air_sampled)s,%(mean_lag_time)s,%(sample_factor)s,%(hysplit_hourly_id)s,%(whi_sampling_cond_id)s,%(gc_hourly_id)s)'''
			  )
	
#

multiple_records = []
i=1
while start <= end:
	print start
	UNIX_start = calendar.timegm(start.utctimetuple())
	UNIX_end = UNIX_start + timestep*3600
	st = datetime.now()
	#filter on hk data here
	cursor.execute('''(SELECT 
	mn.UNIX_UTC_ts_int_start,
	mn.UNIX_UTC_ts_int_end,
	mn.rBC_mass_fg_BBHG,
	mn.rBC_mass_fg_BBHG_err,
	mn.BB_incand_pk_pos,
	mn.BB_scat_pk_pos,
	mn.BB_scat_pkht,
	hk.sample_flow
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
	print datetime.now()-st
	print 'records:',len(ind_data)
	data={
	'rBC_mass_fg':[],
	'rBC_mass_fg_err':[],
	'lag_time':[]
	}
	
	total_sample_vol = 0
	
	for row in ind_data:
		ind_start_time = float(row[0])
		ind_end_time = float(row[1])
		bbhg_mass_corr = float(row[2])
		bbhg_mass_corr_err = float(row[3])
		BB_incand_pk_pos = float(row[4])
		BB_scat_pk_pos = float(row[5])	
		BB_scat_pk_ht = float(row[6])	
		sample_flow = float(row[7])  #in vccm
		
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
		
		
		sample_vol =  (sample_flow*(ind_end_time-ind_start_time)/60)    #/60 b/c sccm and time in secs  
		total_sample_vol = total_sample_vol + sample_vol
		
		data['rBC_mass_fg'].append(bbhg_mass_corr)  
		data['rBC_mass_fg_err'].append(bbhg_mass_corr_err)  
		#only calc lag time if there is a scattering signal
		if BB_scat_pk_ht > min_scat_pkht:
			lag_time = (BB_incand_pk_pos-BB_scat_pk_pos)*0.2  #us
			data['lag_time'].append(lag_time)  
	
	tot_rBC_mass_fg =  sum(data['rBC_mass_fg'])
	tot_rBC_mass_uncer =  sum(data['rBC_mass_fg_err'])
	rBC_number =  len(data['rBC_mass_fg'])
	mean_lag =  float(np.mean(data['lag_time']))
	if np.isnan(mean_lag):
		mean_lag = None
	
	#get sample factor, hysplit id, met Id, gc_id
	sample_factor = get_sample_factor(UNIX_start)
	
	#get hysplit_id
	hysplit_id = get_hysplit_id(UNIX_start)
	
	#get sampling conditions id
	met_id = get_met_id(UNIX_start)
	
	#get hysplit_id
	gc_id = get_gc_id(UNIX_start)
	
	
	#add to db
	single_record = {
		'UNIX_UTC_start_time'	:UNIX_start,
		'UNIX_UTC_end_time'     :UNIX_end,
		'number_particles'      :rBC_number,
		'rBC_mass'              :tot_rBC_mass_fg,
		'rBC_mass_err'          :tot_rBC_mass_uncer,
		'volume_air_sampled'    :total_sample_vol,
		'mean_lag_time'         :mean_lag,
		'sample_factor'         :sample_factor,
		'hysplit_hourly_id'     :hysplit_id,
		'whi_sampling_cond_id'  :met_id,
		'gc_hourly_id'          :gc_id,
	}

	multiple_records.append((single_record))
	
	#bulk insert to db table
	if i%24 == 0:
		cursor.executemany(add_data, multiple_records)
		cnx.commit()
		multiple_records = []
	#increment count 
	i+= 1
	
	start += timedelta(hours = timestep)
	
#bulk insert of remaining records to db
if multiple_records != []:
	cursor.executemany(add_data, multiple_records)
	cnx.commit()
	multiple_records = []	
	
	
	
	
cnx.close()
