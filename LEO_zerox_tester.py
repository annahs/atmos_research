#this script is used to fit the leading edge SP2 scattering signal of real incandescent particles 

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
data_dir = 'F:/Alert/2011/SP2B_files/'
start_analysis_at = datetime(2011,3,5)
end_analysis_at = 	datetime(2012,1,1)
show_full_fit = False
SP2_number = 17
zeroX_evap_threshold = 40
min_incand = 500

record_size_bytes = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458, Alert SP2 #44 and #58 = 1658 #17 =1498)
hk_dict = {
'yag_min':4,
'yag_max':7,
'sample_flow_min':118.5,
'sample_flow_max':121.5,
'sheath_flow_min':990,
'sheath_flow_max':1010,
}

show_leo_fit = True
fit_factor = 15  #inverse fraction of signal to fit
fit_factor_ratio_bump = 3
 

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#**********parameters dictionary**********
parameters = {
'acq_rate': 5000000, #5000000,
}

def find_nearest(array,value):   #get index of value in array closest to value
	idx = (np.abs(array-value)).argmin()
	return idx

def make_plot(record,ratio_pk):
	if ratio_pk == None:
		ratio_pk = np.nan
	ratio_pk_adjusted = ratio_pk+record.LF_baseline
	center = record.beam_center_pos
	x_vals_all = record.getAcqPoints()
	y_vals_all = record.getScatteringSignal()	
	y_vals_split = record.getSplitDetectorSignal()
	y_vals_incand = record.getWidebandIncandSignal()
	fit_result = record.LF_results		

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.plot(x_vals_all,y_vals_all,'o', markerfacecolor='None')  
	ax1.plot(center,ratio_pk_adjusted,'o')  
	if fit_result != []:
		ax1.plot(x_vals_all,fit_result, color='blue',marker='o')
	ax1.plot(record.LF_x_vals_to_use,record.LF_y_vals_to_use, color = 'black',linewidth=3)
	ax1.plot(x_vals_all, y_vals_split, 'o', color ='green')
	ax1.plot(x_vals_all, y_vals_incand, color ='red')
	plt.axvline(x=record.zeroCrossingPos, ymin=0, ymax=1)
	plt.axvline(x=record.beam_center_pos, ymin=0, ymax=1, color='red')
	plt.show()

def checkHKDetails(particle_event_time,instr_number,hk_dictionary):
	event_minute = int(particle_event_time-particle_event_time%60)  #hk data is in 1min intervals, so need event minute
	cursor.execute(('SELECT sample_flow, sheath_flow, yag_power FROM alert_hk_data WHERE SP2_ID =%s AND UNIX_UTC_ts = %s'),(instr_number,event_minute))
	hk_data = cursor.fetchall()
	hk_flag = 0
	if hk_data != []:
		sample_flow = hk_data[0][0]
		sheath_flow = hk_data[0][1]
		yag_power = hk_data[0][2]
		if sample_flow < hk_dictionary['sample_flow_min'] or sample_flow > hk_dictionary['sample_flow_max']:
			hk_flag = 1
		if sheath_flow < hk_dictionary['sheath_flow_min'] or sheath_flow > hk_dictionary['sheath_flow_max']: 
			hk_flag = 2
		if yag_power < hk_dictionary['yag_min'] or yag_power > hk_dictionary['yag_max']:
			hk_flag = 3
	else:
		hk_flag = 4
	
	return hk_flag
	
def gaussLeoFit(parameters_dict,show_fit,leo_fit_factor,instr_number,HK_dict,evap_threshold,bb_incand_min,FF_bump):
	
	f = open(parameters_dict['file'], 'rb')
	record_index = 0      
	multiple_records = []
	i=1
	good = 0
	bad = 0
	while record_index < parameters['number_of_records']:
		
		#read the binary for a particle
		record = f.read(parameters['record_size'])	
		try:
			particle_record = ParticleRecord(record, parameters_dict['acq_rate'])
		except:
			print record_index, 'cant read'
			record_index +=1
			continue
		event_time = particle_record.timestamp  #UTC
		
		#run the wideband incandPeakInfo method to retrieve various incandescence peak attributes	
		particle_record.incandPeakInfo() 			
		bb_incand_pk_amp = float(particle_record.incandMax)
		
		#if this is an incandescent particle that we can detect then continue
		if bb_incand_pk_amp >= bb_incand_min:
			
			nb_incand_pk_amp = None
			scat_pk_amp = None
			LF_scattering_amp = None
			ratio_method_pk = None
			zero_crossing_pt = None
			rBC_mass = None
			coat_th = None
			
			##Check DB here for bad HK parameters and only do fitting etc for good hk times
			housekeeping_flag = checkHKDetails(event_time,instr_number,HK_dict)
			if housekeeping_flag == 0:
			
				#run the scatteringPeakInfo method to retrieve various scttering peak attributes
				particle_record.scatteringPeakInfo()
				scat_pk_amp = float(particle_record.scatteringMax)
				scat_pk_pos = particle_record.scatteringMaxPos
				
				#get the zero-crossing 
				try:
					zero_crossing_pt = float(particle_record.zeroCrossingPosSlope(evap_threshold))
				except:
					print record_index, 'cant get zero x'
					record_index +=1
					continue
				if zero_crossing_pt >=0: 
					good +=1 
				if zero_crossing_pt <0:
					bad +=1
		record_index+=1
	print '\n'
	print good, bad
	print good*100./(good+bad)
	f.close()





os.chdir(data_dir)
for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
		parameters['folder']= directory
		folder_date = datetime.strptime(directory, '%Y%m%d')		
		if folder_date >= start_analysis_at and folder_date < end_analysis_at:
			parameters['directory']=os.path.abspath(directory)
			os.chdir(parameters['directory'])
			UNIX_date = calendar.timegm(folder_date.utctimetuple())
						
			#start the fitting
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False):
					print file
					parameters['file'] = file
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					parameters['record_size'] = record_size_bytes  
					parameters['number_of_records']= (file_bytes/parameters['record_size'])-1
					#call fitting functions
					gaussLeoFit(parameters,show_leo_fit,fit_factor,SP2_number,hk_dict,zeroX_evap_threshold,min_incand,fit_factor_ratio_bump)
			os.chdir(data_dir)
cnx.close()	



	
