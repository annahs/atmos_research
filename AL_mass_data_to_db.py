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
data_dir = 'F:/Alert/2015/SP2B_files/'
start_analysis_at = datetime(2015,4,2)
end_analysis_at = 	datetime(2015,6,6)
SP2_number = 58
min_incand_BBHG = 50
max_incand_BBHG = 60000

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
		
			#get incandescent signals
			particle_record.incandPeakInfoLG()
			bblg_incand_pk_amp = float(particle_record.incandMax_LG)
			
			particle_record.narrowIncandPeakInfo()
			nbhg_incand_pk_amp = float(particle_record.narrowIncandMax)
			
			particle_record.narrowIncandPeakInfoLG()
			nblg_incand_pk_amp = float(particle_record.narrowIncandMax_LG)
				
			#calculate masses
			bbhg_mass = 0.41527 + 2.13238E-4*bbhg_incand_pk_amp + 7.17406E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp
			bbhg_mass_uncertainty = 0.07629 + 9.60334E-6*bbhg_incand_pk_amp + 1.96833E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp
			
			bblg_mass = 0.70095 + 0.00182*bblg_incand_pk_amp + 1.22794E-7*bblg_incand_pk_amp*bblg_incand_pk_amp
			bblg_mass_uncertainty = 0.30863 + 1.38156E-4*bblg_incand_pk_amp + 1.17569E-8*bblg_incand_pk_amp*bblg_incand_pk_amp

			add_data = ('INSERT INTO alert_mass_number_data_2015'							  
			  '(sp2b_file, file_index, instrument_ID, UNIX_UTC_ts_int_start,UNIX_UTC_ts_int_end,BB_incand_HG,BB_incand_LG,NB_incand_HG,NB_incand_LG,rBC_mass_fg_BBHG,rBC_mass_fg_BBHG_err,rBC_mass_fg_BBLG,rBC_mass_fg_BBLG_err,HK_id)'
			  'VALUES (%(sp2b_file)s,%(file_index)s,%(instrument_ID)s,%(UNIX_UTC_ts_int_start)s,%(UNIX_UTC_ts_int_end)s,%(BB_incand_HG)s,%(BB_incand_LG)s,%(NB_incand_HG)s,%(NB_incand_LG)s,%(rBC_mass_fg_BBHG)s,%(rBC_mass_fg_BBHG_err)s,%(rBC_mass_fg_BBLG)s,%(rBC_mass_fg_BBLG_err)s,%(HK_id)s)')
			
			
			single_record ={
			'sp2b_file' : parameters['file'],
			'file_index' : record_index,
			'instrument_ID' :instr_number,
			'UNIX_UTC_ts_int_start' :prev_particle_ts,
			'UNIX_UTC_ts_int_end' :event_time,
			'BB_incand_HG': bbhg_incand_pk_amp,
			'BB_incand_LG': bblg_incand_pk_amp,
			'NB_incand_HG' : nbhg_incand_pk_amp, 
			'NB_incand_LG' : nblg_incand_pk_amp,
			'rBC_mass_fg_BBHG': bbhg_mass,
			'rBC_mass_fg_BBHG_err': bbhg_mass_uncertainty,
			'rBC_mass_fg_BBLG': bblg_mass,
			'rBC_mass_fg_BBLG_err': bblg_mass_uncertainty,
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
	cursor.executemany(add_data, multiple_records)
	cnx.commit()
	
	#close file
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
					parameters['number_of_records']= (file_bytes/parameters['record_size'])
					
					prev_event_ts = getParticleData(parameters,SP2_number,min_incand_BBHG,prev_event_ts,max_incand_BBHG)
					
			os.chdir(data_dir)
cnx.close()	



	
