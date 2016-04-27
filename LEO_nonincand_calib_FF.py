#this script is used to fit the full SP2 scattering signal of real particles 
#when run for non-incandescent reals this gives a set of data that can be used to set the fixed LEO fit parameters (width and centre position) over time

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

#setup
data_dir = 'F:/Alert/2013/SP2B_files/'
start_analysis_at = datetime(2013,9,27)
end_analysis_at = 	datetime(2014,1,1)
show_full_fit = False
SP2_number = 58
zeroX_evap_threshold = 2000
record_size_bytes = 1658 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458, Alert SP2 #4 and #58 = 832? )
hk_dict = {
'yag_min':4,
'yag_max':6,
'sample_flow_min':118.5,
'sample_flow_max':121.5,
'sheath_flow_min':992,
'sheath_flow_max':1006,
}


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#**********parameters dictionary**********
parameters = {
'acq_rate': 2500000, #5000000,
}


def make_plot(record):
	x_vals = record.getAcqPoints()
	y_vals = record.getScatteringSignal()
	fit_result = record.FF_results
	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.plot(x_vals,y_vals,'o', markerfacecolor='None')   
	ax1.plot(x_vals,fit_result, 'red')
	ax1.plot(record.LF_x_vals_to_use,record.LF_y_vals_to_use, color = 'black',linewidth=3)
	ax1.plot(record.getAcqPoints(), record.getSplitDetectorSignal(), 'o', color ='green')
	plt.axvline(x=record.zeroCrossingPos, ymin=0, ymax=1)
	plt.axvline(x=record.beam_center_pos, ymin=0, ymax=1, color='red')
	plt.show()

def find_nearest(array,value):   #get index of value in array closest to value
	idx = (np.abs(array-value)).argmin()
	return idx
	
	
def gaussFullFit(file,parameters_dict,particle_record_size,show_fit,file_interval,number_of_records,evap_threshold,hk_dictionary,instr_number):
		#pararmeters used to reject invalid particle records based on scattering peak attributes
		min_peakheight = 1000
		max_peakheight = 60000
		min_peakpos = 20
		max_peakpos = 80
		max_incand = 35
		type_particle = 'nonincand'
		
		
		f = open(file, 'rb')
		record_index = 0      
		while record_index < number_of_records:
			
			record = f.read(particle_record_size)
			
			if record_index == 0 or record_index%file_interval == 0:
				try:
					particle_record = ParticleRecord(record, parameters_dict['acq_rate'])
				except:
					print 'corrupt particle record'
					input("Press Enter to continue...")
					record_index+=1
					continue
				event_time = particle_record.timestamp  #UTC
				
				###### FITTING AND ANALYSIS ########          

				##Check DB here for bad HK parameters and skip 
				event_minute = int(event_time-event_time%60)
				cursor.execute(('SELECT sample_flow, sheath_flow, yag_power FROM alert_hk_data WHERE SP2_ID =%s AND UNIX_UTC_ts = %s'),(instr_number,event_minute))
				hk_data = cursor.fetchall()
				if hk_data != []:
					
					sample_flow = hk_data[0][0]
					sheath_flow = hk_data[0][1]
					yag_power = hk_data[0][2]
					
					if (hk_dictionary['sample_flow_min'] < sample_flow < hk_dictionary['sample_flow_max']) and (hk_dictionary['sheath_flow_min'] < sheath_flow < hk_dictionary['sheath_flow_max']) and (hk_dictionary['yag_min'] < yag_power < hk_dictionary['yag_max']):
						
						#run the scatteringPeakInfo method to retrieve various peak attributes 
						particle_record.scatteringPeakInfo()
						actual_scat_signal = particle_record.getScatteringSignal()
						scattering_baseline = particle_record.scatteringBaseline
						actual_max_value = particle_record.scatteringMax
						actual_max_pos = particle_record.scatteringMaxPos
						
						#run the incandPeakInfo method to retrieve peak height
						particle_record.incandPeakInfo()
						incand_max = particle_record.incandMax
						

						#check to see if incandescence is negligible, scattering signal is over threshold, is in a reasonable position, and no double peaks
						if incand_max < max_incand and actual_max_value > min_peakheight and actual_max_value < max_peakheight and actual_max_pos > min_peakpos and actual_max_pos < max_peakpos:
							
							#check zero crossing posn
							#note: zero-crossing calc will depend on the slope of the zero-crossing from the split detector
							zero_crossing_pt = particle_record.zeroCrossingNegSlope(evap_threshold)
							if zero_crossing_pt > 0: 
							
								#check for a double peak
								try:
									particle_record.isSingleParticle()
								except:
									print record_index
									print actual_max_value
									
								if particle_record.doublePeak==False:
								
									particle_record.fullGaussFit()
																								
									fit_peak_pos = particle_record.FF_peak_pos
									fit_width = particle_record.FF_width
									fit_scattering_amp = particle_record.FF_scattering_amp
									zero_cross_to_peak = (zero_crossing_pt - fit_peak_pos)
									
									add_data = ('INSERT INTO alert_leo_params_from_nonincands'							  
									  '(UNIX_UTC_ts, sp2b_file, file_index, instrument_ID, particle_type, actual_scat_amp,FF_scat_amp,FF_peak_posn,FF_gauss_width,actual_zero_x_posn)'
									  'VALUES (%(UNIX_UTC_ts)s,%(sp2b_file)s,%(file_index)s,%(instrument_ID)s,%(particle_type)s,%(actual_scat_amp)s,%(FF_scat_amp)s,%(FF_peak_posn)s,%(FF_gauss_width)s,%(actual_zero_x_posn)s)')
									
									data ={
									'UNIX_UTC_ts' :event_time,
									'sp2b_file' : file,
									'file_index' : record_index,
									'instrument_ID' :instr_number,
									'particle_type' :type_particle, 
									'actual_scat_amp' : float(actual_max_value), 
									'FF_scat_amp' : float(fit_scattering_amp),
									'FF_peak_posn' :    float(fit_peak_pos),
									'FF_gauss_width':   float(fit_width),
									'actual_zero_x_posn': float(zero_crossing_pt),
									}
									
									if np.isnan(np.sum([actual_max_value,fit_scattering_amp,fit_peak_pos,fit_width,zero_crossing_pt])) == False: #check for any nans
										cursor.execute('DELETE FROM alert_leo_params_from_nonincands WHERE UNIX_UTC_ts = %s AND id >= %s',(data['UNIX_UTC_ts'],0))
										cursor.execute(add_data, data)
										cnx.commit()
									
									#plot particle fit if desired
									if show_full_fit == True:
										print record_index, fit_width, zero_cross_to_peak			
										print data['actual_scat_amp'],fit_scattering_amp, fit_peak_pos
										print '\n'
										make_plot(particle_record)
					#			else:
					#				print 'double_peak'
					#				print '\n'
					#				#make_plot(particle_record)
					#		else:
					#			print 'zero-x ', zero_crossing_pt
					#			print '\n'
					#			#make_plot(particle_record)
					#	else:
					#		print record_index, 'incand ', incand_max, 'scat_max ', actual_max_value, 'scat_pos ', actual_max_pos
					#		print '\n'
					#		#make_plot(particle_record)
							
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
			
			number_of_sp2b_files = len([name for name in os.listdir('.') if (name.endswith('.sp2b') and name.endswith('gnd.sp2b') == False)])
			file_interval = number_of_sp2b_files*2
			print file_interval
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False):
					print file			
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					record_size = record_size_bytes  
					number_of_records = (file_bytes/record_size)-1
					gaussFullFit(file,parameters,record_size,show_full_fit,file_interval,number_of_records,zeroX_evap_threshold,hk_dict,SP2_number)
			os.chdir(data_dir)
cnx.close()	



	
