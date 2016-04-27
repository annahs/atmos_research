#this script is used to fit the leading edge SP2 scattering signal of real particles 


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
start_analysis_at = datetime(2013,9,27)
end_analysis_at = 	datetime(2014,1,1)
show_leo_fit = False
leo_fit_factor = 15
fit_bump = 4
zeroX_evap_threshold = 2000
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

def getNonincandCalibData(date,fit_factor):
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
	ratio_pk_adjusted = ratio_pk+record.LF_baseline
	center = record.beam_center_pos
	x_vals_all = record.getAcqPoints()
	y_vals_all = record.getScatteringSignal()	
	y_vals_split = record.getSplitDetectorSignal()
	fit_result = record.LF_results		

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.plot(x_vals_all,y_vals_all,'o', markerfacecolor='None')  
	ax1.plot(center,ratio_pk_adjusted,'o')  
	try:
		ax1.plot(x_vals_all,fit_result, 'blue')
	except:
		print 'no fit result'
	ax1.plot(record.LF_x_vals_to_use,record.LF_y_vals_to_use, color = 'black',linewidth=3)
	ax1.plot(x_vals_all, y_vals_split, 'o', color ='green')
	plt.axvline(x=record.zeroCrossingPos, ymin=0, ymax=1)
	plt.axvline(x=record.beam_center_pos, ymin=0, ymax=1, color='red')
	plt.show()
	
	
	
def gaussLeoFit(file,parameters_dict,particle_record_size,show_fit,number_of_records,calib_list,evap_threshold,fit_factor,FF_bump):
		
		f = open(file, 'rb')
		record_index = 0      
		
				
		while record_index < number_of_records:
			record = f.read(particle_record_size)
			#check if we've done a full fit on this particle
			cursor.execute(('SELECT id, UNIX_UTC_ts FROM alert_leo_params_from_nonincands WHERE sp2b_file =%s AND file_index = %s'),(file,record_index))
			nonincand_data = cursor.fetchall()
			
			
			#if we have, try a leo fit so we can compare them
			if nonincand_data != []:
				particle_id = nonincand_data[0][0]
				particle_timestamp = nonincand_data[0][1]
				try:
					particle_record = ParticleRecord(record, parameters_dict['acq_rate'])
				except:
					print 'corrupt particle record'
					input("Press Enter to continue...")
					record_index+=1
					continue
				
				event_time = particle_record.timestamp  #UTC
				#check the timestamps
				if particle_timestamp != event_time:
					print record_index, 'timestamp mismatch! ', 'DB: ', particle_timestamp, ' record: ',event_time
					input("Press Enter to continue...")
					record_index+=1
					continue
				
				###### FITTING AND ANALYSIS ########          
				#get calib parameters
				zeroX_to_LEO_limit = calib_list[0]
				mean_zeroX_to_peak = calib_list[1]
				mean_calib_fit_width = calib_list [2]
				particle_record.scatteringPeakInfo()
				scat_pk_amp = particle_record.scatteringMax
				zero_crossing_pt = particle_record.zeroCrossingNegSlope(evap_threshold)
				
				particle_record.leoGaussFit(zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_calib_fit_width,evap_threshold,zero_crossing_pt)
																			
				LF_scattering_amp = particle_record.LF_scattering_amp
				try:
					ratio_method_pk = float((particle_record.LF_y_vals_to_use[-1]-particle_record.LF_baseline)*(fit_factor+FF_bump))
				except:
					ratio_method_pk = None
				
				cursor.execute('UPDATE alert_leo_params_from_nonincands SET LF_scat_amp=%s WHERE id = %s',(float(LF_scattering_amp),particle_id))
				cursor.execute('UPDATE alert_leo_params_from_nonincands SET LF_ratio_scat_amp=%s WHERE id = %s',(ratio_method_pk,particle_id))
				cnx.commit()
				
				
				#plot particle fit if desired
				if show_fit == True:			
					print record_index
					print 'ratio_method_pk:',ratio_method_pk, 'LF:',LF_scattering_amp
					print '\n'
					make_plot(particle_record,ratio_method_pk)
					

							
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
			
			calib_list = getNonincandCalibData(UNIX_date,leo_fit_factor)
			if calib_list == None:  #skip empty folder
				os.chdir(data_dir)
				continue
				
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False):
					print file			
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					record_size = record_size_bytes  
					number_of_records = (file_bytes/record_size)-1
					gaussLeoFit(file,parameters,record_size,show_leo_fit,number_of_records,calib_list,zeroX_evap_threshold,leo_fit_factor,fit_bump)
			os.chdir(data_dir)
cnx.close()	



	
