#This script is for doing the leading edge fit on SP2 scattering signals 
#If run on non-incandescent particles, it can be used to check the performance of the LEO procedure (by plotting actual or FF scat amp vs LF scat amp)
#When run on incandescent particle it is used to recover the unperturbed peak scattering signal for coating determination
#The LEO_calibration_FF must be run before running this script to provide fixed fitting parameters for the appropriate instrument and time period ( beam width and center etc)

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
from datetime import datetime
from datetime import timedelta
import calendar



#analysis parameters
data_dir = data_dir = 'D:/2015/NETCARE_UBC_SP2/flight data/'#'D:/2012/WHI_UBCSP2/Binary/' #'D:/2012/WHI_UBCSP2/Binary/' #'D:/2009/WHI_ECSP2/Binary/'# 'D:/2010/WHI_ECSP2/Binary/'  #'D:/2012/WHI_UBCSP2/Binary/' 
instrument = 'UBCSP2'
instrument_locn = 'POLAR6'
type_particle = 'nonincand' #PSL, nonincand, incand
start_analysis_at = datetime.strptime('20150405','%Y%m%d')
end_analysis_at = datetime.strptime('20150406','%Y%m%d')
analysis_time_start = 0  #use this to retrict analsyis to a particular time of day
analysis_time_end = 24
num_records_to_analyse = 1000#'all'
fit_function = 'Giddings' #Gauss or Giddings
show_LEO_fit = False
FF = 0 #fudge factor for fit_width

#parameters for setting values of fixed variables in fitting
calib_instrument = 'UBCSP2'
calib_instrument_locn = 'POLAR6'
calib_type_particle = 'nonincand'
calib_time_span = 1800 #in secs  #the program will select calibration data from +- this time period surrounding the data being LEO fitted


#pararmeters used to reject invalid particle records based on scattering peak attributes
min_peakheight = 6
max_peakheight = 3700
min_peakpos = 20 #50 for 2010
max_peakpos = 125 #250 for 2010

#pararmeters used to assess incandescent peak
min_incand_amp = 20

record_size_bytes = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)

#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()


#**********parameters dictionary**********
parameters = {
'acq_rate': 5000000,
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
#show plots?
'show_plot':False,
}


def gaussLEOFit(parameters_dict):
	print parameters['folder']

	
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
			f2 = open(file, 'rb')			
			
			path = parameters['directory'] + '/' + str(file)
			file_bytes = os.path.getsize(path) #size of entire file in bytes
			record_size = record_size_bytes
			number_of_records = (file_bytes/record_size)-1
			if num_records_to_analyse == 'all':
				number_records_toshow =  number_of_records 
			else:
				number_records_toshow = num_records_to_analyse    

			#grab the pickled bad_durations file generated by the HK analysis
			for hk_file in os.listdir('.'):
				if hk_file.endswith('.hkpckl'):
					hk_data = open(hk_file, 'r')
					bad_durations = pickle.load(hk_data)
					hk_data.close()
		
			
			## fitting scattering signals to get info for LEO fits
			record_index = 0
			while record_index < number_records_toshow:
				
				##Import and parse binary
				record = f2.read(record_size)
				particle_record = ParticleRecord(record, parameters['acq_rate'])	
				event_time = particle_record.timestamp #UNIXts in UTC
				
				#**********get LEO calib parameters from nonincand reals
				
				if (record_index % 100) == 0 or record_index == 0:
					time_span = calib_time_span #in secs
					begin_calib_data = event_time-time_span
					end_calib_data = event_time+time_span
					#get parameters for fixing variables in Gaussian fitting
					c.execute('''SELECT FF_gauss_width, zeroX_to_peak, zeroX_to_LEO_limit FROM SP2_coating_analysis 
					WHERE instr=? and instr_locn=? and particle_type=? and unix_ts_utc>=? and unix_ts_utc<? and FF_fit_function=? and FF_gauss_width is not null and zeroX_to_peak is not null''', 
					(calib_instrument,calib_instrument_locn,calib_type_particle, begin_calib_data, end_calib_data,fit_function))
					result = c.fetchall()
					
					mean_calib_fit_width = np.nanmean([row[0] for row in result])+FF
					mean_zeroX_to_peak = np.nanmean([row[1] for row in result]) 
					mean_zeroX_to_LEO_limit = np.nanmean([row[2] for row in result]) 
					#print 'number of calib particles = ',len(result)

				#******
				
				
											
				#if there are any bad hk durations, note the beginning and end times of the first one
				number_bad_durations = len(bad_durations)
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
					
					#get the zero-crossing with the appropriate method
					zero_crossing_pt = particle_record.zeroCrossing()
					analyze_this_particle = False
					
					#for calibration purposes we only grab files where we had a successful fullGauss fit 
					if type_particle == 'nonincand':
						c.execute('''SELECT * FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=? and sp2b_file=? and file_index=?''', 
						(instrument,instrument_locn,type_particle, file, record_index))
						result = c.fetchone()
						if result is not None:
							analyze_this_particle = True
							
					#for looking at incandescent particles we will try a LEO fit if scattering and incandescent peaks high enough
					if type_particle == 'incand':
						
						particle_record.incandPeakInfo() #run the incandPeakInfo method to retrieve various incandescence peak attributes				
						incand_pk_amp = particle_record.incandMax					
						incand_pk_pos = particle_record.incandMaxPos
						scat_pk_pos = particle_record.scatteringMaxPos
						 
						
						if incand_pk_amp > min_incand_amp:

							scattering_pk_amp = particle_record.scatteringMax
							lag_time_pts = incand_pk_pos-scat_pk_pos
		
							c.execute('''INSERT or IGNORE into SP2_coating_analysis (sp2b_file, file_index, instr) VALUES (?,?,?)''', 
								(file, record_index,instrument))
							c.execute('''UPDATE SP2_coating_analysis SET 
							instr_locn=?,
							particle_type=?,
							unix_ts_utc=?, 
							actual_scat_amp=?, 
							incand_amp=?,
							lag_time_fit_to_incand=?,	
							zero_crossing_posn=?
							WHERE sp2b_file=? and file_index=? and instr=?''', 
							(instrument_locn,
							type_particle,
							event_time,
							scattering_pk_amp,
							incand_pk_amp,
							lag_time_pts,
							zero_crossing_pt,
							file, record_index,instrument))
						
						if incand_pk_amp > min_incand_amp and scattering_pk_amp < min_peakheight:	
							c.execute('''UPDATE SP2_coating_analysis SET 
							LF_scat_amp=?
							WHERE sp2b_file=? and file_index=? and instr=?''', 
							(0.0,
							file, record_index, instrument))
						
						if incand_pk_amp > min_incand_amp and scattering_pk_amp >= min_peakheight:	
							analyze_this_particle = True
					
					
					if analyze_this_particle == True:
						
						if fit_function == 'Giddings':
							particle_record.leoGiddingsFit(mean_zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_calib_fit_width)
							
						if fit_function == 'Gauss':
							particle_record.leoGaussFit(mean_zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_calib_fit_width)
											
						LEO_max_fit_index = particle_record.LF_max_index
						LEO_amp = particle_record.LF_scattering_amp	 #this will be -1 if the fitting failed, will be -2 if zero-crossing couldn't be found
						LEO_baseline = particle_record.LF_baseline #this will be -1 if the fitting failed, will be -2 if zero-crossing couldn't be found
						actual_baseline = particle_record.scatteringBaseline
						LF_percent_diff_baseline = np.absolute((LEO_baseline-actual_baseline)/(0.5*LEO_baseline+0.5*actual_baseline))
						
						if LEO_max_fit_index < 20 or LEO_max_fit_index > max_peakpos: #error locating LEO fitting index
							LEO_amp = -3  #-2 in these values indicates a failure in the initial look for a zero-crossing, -3 indicates outside the range set here
							LEO_baseline = -3
						if LEO_amp < 0:
							LEO_amp = None
						c.execute('''UPDATE SP2_coating_analysis SET 
							LF_scat_amp=?,
							LF_baseline_pct_diff=?,
							zero_crossing_posn=?,
							LF_fit_function=?
							WHERE sp2b_file=? and file_index=? and instr=?''',
							(LEO_amp,
							LF_percent_diff_baseline,
							zero_crossing_pt,
							fit_function,
							file,record_index,instrument))
						#plot particle fit if desired				
						if show_LEO_fit == True:# and incand_pk_amp > min_incand_amp:
						
							x_vals_all = particle_record.getAcqPoints()
							y_vals_all = particle_record.getScatteringSignal()	
							y_vals_split = particle_record.getSplitDetectorSignal()
							y_vals_incand = particle_record.getWidebandIncandSignal()
							fit_result = particle_record.LF_results		
												
							print file, 'record: ',record_index, LEO_amp
							fig = plt.figure()
							ax1 = fig.add_subplot(111)
							ax1.plot(x_vals_all,y_vals_all,'o', markerfacecolor='None')  
							try:
								ax1.plot(x_vals_all,fit_result, 'blue')
							except:
								print 'no fit result'
							ax1.plot(particle_record.LF_x_vals_to_use,particle_record.LF_y_vals_to_use, color = 'black',linewidth=3)
							#ax1.plot(x_vals_all, y_vals_split, 'o', color ='green')
							ax1.plot(x_vals_all, y_vals_incand, color ='red')
							plt.axvline(x=zero_crossing_pt, ymin=0, ymax=1)
							plt.axvline(x=particle_record.beam_center_pos, ymin=0, ymax=1, color='red')
							plt.show()

							
				record_index+=1    
			f2.close()        
		conn.commit()

os.chdir(data_dir)
for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
		parameters['folder']= directory
		folder_date = datetime.strptime(directory, '%Y%m%d')		
		if folder_date >= start_analysis_at and folder_date < end_analysis_at:
			parameters['directory']=os.path.abspath(directory)
			os.chdir(parameters['directory'])
			gaussLEOFit(parameters)
			os.chdir(data_dir)
conn.close()	




