import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math

#need to filter on spike times, hk (flow, yag, etc), RH (for in-cloud times), local BB

start_ts = datetime(2009,6,28)  #2009 - 20090628  2010 - 20100610   2012 - 20100405
end_ts = datetime(2012,6,1)     #2009 - 20090816  2010 - 20100726   2012 - 20100601
bin_incr = 10
min_bin = 150
max_bin = 220
timestep = 1 #hours for RH and cluster filtering

#hk parameters
sample_min = 117  #117 for all 2009-2012
sample_max = 123  #123 for all 2009-2012
yag_min = 3.8  #3.8 for all 2009-2012
yag_max = 6	 #6  for all 2009-2012


#local BB times
fire_span_09s=datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span_09f=datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')



#database connection
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
	
def get_hysplit_clusters(hour_start):
	cursor.execute('''SELECT cluster_number_1h,cluster_number_6h
					  FROM whi_hysplit_hourly_data
					  WHERE (UNIX_UTC_start_time <= %s AND UNIX_UTC_end_time > %s)
					  ''',
					  (hour_start,hour_start))
		
	hy_id_list = cursor.fetchall()
	
	#cluster names
	cluster_names_1h = {
		1:'NPac',
		2:'WPac',
		4:'NCan',
		5:'SPac',
		None:None,
		}
			
	cluster_names_6h = {
		1:'NPac',
		2:'WPac',
		3:'NPac',
		4:'NCan',
		5:'NPac',
		6:'SPac',
		7:'WPac',
		8:'SPac',
		9:'SPac',
		10:'NPac',
		None:None,
		}

	if hy_id_list == []:
		return [None, None]
	
	cluster_1h_number = hy_id_list[0][0]
	cluster_6h_number = hy_id_list[0][1]
	cluster_1h_name = cluster_names_1h[cluster_1h_number]
	cluster_6h_name = cluster_names_6h[cluster_6h_number]
	return [cluster_1h_name,cluster_6h_name]
	
def get_RH(hour_start):
	cursor.execute('''SELECT RH
					  FROM whi_sampling_conditions
					  WHERE (UNIX_UTC_start_time <= %s AND UNIX_UTC_end_time > %s)
					  ''',
					  (hour_start,hour_start))
		
	met_list = cursor.fetchall()
	if met_list == []:
		RH = None
	else:
		RH = met_list[0][0]

	return RH

	

#mysql to add records	
add_data = ('''INSERT INTO whi_sp2_distr_data
		  (bin_LL,bin_UL,mass,number,volume,cluster_interval,cluster)
		  VALUES (%(bin_LL)s,%(bin_UL)s,%(mass)s,%(number)s,%(volume)s,%(cluster_interval)s,%(cluster)s)'''
		  )
	
	

	
#start getting data
for bin in range(min_bin,max_bin,bin_incr):
	bin_LL = bin
	bin_UL = bin+bin_incr
	print bin_LL, bin_UL
	bin_mass_min = ((bin_LL/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
	bin_mass_max = ((bin_UL/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

	#dictionaries for storing the bin data - reset for each bin
	cluster_1h = {
	'NPac':{'mass':0,'number':0,'volume':0,},
	'SPac':{'mass':0,'number':0,'volume':0,},
	'WPac':{'mass':0,'number':0,'volume':0,},
	'NCan':{'mass':0,'number':0,'volume':0,},
	'BB':{'mass':0,'number':0,'volume':0,},
	}
	
	cluster_6h = {
	'NPac':{'mass':0,'number':0,'volume':0,},
	'SPac':{'mass':0,'number':0,'volume':0,},
	'WPac':{'mass':0,'number':0,'volume':0,},
	'NCan':{'mass':0,'number':0,'volume':0,},
	'BB':{'mass':0,'number':0,'volume':0,},
	}
	
	#run through at hourly intervals because this is the resoltuion of the hysplit clustering and the RH measurements
	start = start_ts
	while start <= end_ts:
		#only look at 2000-0800 PST
		if (datetime(2009,8,16) < start < datetime(2010,6,10)) or (datetime(2010,7,26) < start < datetime(2012,4,5)):
			start += timedelta(hours = timestep)
			continue
			
		if (4 <= start.hour < 16):
			print start
			#variables for storing the hourly data
			total_sample_vol = 0
			total_mass = 0
			total_number = 0
			
			UNIX_start = calendar.timegm(start.utctimetuple())
			UNIX_end = UNIX_start + timestep*3600
			
			
			#filter RH for in-cloud do this here becasue its at hourly resolution so must remove whole hour
			RH = get_RH(UNIX_start)
			if RH > 90:
				print 'RH:',RH
				start += timedelta(hours = timestep)
				continue
			
			#filter on hk data here
			cursor.execute('''(SELECT 
			mn.UNIX_UTC_ts_int_start,
			mn.UNIX_UTC_ts_int_end,
			mn.rBC_mass_fg_BBHG,
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
			(UNIX_start,UNIX_end,bin_mass_min,bin_mass_max,sample_min,sample_max,yag_min,yag_max))
			sp_data = cursor.fetchall()
					
			for row in sp_data:
				ind_start_time = float(row[0])
				ind_end_time = float(row[1])
				bbhg_mass_corr = float(row[2])
				sample_flow = float(row[3])  #in vccm
				
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
				
				
				sample_vol =  (sample_flow*(ind_end_time-ind_start_time)/60)    #/60 b/c sccm and time in secs  0.87 = STP corr?????
				total_sample_vol = total_sample_vol + sample_vol
				total_mass = total_mass + bbhg_mass_corr
				total_number = total_number + 1	
			
			#get hysplit_clusters - these are at hourly resolution so that's why we do this in hour-long chunks
			hysplit_clusters = get_hysplit_clusters(UNIX_start)
			cluster_1h_name = hysplit_clusters[0]
			cluster_6h_name = hysplit_clusters[1]
			
			#overwrite cluster name if local BB
			if (fire_span_09s <= start < fire_span_09f) or (fire_span_10s <= start < fire_span_10f):
				cluster_1h_name = 'BB'
				cluster_6h_name = 'BB'

			#add hours data to cluster dicts for each bin
			if cluster_1h_name != None:
				cluster_1h[cluster_1h_name]['mass'] =   cluster_1h[cluster_1h_name]['mass'] + total_mass
				cluster_1h[cluster_1h_name]['number'] = cluster_1h[cluster_1h_name]['number'] + total_number
				cluster_1h[cluster_1h_name]['volume'] = cluster_1h[cluster_1h_name]['volume'] + total_sample_vol
			
			if cluster_6h_name != None:
				cluster_6h[cluster_6h_name]['mass']   = cluster_6h[cluster_6h_name]['mass'] + total_mass
				cluster_6h[cluster_6h_name]['number'] = cluster_6h[cluster_6h_name]['number'] + total_number
				cluster_6h[cluster_6h_name]['volume'] = cluster_6h[cluster_6h_name]['volume'] + total_sample_vol
		
		#move to next hour
		start += timedelta(hours = timestep)
	
	#add this bins data to db	
	for cluster in cluster_1h:	
		
		single_record_1h = {
		'bin_LL'			:bin_LL,
		'bin_UL'    		:bin_UL,
		'mass'     			:cluster_1h[cluster]['mass'],
		'number'            :cluster_1h[cluster]['number'],
		'volume'            :cluster_1h[cluster]['volume'],
		'cluster_interval'  :1,
		'cluster'   		:cluster,
		}
		
		cursor.execute(add_data, single_record_1h)
		cnx.commit()
		
		
	for cluster in cluster_6h:
		single_record_6h = {
		'bin_LL'			:bin_LL,
		'bin_UL'    		:bin_UL,
		'mass'     			:cluster_6h[cluster]['mass'],
		'number'            :cluster_6h[cluster]['number'],
		'volume'            :cluster_6h[cluster]['volume'],
		'cluster_interval'  :6,
		'cluster'   		:cluster,
		}
		
		cursor.execute(add_data, single_record_6h)
		cnx.commit()
	
	
cnx.close()