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
data_dir = 'F:/Alert/2013/SP2B_files/'
start_analysis_at = datetime(2013,12,27)
end_analysis_at = 	datetime(2014,1,1)
SP2_number = 58
zeroX_evap_threshold = 2000
min_incand = 50
hk_dict = {
'yag_min':4,
'yag_max':6,
'sample_flow_min':118.5,
'sample_flow_max':121.5,
'sheath_flow_min':992,
'sheath_flow_max':1006,
}
show_leo_fit = False
fit_factor = 15  #inverse fraction of signal to fit
fit_factor_ratio_bump = 4
 
record_size_bytes = 1658 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458, Alert SP2 #4 and #58 = 832? )

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#**********parameters dictionary**********
parameters = {
'acq_rate': 2500000, #5000000,
}

def find_nearest(array,value):   #get index of value in array closest to value
	idx = (np.abs(array-value)).argmin()
	return idx

def getNonincandCalibData(date, leo_fit_factor):
	FF = 0 #fudge factor for fit_width
	cursor.execute(('SELECT AVG(FF_gauss_width), AVG(FF_peak_posn), AVG(actual_zero_x_posn) FROM alert_leo_params_from_nonincands where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),
	(date,date+86400))	#all calib points from that day
	calib_data = cursor.fetchall()
	if calib_data == [(None,None,None)]:
		return None
	mean_calib_fit_width = calib_data[0][0]+FF
	mean_peak_pos = calib_data[0][1]
	mean_zero_x_posn = calib_data[0][2]
	mean_zeroX_to_peak = mean_zero_x_posn-mean_peak_pos
	
	#calculate half-width at x% point (eg 5% for factor 20)  
	HWxM = math.sqrt(2*math.log(fit_factor))*(mean_calib_fit_width-FF)
	mean_zeroX_to_LEO_limit = HWxM + mean_zeroX_to_peak
	print mean_zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_calib_fit_width
	return [mean_zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_calib_fit_width]

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
	
def gaussLeoFit(parameters_dict,show_fit,calib_list,leo_fit_factor,instr_number,HK_dict,evap_threshold,bb_incand_min,FF_bump):
	
	f = open(parameters_dict['file'], 'rb')
	record_index = 0      
	
	while record_index < parameters['number_of_records']:
		
		#read the binary for a particle
		record = f.read(parameters['record_size'])	
		particle_record = ParticleRecord(record, parameters_dict['acq_rate'])
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
				zero_crossing_pt = float(particle_record.zeroCrossingNegSlope(evap_threshold))

				#run the narrowband incandPeakInfo method to retrieve various narrowband incandescence peak attributes	
				particle_record.narrowIncandPeakInfo() 			
				nb_incand_pk_amp = float(particle_record.narrowIncandMax)				
				
				#get calib parameters
				zeroX_to_LEO_limit = calib_list[0]
				mean_zeroX_to_peak = calib_list[1]
				mean_calib_fit_width = calib_list[2]
				zero_crossing_pt_L = particle_record.zeroCrossingNegSlope(evap_threshold)
				
				particle_record.leoGaussFit(zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_calib_fit_width,evap_threshold,zero_crossing_pt_L)

				LF_scattering_amp = float(particle_record.LF_scattering_amp)
				
				if particle_record.LF_y_vals_to_use != []:
					ratio_method_pk = float((particle_record.LF_y_vals_to_use[-1]-particle_record.scatteringBaseline)*(leo_fit_factor+FF_bump))
				
				#plot particle fit if desired
				if show_leo_fit == True:
					print record_index			
					print 'LF: ',LF_scattering_amp, 'Ratio: ',ratio_method_pk
					print '\n'
					make_plot(particle_record,ratio_method_pk)
				

				
			#put data into database
			add_data = ('INSERT INTO alert_leo_coating_data'							  
			  '(UNIX_UTC_ts, sp2b_file, file_index, instrument_ID, BB_incand,NB_incand,actual_scat_amp,LF_scat_amp,LF_ratio_scat_amp,actual_zero_x_posn,HK_flag,rBC_mass_fg,coat_thickness_nm)'
			  'VALUES (%(UNIX_UTC_ts)s,%(sp2b_file)s,%(file_index)s,%(instrument_ID)s,%(BB_incand)s,%(NB_incand)s,%(actual_scat_amp)s,%(LF_scat_amp)s,%(LF_ratio_scat_amp)s,%(actual_zero_x_posn)s,%(HK_flag)s,%(rBC_mass_fg)s,%(coat_thickness_nm)s)')

			data ={
			'UNIX_UTC_ts' :event_time,
			'sp2b_file' : parameters['file'],
			'file_index' : record_index,
			'instrument_ID' :instr_number,
			'BB_incand': bb_incand_pk_amp,
			'NB_incand': nb_incand_pk_amp,
			'actual_scat_amp' : scat_pk_amp, 
			'LF_scat_amp' : LF_scattering_amp,
			'LF_ratio_scat_amp': ratio_method_pk,
			'actual_zero_x_posn': zero_crossing_pt,
			'HK_flag': housekeeping_flag,		
			'rBC_mass_fg': rBC_mass,
			'coat_thickness_nm': coat_th,
			}
			
			#cursor.execute('DELETE FROM alert_leo_coating_data WHERE UNIX_UTC_ts = %s AND instrument_ID >= %s',(data['UNIX_UTC_ts'],data['instrument_ID']))
			cursor.execute(add_data, data)
			cnx.commit()
					
		record_index+=1   
			
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
			
			#get the calibration fitting parameters
			calib_list = getNonincandCalibData(UNIX_date,fit_factor)
			if calib_list == None:  #skip empty folder, no calib data == no incandescent data
				os.chdir(data_dir)
				continue
				
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
					gaussLeoFit(parameters,show_leo_fit,calib_list,fit_factor,SP2_number,hk_dict,zeroX_evap_threshold,min_incand,fit_factor_ratio_bump)
			os.chdir(data_dir)
cnx.close()	



	
