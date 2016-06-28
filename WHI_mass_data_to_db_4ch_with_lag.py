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
data_dir = 'D:/2012/WHI_UBCSP2/Binary/'
start_analysis_at = datetime(2012,5,29)
end_analysis_at = 	datetime(2012,6,1)
SP2_number = 'UBCSP2'
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

add_data = ('''INSERT INTO whi_sp2_particle_data							  
		  (sp2b_file, 
		  file_index, 
		  instrument_ID, 
		  UNIX_UTC_ts_int_start,
		  UNIX_UTC_ts_int_end,
		  BB_incand_HG,
		  NB_incand_HG,
		  rBC_mass_fg_BBHG,
		  rBC_mass_fg_BBHG_err,
		  BB_incand_pk_pos,
		  BB_scat_pk_pos,
		  BB_scat_pkht,
		  HK_id)
		  VALUES (
		  %(sp2b_file)s,
		  %(file_index)s,
		  %(instrument_ID)s,
		  %(UNIX_UTC_ts_int_start)s,
		  %(UNIX_UTC_ts_int_end)s,
		  %(BB_incand_HG)s,
		  %(NB_incand_HG)s,
		  %(rBC_mass_fg_BBHG)s,
		  %(rBC_mass_fg_BBHG_err)s,
		  %(BB_incand_pk_pos)s,
		  %(BB_scat_pk_pos)s,
		  %(BB_scat_pkht)s,
		  %(HK_id)s)''')
		

def checkHKId(particle_event_time):
	event_minute = int(particle_event_time-particle_event_time%60)  #hk data is in 1min intervals, so need event minute
	cursor.execute(('SELECT id FROM whi_hk_data WHERE UNIX_UTC_ts = %s and id > %s'),(event_minute,1))
	hk_data = cursor.fetchall()
	if hk_data != []:
		hk_id= hk_data[0][0]
	else:
		hk_id = None
		
	return hk_id
	
def make_plot(record):
	center = record.beam_center_pos
	x_vals_all = record.getAcqPoints()
	y_vals_all = record.getScatteringSignal()	
	y_vals_split = record.getSplitDetectorSignal()
	y_vals_incand = record.getWidebandIncandSignal()
	

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.plot(x_vals_all,y_vals_all,'o', markerfacecolor='None', label = 'scattering signal')  
	ax1.plot(x_vals_all, y_vals_incand, color ='red',marker = 'o', linestyle = 'None', label = 'incandescent signal')
	ax1.set_xlabel('data point #')
	ax1.set_ylabel('amplitude (a.u.)')

	#ax1.plot(x_vals_all, y_vals_split, 'o', color ='green')
	
	#plt.axvline(x=record.zeroCrossingPos, ymin=0, ymax=1)
	#plt.axvline(x=record.beam_center_pos, ymin=0, ymax=1, color='red')
	plt.legend()
	plt.show()


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
		bbhg_incand_pk_pos = float(particle_record.incandMaxPos)
		
		#if this is an incandescent particle that we can detect with the HG channel then continue 
		if bbhg_incand_pk_amp >= bbhg_incand_min:
			
			#print record_index
			#make_plot(particle_record)
			
			event_time = particle_record.timestamp  #UTC
			
			##Retrieve HK id for the event to join tables on later
			housekeeping_id = checkHKId(event_time)
				
			particle_record.narrowIncandPeakInfo()
			nbhg_incand_pk_amp = float(particle_record.narrowIncandMax)
				
			particle_record.scatteringPeakInfo()
			bbhg_scat_pk_pos = float(particle_record.scatteringMaxPos)
			BB_scat_pkht = float(particle_record.scatteringMax)
		
			####calculate masses
			
			#HG	
			#bbhg_mass_uncorr = 0.01244 + 0.01204*bbhg_incand_pk_amp #ECSP2 2009
			#bbhg_mass_uncertainty_uncorr = 0.14983 + 2.58886E-4*bbhg_incand_pk_amp #ECSP2 2009
			
			#bbhg_mass_uncorr = -0.32619 + 0.00757*bbhg_incand_pk_amp #ECSP2 2010 - lin
			#bbhg_mass_uncertainty_uncorr = 0.16465 + 1.53954E-4*bbhg_incand_pk_amp #ECSP2 2010 - lin
			
			#bbhg_mass_uncorr = 0.12998 + 0.006137*bbhg_incand_pk_amp + 6.1825e-7*bbhg_incand_pk_amp*bbhg_incand_pk_amp #ECSP2 2010 - poly
			#bbhg_mass_uncertainty_uncorr = 0.05224 + 1.15458E-4*bbhg_incand_pk_amp + 4.73331E-8*bbhg_incand_pk_amp*bbhg_incand_pk_amp #ECSP2 2010 - poly
			
			bbhg_mass_uncorr =  0.24826 + 0.00213*bbhg_incand_pk_amp #UBCSP2 2012 - lin
			bbhg_mass_uncertainty_uncorr = 0.05668 + 4.11581E-5*bbhg_incand_pk_amp #UBCSP2 2012 - lin
			
			bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
			bbhg_mass_only_rel_err = bbhg_mass_uncertainty_uncorr/bbhg_mass_uncorr
			bbhg_ADcorr_rel_err = (0.05/0.7)
			bbhg_mass_abs_uncertainty_corr = (bbhg_ADcorr_rel_err + bbhg_mass_only_rel_err) * bbhg_mass_corr
					
		
			
			single_record ={
			'sp2b_file' : parameters['file'],
			'file_index' : record_index,
			'instrument_ID' :instr_number,
			'UNIX_UTC_ts_int_start' :prev_particle_ts,
			'UNIX_UTC_ts_int_end' :event_time,
			'BB_incand_HG': bbhg_incand_pk_amp,
			'NB_incand_HG' : nbhg_incand_pk_amp, 
			'rBC_mass_fg_BBHG': bbhg_mass_corr,
			'rBC_mass_fg_BBHG_err': bbhg_mass_abs_uncertainty_corr,
			'BB_incand_pk_pos': bbhg_incand_pk_pos,
			'BB_scat_pk_pos': bbhg_scat_pk_pos,
			'BB_scat_pkht': BB_scat_pkht,
			'HK_id': housekeeping_id,		
			}
			
			
			multiple_records.append((single_record))
			#bulk insert to db table
			
			if i%2000 == 0:
				print '1',datetime.now()
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
			print folder_date
			#start the fitting
			
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False):
					print file
					parameters['file'] = file
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					parameters['record_size'] = record_size_bytes  
					parameters['number_of_records']= (file_bytes/parameters['record_size'])
					print '1',datetime.now()
					prev_event_ts = getParticleData(parameters,SP2_number,min_incand_BBHG,prev_event_ts,max_incand_BBHG)
					print '2',datetime.now()
			os.chdir(data_dir)
cnx.close()	



	
