#this script is used to add rBC mass to the database

import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from scipy.optimize import curve_fit
from scipy import stats
from SP2_particle_record_UTC import ParticleRecord
from struct import *
import hk_new
import hk_new_no_ts_LEO
from scipy import linspace, polyval, polyfit, sqrt, stats
import math
import mysql.connector
from datetime import datetime
import calendar



#setup
data_dir = 'F:/Alert/2014/SP2B_files/'
start_analysis_at = datetime(2014,12,24)
end_analysis_at = 	datetime(2015,1,1)
SP2_number = 58
min_incand_BBHG = 50

record_size_bytes = 1658 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458, Alert SP2 #4 and #58 = 832? )

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#**********parameters dictionary**********
parameters = {
'acq_rate': 2500000, #5000000,
}

def checkHKId(particle_event_time,instr_number):
	event_minute = int(particle_event_time-particle_event_time%60)  #hk data is in 1min intervals, so need event minute
	cursor.execute(('SELECT id FROM alert_hk_data WHERE SP2_ID =%s AND UNIX_UTC_ts = %s'),(instr_number,event_minute))
	hk_data = cursor.fetchall()
	if hk_data != []:
		hk_id= hk_data[0][0]
	else:
		hk_id = None
		
	return hk_id

def getParticleData(parameters_dict,instr_number,bbhg_incand_min,prev_particle_ts):
	
	f = open(parameters_dict['file'], 'rb')
	
	start_time = prev_particle_ts
	record_index = 0      
	current_minute = 0
	
	##Retrieve HK id for the event to join tables on later
	housekeeping_id = checkHKId(start_time,instr_number)
	
	temp={
	'rBC_mass_fg_HG_low':[],
	'rBC_mass_fg_HG_high':[],
	'rBC_mass_fg_LG_low':[],
	'rBC_mass_fg_LG_high':[],
	}
	
	while record_index < parameters['number_of_records']:
		
		#read the binary for a particle
		record = f.read(parameters['record_size'])	
	
		particle_record = ParticleRecord(record, parameters_dict['acq_rate'])
		
		#run the wideband HG incandPeakInfo method to retrieve various HG BB incandescence peak attributes	
		particle_record.incandPeakInfo() 			
		bbhg_incand_pk_amp = float(particle_record.incandMax)
		
		#if this is an incandescent particle that we can detect with the HG channel then continue
		if bbhg_incand_pk_amp >= bbhg_incand_min:
			event_time = particle_record.timestamp  #UTC
			event_time_dt = datetime.utcfromtimestamp(event_time)

			#get incandescent signals
			particle_record.incandPeakInfoLG()
			bblg_incand_pk_amp = float(particle_record.incandMax_LG)
			
			particle_record.narrowIncandPeakInfo()
			nbhg_incand_pk_amp = float(particle_record.narrowIncandMax)
			
			particle_record.narrowIncandPeakInfoLG()
			nblg_incand_pk_amp = float(particle_record.narrowIncandMax_LG)
				
			#calculate masses
			bbhg_mass = 0.41527 + 2.13238E-4*bbhg_incand_pk_amp + 7.17406E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp
			bbhg_mass_uncertainty = 0.0869 + 1.09646E-5*bbhg_incand_pk_amp + 2.2873E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp
			
			bblg_mass = 0.70095 + 0.00182*bblg_incand_pk_amp + 1.22794E-7*bblg_incand_pk_amp*bblg_incand_pk_amp
			bblg_mass_uncertainty = 0.30863 + 1.38156E-4*bblg_incand_pk_amp + 1.17569E-8*bblg_incand_pk_amp*bblg_incand_pk_amp

			######
			if event_time_dt.minute == current_minute:
				if 0.33 <= bbhg_mass < 1.8:
					temp['rBC_mass_fg_HG_low'].append(bbhg_mass)  
				if 1.8 <= bbhg_mass < 12.8:
					temp['rBC_mass_fg_HG_high'].append(bbhg_mass)
				if 1.8 <= bblg_mass < 12.8:
					temp['rBC_mass_fg_LG_low'].append(bblg_mass)
				if 12.8 <= bblg_mass < 36.3:
					temp['rBC_mass_fg_LG_high'].append(bblg_mass)		
			else:
				end_time = event_time
				
				if 0.33 <= bbhg_mass < 1.8:
					temp['rBC_mass_fg_HG_low'].append(bbhg_mass)  
				if 1.8 <= bbhg_mass < 12.8:
					temp['rBC_mass_fg_HG_high'].append(bbhg_mass)
				if 1.8 <= bblg_mass < 12.8:
					temp['rBC_mass_fg_LG_low'].append(bblg_mass)
				if 12.8 <= bblg_mass < 36.3:
					temp['rBC_mass_fg_LG_high'].append(bblg_mass)
				
				avg_rBC_mass_fg_HG_low =  float(np.nan_to_num(np.mean(temp['rBC_mass_fg_HG_low'])))
				rBC_number_HG_low =  len(temp['rBC_mass_fg_HG_low'])
				
				avg_rBC_mass_fg_HG_high = float(np.nan_to_num(np.mean(temp['rBC_mass_fg_HG_high'])))
				rBC_number_HG_high = len(temp['rBC_mass_fg_HG_high'])
				
				avg_rBC_mass_fg_LG_low =  float(np.nan_to_num(np.mean(temp['rBC_mass_fg_LG_low'])))
				rBC_number_LG_low = len(temp['rBC_mass_fg_LG_low'])
				
				avg_rBC_mass_fg_LG_high = float(np.nan_to_num(np.mean(temp['rBC_mass_fg_LG_high'])))
				rBC_number_LG_high = len(temp['rBC_mass_fg_LG_high'])
	
				
				#put data into database
				add_interval = ('''INSERT INTO alert_1min_mass_number_data (		
						instrument_ID, 
						UNIX_UTC_ts_int_start,  
						UNIX_UTC_ts_int_end,  
						rBC_mass_fg_HG_low,  
						rBC_number_HG_low,  
						rBC_mass_fg_HG_high,  
						rBC_number_HG_high,  
						rBC_mass_fg_LG_low,  
						rBC_number_LG_low,  
						rBC_mass_fg_LG_high,  
						rBC_number_LG_high,  
						HK_id
						)
						VALUES (
						%(instrument_ID)s,
						%(UNIX_UTC_ts_int_start)s,
						%(UNIX_UTC_ts_int_end)s,
						%(rBC_mass_fg_HG_low)s,
						%(rBC_number_HG_low)s,
						%(rBC_mass_fg_HG_high)s,
						%(rBC_number_HG_high)s,
						%(rBC_mass_fg_LG_low)s,
						%(rBC_number_LG_low)s,
						%(rBC_mass_fg_LG_high)s,
						%(rBC_number_LG_high)s,
						%(HK_id)s
						)''')
							
	
				
				interval_data = {
				'instrument_ID':instr_number,
				'UNIX_UTC_ts_int_start':start_time,
				'UNIX_UTC_ts_int_end':end_time,
				'rBC_mass_fg_HG_low':avg_rBC_mass_fg_HG_low,
				'rBC_number_HG_low':rBC_number_HG_low,
				'rBC_mass_fg_HG_high':avg_rBC_mass_fg_HG_high,
				'rBC_number_HG_high':rBC_number_HG_high,
				'rBC_mass_fg_LG_low': avg_rBC_mass_fg_LG_low,
				'rBC_number_LG_low': rBC_number_LG_low,
				'rBC_mass_fg_LG_high':avg_rBC_mass_fg_LG_high,
				'rBC_number_LG_high':rBC_number_LG_high,
				'HK_id':housekeeping_id,
				}

				cursor.execute(add_interval, interval_data)
				cnx.commit()

												
				temp={
				'rBC_mass_fg_HG_low':[],
				'rBC_mass_fg_HG_high':[],
				'rBC_mass_fg_LG_low':[],
				'rBC_mass_fg_LG_high':[],
				}
			
				start_time = event_time
				##Retrieve HK id for the event to join tables on later
				housekeeping_id = checkHKId(start_time,instr_number)
			
			current_minute = event_time_dt.minute

			#####
			
		record_index+=1   
	
	f.close()
	return prev_particle_ts




os.chdir(data_dir)
for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
		parameters['folder']= directory
		folder_date = datetime.strptime(directory, '%Y%m%d')		
		if folder_date >= start_analysis_at and folder_date < end_analysis_at:
			parameters['directory']=os.path.abspath(directory)
			os.chdir(parameters['directory'])
			
			#start the fitting
			prev_event_ts = 0
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False):
					print file
					parameters['file'] = file
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					parameters['record_size'] = record_size_bytes  
					parameters['number_of_records']= (file_bytes/parameters['record_size'])-1

					prev_event_ts = getParticleData(parameters,SP2_number,min_incand_BBHG,prev_event_ts)
			os.chdir(data_dir)
cnx.close()	



	
