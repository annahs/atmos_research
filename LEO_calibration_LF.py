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
data_dir = 'D:/2012/WHI_UBCSP2/Binary/' #'D:/2009/WHI_ECSP2/Binary/'# 'D:/2010/WHI_ECSP2/Binary/'  #'D:/2012/WHI_UBCSP2/Binary/' 
#analysis_dir = 'D:/2012/WHI_UBCSP2/Calibrations/20120328/PSL/Binary/200nm/'
multiple_directories = True
num_records_to_analyse = 'all'
LEO_factor = 16  # fit up to 1/this_value of max peak height (ie 1/20 is 5%)
show_LEO_fit = False
instrument = 'WHI_UBCSP2'
instrument_locn = 'WHI'
type_particle = 'incand' #PSL, nonincand, incand
start_analysis_at = datetime.strptime('20120406','%Y%m%d')
end_analysis_at = datetime.strptime('20120430','%Y%m%d')
analysis_time_start = 20
analysis_time_end = 8
FF = 1.
#parameters for settign values of fixed variables in Gaussian fitting
calib_instrument = 'WHI_UBCSP2'
calib_instrument_locn = 'WHI'
calib_type_particle = 'nonincand'

#pararmeters used to reject invalid particle records based on scattering peak attributes
min_peakheight = 20
max_peakheight = 3500
min_peakpos = 20
max_peakpos = 125

#pararmeters used to assess incandescent peak
min_incand_amp = 20

#parameters for calculating rBC mass

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
	
	#**********get LEO calib parameters
	file_date = datetime.strptime(parameters['folder'],'%Y%m%d')
	file_date_UNIX = calendar.timegm(file_date.timetuple())
	time_span = 172800 #48h in secs
	begin_calib_data = file_date_UNIX-time_span
	end_calib_data = file_date_UNIX+time_span
	#get parameters for fixing variables in Gaussian fitting
	
	c.execute('''SELECT FF_gauss_width, zeroX_to_peak FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=? and UTC_datetime>? and UTC_datetime<? and FF_gauss_width is not null and zeroX_to_peak is not null ''', (calib_instrument,calib_instrument_locn,calib_type_particle, begin_calib_data, end_calib_data))
	result = c.fetchall()

	mean_gauss_width = np.nanmean([row[0] for row in result])+FF
	mean_zeroX_to_peak = np.nanmean([row[1] for row in result]) 


	#calculate half-width at x% point (eg 5% for factor 20)  
	HWxM = math.sqrt(2*math.log(LEO_factor))*(mean_gauss_width-FF)
	zeroX_to_LEO_limit = HWxM + mean_zeroX_to_peak

	print zeroX_to_LEO_limit,mean_gauss_width,mean_zeroX_to_peak
	
	#*******HK ANALYSIS************ 

	###use for hk files with no timestamp (just time since midnight) (this should work for the EC polar flights in spring 2012,also for ECSP2 for WHI 20100610 to 20100026, UBCSP2 prior to 20120405)
	#avg_flow = hk_new_no_ts_LEO.find_bad_hk_durations_no_ts(parameters) 
	#parameters['avg_flow'] = avg_flow
	#bad_durations = []

	###use for hk files with timestamp (this is for the UBCSP2 after 20120405)
	avg_flow = hk_new.find_bad_hk_durations(parameters)
	parameters['avg_flow'] = avg_flow

	#*************LEO routine************
	
	for file in os.listdir('.'):
		
		if file.endswith('.sp2b'):
			
			print file
			f2 = open(file, 'rb')			
			path = parameters['directory'] + '/' + str(file)
			file_bytes = os.path.getsize(path) #size of entire file in bytes
			record_size = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)
			number_of_records = (file_bytes/record_size)-1
			if num_records_to_analyse == 'all':
				number_records_toshow =  number_of_records 
			else:
				number_records_toshow = num_records_to_analyse    

			
			## fitting scattering signals to get info for LEO fits
			record_index = 0
			while record_index < number_records_toshow:
				
				##Import and parse binary
				record = f2.read(record_size)
				particle_record = ParticleRecord(record, parameters['acq_rate'], parameters['timezone'])	
				event_time = particle_record.timestamp #UNIX ts in UTC
				local_datetime = datetime.utcfromtimestamp(event_time)+timedelta(hours=parameters['timezone'])
				
				print event_time, local_datetime
				sys.exit()
				
				if local_datetime.hour >=
				#run the scatteringPeakInfo method to retrieve various peak attributes
				particle_record.scatteringPeakInfo()
				
				#get the zero-crossing with the appropriate method
				zero_crossing_pt_LEO = particle_record.zeroCrossing()
					
				analyze_this_particle = False
				
				#for calibration purposes we only grab files where we had a successful fullGauss fit 
				if type_particle == 'nonincand' or type_particle == 'PSL':
					c.execute('''SELECT * FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=? and sp2b_file=? and file_index=?''', (instrument,instrument_locn,type_particle, file, record_index))
					result = c.fetchone()
					if result is not None:
						analyze_this_particle = True
						
				#for looking at incandescent particles we will try a LEO fit if scattering and incandescent peaks high enough
				if type_particle == 'incand':
					
					particle_record.incandPeakInfo() #run the incandPeakInfo method to retrieve various incandescence peak attributes				
					incand_pk_amp = particle_record.incandMax					
					incand_pk_pos = particle_record.incandMaxPos
					zero_crossing_pt = particle_record.zeroCrossing() #get this to calc lag time
					
					if incand_pk_amp > min_incand_amp:

						scattering_pk_amp = particle_record.scatteringMax
						lag_time_pts = (incand_pk_pos-zero_crossing_pt)+mean_zeroX_to_peak
	
						c.execute('''INSERT or IGNORE into SP2_coating_analysis (sp2b_file, file_index, instr, instr_locn, particle_type) VALUES (?,?,?,?,?)''', (file, record_index,instrument, instrument_locn,type_particle))
						c.execute('''UPDATE SP2_coating_analysis SET 
						UTC_datetime=?, 
						actual_scat_amp=?, 
						incand_amp=?,
						lag_time_fit_to_incand=?						
						WHERE sp2b_file=? and file_index=? and instr=?''', 
						(event_time,
						scattering_pk_amp,
						incand_pk_amp,
						lag_time_pts,
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
					
					particle_record.leoGaussFit(zeroX_to_LEO_limit,mean_zeroX_to_peak,mean_gauss_width)
					
					LEO_max_fit_index = particle_record.LF_max_index
					LEO_amp = particle_record.LF_scattering_amp	 #this will be -1 if the fitting failed
					LEO_baseline = particle_record.LF_baseline #this will be -1 if the fitting failed
					actual_baseline = particle_record.scatteringBaseline
					LF_percent_diff_baseline = np.absolute((LEO_baseline-actual_baseline)/(0.5*LEO_baseline+0.5*actual_baseline))
					
					if LEO_max_fit_index < 5 or LEO_max_fit_index > max_peakpos: #error locating LEO fitting index
						LEO_amp = -2
						LEO_baseline = -2
						
					c.execute('''UPDATE SP2_coating_analysis SET 
						LF_scat_amp=?,
						LF_baseline_pct_diff=?
						WHERE sp2b_file=? and file_index=? and instr=?''',
						(LEO_amp,
						LF_percent_diff_baseline,
						file,record_index,instrument))
		
				#plot particle fit if desired				
				if show_LEO_fit == True and incand_pk_amp > min_incand_amp:
				
					x_vals_all = particle_record.getAcqPoints()
					y_vals_all = particle_record.getScatteringSignal()	
					y_vals_split = particle_record.getSplitDetectorSignal()
					y_vals_incand = particle_record.getWidebandIncandSignal()
					fit_result = particle_record.LF_results		
										
					print file, 'record: ',record_index
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
					plt.axvline(x=zero_crossing_pt_LEO, ymin=0, ymax=1)
					plt.axvline(x=particle_record.beam_center_pos, ymin=0, ymax=1, color='red')
					plt.show()

						
				record_index+=1    
			
			f2.close()        
		conn.commit()

if multiple_directories == True:
	os.chdir(data_dir)
	for directory in os.listdir(data_dir):
		if os.path.isdir(directory) == True and directory.startswith('20'):
			parameters['folder']= directory
			folder_date = datetime.strptime(directory, '%Y%m%d')		
			if folder_date >= start_analysis_at and folder_date <= end_analysis_at:
				parameters['directory']=os.path.abspath(directory)
				os.chdir(parameters['directory'])
				gaussLEOFit(parameters)
				os.chdir(data_dir)
	conn.close()	

else:
	parameters['directory']=os.path.abspath(analysis_dir)
	os.chdir(parameters['directory'])
	gaussLEOFit(parameters)
	conn.close()


