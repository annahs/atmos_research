#this script is used to do a full fit (Gauss or other) on PSL signals from the SP2
#this can be used to calibrate the instrument's scattering response to the Mie calculated scattering of a PSL
#in reality we can simply use the actual peak scattering amplitude for the calibration, so doing a fit is useful mostly for diagnosing the fitting procedure

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
import sqlite3



current_dir = 'D:/2015/NETCARE_UBC_SP2/calibration data/20150129/PSL240/'
#current_dir = 'D:/2012/WHI_UBCSP2/Calibrations/20120328/PSL/Binary/200nm/'
instrument = 'UBCSP2'
instrument_locn = 'POLAR6'
PSL_size = 240
type_particle = 'PSL'
os.chdir(current_dir)

#setup
num_records_to_analyse = 'all'
show_full_fit = True

#pararmeters used to reject invalid particle records based on scattering peak attributes
min_peakheight = 10
max_peakheight = 4000
min_peakpos = 20
max_peakpos = 125



#**********parameters dictionary**********

parameters = {
'acq_rate': 5000000,
#file i/o
'directory':current_dir,
#date and time
'timezone':-8,
#will be set by hk analysis
'avg_flow':120, #in vccm
#parameter to find bad flow durations
'flow_min' : 115,
'flow_max' : 125,
'YAG_min' : 4,
'YAG_max' : 6,
'min_good_points' : 10,
#show hk plots?
'show_plot':True,
}
parameters ['folder'] = '20150129'

#setup database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()


#sp2b_file TEXT, 			eg 20120405x001.sp2b
#file_index INT, 			
#instr TEXT,				eg UBCSP2, ECSP2
#instr_locn TEXT,			eg WHI, DMT, POLAR6
#particle_type TEXT,		eg PSL, nonincand, incand, Aquadag
#particle_dia FLOAT,				
#unix_ts_utc FLOAT,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#LF_scat_amp FLOAT,
#incand_amp FLOAT,
#lag_time_fit_to_incand FLOAT,
#LF_baseline_pct_diff FLOAT,
#rBC_mass_fg FLOAT,
#coat_thickness_nm FLOAT,
#zero_crossing_posn FLOAT,
#coat_thickness_from_actual_scat_amp FLOAT,
#FF_fit_function TEXT,
#LF_fit_function TEXT,
#zeroX_to_LEO_limit FLOAT
#UNIQUE (sp2b_file, file_index, instr)
#)''')



#*******HK ANALYSIS************ 

#####comment this out if it's been run once
	
###use for hk files with no timestamp (just time since midnight) (this should work for the EC polar flights in spring 2012,also for ECSP2 for WHI 20100610 to 20100026, UBCSP2 prior to 20120405)
#avg_flow = hk_new_no_ts_LEO.find_bad_hk_durations_no_ts(parameters) 
#parameters['avg_flow'] = avg_flow
#bad_durations = []

###use for hk files with timestamp (this is for the UBCSP2 after 20120405)
#avg_flow = hk_new.find_bad_hk_durations(parameters)
#parameters['avg_flow'] = avg_flow


#*************LEO routine************
for file in os.listdir('.'):
	
	if file.endswith('.sp2b'):
		
		print file
		
		path = current_dir + str(file)
		file_bytes = os.path.getsize(path) #size of entire file in bytes
		record_size = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)
		number_of_records = (file_bytes/record_size)-1
		if num_records_to_analyse == 'all':
			number_records_toshow =  number_of_records 
		else:
			number_records_toshow = num_records_to_analyse    
		
		##************This is the full-gauss prefit************
		
		f = open(file, 'rb')
		
		#grab the pickled bad_durations file generated by the HK analysis
		for hk_file in os.listdir('.'):
			if hk_file.endswith('.hkpckl'):
				hk_data = open(hk_file, 'r')
				bad_durations = pickle.load(hk_data)
				hk_data.close()
	
		record_index = 0      
		
		while record_index < number_records_toshow:
			
			##Import and parse binary
			record = f.read(record_size)
			particle_record = ParticleRecord(record, parameters['acq_rate'])	
			event_time = particle_record.timestamp
			
			###### FITTING AND ANALYSIS ########          
			number_bad_durations = len(bad_durations)
			
							
			#if there are any bad hk durations, note the beginning and end times of the first one
			if number_bad_durations:               
				bad_duration_start_time = bad_durations[0][0]
				bad_duration_end_time = bad_durations[0][1]
			
				#if the current event is after the end of the first bad duration in the list, pop that duration off, repeat if necessary until all bad durations before the event are gone
				while event_time >= bad_duration_end_time:
					if len(bad_durations): 
						bad_durations.pop(0)
						if len(bad_durations):
							bad_duration_start_time = bad_durations[0][0]
							bad_duration_end_time = bad_durations[0][1]
							continue
						else:
							break
			

			if not number_bad_durations or event_time < bad_duration_start_time:  

				#run the scatteringPeakInfo method to retrieve various peak attributes 
				particle_record.scatteringPeakInfo()		
				actual_max_value = particle_record.scatteringMax
				actual_max_pos = particle_record.scatteringMaxPos
				
				#check for a double peak
				particle_record.isSingleParticle()

				#note: zero-crossing calc will depend on the slope of the zero-crossing from the split detector
				zero_crossing_pt = particle_record.zeroCrossing()
				
				
				#check to see if scattering signal is over threshold, is in a reasonable position, and no double peaks
				if actual_max_value > min_peakheight and actual_max_value < max_peakheight and actual_max_pos > min_peakpos and actual_max_pos < max_peakpos and particle_record.doublePeak==False and zero_crossing_pt > 0 : 
					print record_index
					particle_record.GiddingsFit()
					#particle_record.fullGaussFit()
					
					fit_peak_pos = particle_record.FF_peak_pos
					fit_gauss_width = particle_record.FF_gauss_width
					fit_scattering_amp = particle_record.FF_scattering_amp
					zero_cross_to_peak = (zero_crossing_pt - fit_peak_pos)
					
					#put particle into database or update record
					c.execute('''INSERT or IGNORE into SP2_coating_analysis (sp2b_file, file_index, instr) VALUES (?,?,?)''', (file, record_index,instrument))
					c.execute('''UPDATE SP2_coating_analysis SET 
					instr_locn=?,
					particle_type=?,
					particle_dia=?,
					unix_ts_utc=?, 
					actual_scat_amp=?, 
					actual_peak_pos=?, 
					FF_scat_amp=?, 
					FF_peak_pos=?, 
					FF_gauss_width=?, 
					zeroX_to_peak=?
					WHERE sp2b_file=? and file_index=? and instr=?''', 
					(instrument_locn,
					type_particle,
					PSL_size,
					event_time,
					actual_max_value,
					actual_max_pos,
					fit_scattering_amp,
					fit_peak_pos,
					fit_gauss_width,
					zero_cross_to_peak,
					file, record_index,instrument))
									
					#plot particle fit if desired
					if show_full_fit == True:
						x_vals = particle_record.getAcqPoints()
						y_vals = particle_record.getScatteringSignal()	
						fit_result = particle_record.FF_results
						
						##os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/')
						#file = open('NETCARE POLAR6 2015 Spring PSL data for full gauss fit ' + str(file) + '-' + str(record_index) + '.txt', 'w')
						#file.write('acq_points' + '\t' + 'scattering_signal' + '\t' + 'Full_gauss_fit_result' + '\t' + 'file' + '\t' +'record_index' + '\n')
						#i=0
						#for value in x_vals: 
						#	file.write(str(value) + '\t' + str(y_vals[i]) + '\t' + str(fit_result[i]) + '\n')
						#	i+=1
						#file.close()
						##os.chdir(current_dir)
						
						print record_index, actual_max_value, np.max(fit_result)
						
						fig = plt.figure()
						ax1 = fig.add_subplot(111)
						ax1.plot(x_vals,y_vals,'o', markerfacecolor='None')   
						ax1.plot(x_vals,fit_result, 'red')
						plt.show()

						

			record_index+=1   
				
		f.close()


		
conn.commit()
conn.close()


	
