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
data_dir = 'F:/Alert/2012/SP2B_files/'
start_analysis_at = datetime(2012,3,22)
end_analysis_at = 	datetime(2012,3,27)
SP2_number = 17
min_incand_BBHG = 10
max_incand_BBHG = 3600

record_size_bytes = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458, Alert SP2 #4 and #58 = 1658)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#**********parameters dictionary**********
parameters = {
'acq_rate': 5000000, #5000000,
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

def getParticleData(parameters_dict,instr_number,bbhg_incand_min,prev_particle_ts,bbhg_incand_max):
	
	f = open(parameters_dict['file'], 'rb')
	record_index = 0      
	multiple_records = []
	i=1
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
			
			##Retrieve HK id for the event to join tables on later
			housekeeping_id = checkHKId(event_time,instr_number)
				
			particle_record.narrowIncandPeakInfo()
			nbhg_incand_pk_amp = float(particle_record.narrowIncandMax)
							
			####calculate masses
			
			#HG	
			bbhg_mass_uncorr = -0.017584 + 0.00647*bbhg_incand_pk_amp #SP217
			bbhg_mass_uncertainty_uncorr = 0.13765 + 1.99061E-4*bbhg_incand_pk_amp #SP217
			
			bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
			bbhg_mass_only_rel_err = bbhg_mass_uncertainty_uncorr/bbhg_mass_uncorr
			bbhg_ADcorr_rel_err = (0.05/0.7)
			bbhg_mass_abs_uncertainty_corr = (bbhg_ADcorr_rel_err + bbhg_mass_only_rel_err) * bbhg_mass_corr
			
					
			#add_data = ('INSERT INTO alert_mass_number_data_2012'							  
			#  '(sp2b_file, file_index, instrument_ID, UNIX_UTC_ts_int_start,UNIX_UTC_ts_int_end,BB_incand_HG,NB_incand_HG,rBC_mass_fg_BBHG,rBC_mass_fg_BBHG_err,HK_id)'
			#  'VALUES (%(sp2b_file)s,%(file_index)s,%(instrument_ID)s,%(UNIX_UTC_ts_int_start)s,%(UNIX_UTC_ts_int_end)s,%(BB_incand_HG)s,%(NB_incand_HG)s,%(rBC_mass_fg_BBHG)s,%(rBC_mass_fg_BBHG_err)s,%(HK_id)s)')
			#
			#
			#single_record ={
			#'sp2b_file' : parameters['file'],
			#'file_index' : record_index,
			#'instrument_ID' :instr_number,
			#'UNIX_UTC_ts_int_start' :prev_particle_ts,
			#'UNIX_UTC_ts_int_end' :event_time,
			#'BB_incand_HG': bbhg_incand_pk_amp,
			#'NB_incand_HG' : nbhg_incand_pk_amp, 
			#'rBC_mass_fg_BBHG': bbhg_mass_corr,
			#'rBC_mass_fg_BBHG_err': bbhg_mass_abs_uncertainty_corr,
			#'HK_id': housekeeping_id,		
			#}
			
			add_data = ('INSERT INTO alert_mass_number_data_2012'							  
			  '(sp2b_file, file_index, instrument_ID, UNIX_UTC_ts_int_start,UNIX_UTC_ts_int_end,BB_incand_HG,BB_incand_LG,NB_incand_HG,NB_incand_LG,rBC_mass_fg_BBHG,rBC_mass_fg_BBHG_err,rBC_mass_fg_BBLG,rBC_mass_fg_BBLG_err,HK_id)'
			  'VALUES (%(sp2b_file)s,%(file_index)s,%(instrument_ID)s,%(UNIX_UTC_ts_int_start)s,%(UNIX_UTC_ts_int_end)s,%(BB_incand_HG)s,%(BB_incand_LG)s,%(NB_incand_HG)s,%(NB_incand_LG)s,%(rBC_mass_fg_BBHG)s,%(rBC_mass_fg_BBHG_err)s,%(rBC_mass_fg_BBLG)s,%(rBC_mass_fg_BBLG_err)s,%(HK_id)s)')
			
			
			single_record ={
			'sp2b_file' : parameters['file'],
			'file_index' : record_index,
			'instrument_ID' :instr_number,
			'UNIX_UTC_ts_int_start' :prev_particle_ts,
			'UNIX_UTC_ts_int_end' :event_time,
			'BB_incand_HG': bbhg_incand_pk_amp,
			'BB_incand_LG': None,
			'NB_incand_HG' : nbhg_incand_pk_amp, 
			'NB_incand_LG' : None,
			'rBC_mass_fg_BBHG': bbhg_mass_corr,
			'rBC_mass_fg_BBHG_err': bbhg_mass_abs_uncertainty_corr,
			'rBC_mass_fg_BBLG': None,
			'rBC_mass_fg_BBLG_err': None,
			'HK_id': housekeeping_id,		
			}
			
			
			multiple_records.append((single_record))

			#bulk insert to db table
			if i%5000 == 0:
				cursor.executemany(add_data, multiple_records)
				cnx.commit()
				multiple_records = []


			prev_particle_ts = event_time
			
			#increment count of detectible incandescent particles
			i+= 1
			
		record_index+=1   
		
	#bulk insert of remaining records to db
	if multiple_records != []:
		cursor.executemany(add_data, multiple_records)
		cnx.commit()
		multiple_records = []
		
	#close file
	f.close()
	return prev_particle_ts



prev_event_ts = 0
os.chdir(data_dir)
for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
		parameters['folder']= directory
		folder_date = datetime.strptime(directory, '%Y%m%d')		
		if folder_date >= start_analysis_at and folder_date < end_analysis_at:
			parameters['directory']=os.path.abspath(directory)
			os.chdir(parameters['directory'])
			
			#start the fitting
			
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False):
					print file
					parameters['file'] = file
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					parameters['record_size'] = record_size_bytes  
					parameters['number_of_records']= (file_bytes/parameters['record_size'])
					
					prev_event_ts = getParticleData(parameters,SP2_number,min_incand_BBHG,prev_event_ts,max_incand_BBHG)
					
			os.chdir(data_dir)
cnx.close()	



	
