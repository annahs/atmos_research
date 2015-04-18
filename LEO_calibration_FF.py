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




data_dir = 'D:/2012/WHI_UBCSP2/Binary/' #'D:/2009/WHI_ECSP2/Binary/'# 'D:/2010/WHI_ECSP2/Binary/'  #'D:/2012/WHI_UBCSP2/Binary/' 
#analysis_dir = 'D:/2012/WHI_UBCSP2/Calibrations/20120328/PSL/Binary/200nm/'
multiple_directories = True
instrument = 'WHI_UBCSP2'
instrument_locn = 'WHI'
PSL_size = np.nan
type_particle = 'nonincand' #PSL, nonincand, incand
start_analysis_at = datetime.strptime('20080601','%Y%m%d')
end_analysis_at = datetime.strptime('20120410','%Y%m%d')


#setup
num_records_to_analyse = 100
show_full_fit = False

#pararmeters used to reject invalid particle records based on scattering peak attributes
min_peakheight = 20
max_peakheight = 3500
min_peakpos = 20
max_peakpos = 125


#setup database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

c.execute('''CREATE TABLE if not exists SP2_coating_analysis(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sp2b_file TEXT, 
file_index INT, 
instr TEXT,
instr_locn TEXT,
particle_type TEXT,		
particle_dia FLOAT,				
date TIMESTAMP,
actual_scat_amp FLOAT,
actual_peak_pos INT,
FF_scat_amp FLOAT,
FF_peak_pos INT,
FF_gauss_width FLOAT,
zeroX_to_peak FLOAT,
LF_scat_amp FLOAT,
incand_amp FLOAT,
UNIQUE (sp2b_file, file_index, instr)
)''')

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


	
def gaussFullFit(parameters_dict):
	
	
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
			
			path = parameters['directory'] + '/' + str(file)
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
				particle_record = ParticleRecord(record, parameters['acq_rate'], parameters['timezone'])	
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
					
					#run the incandPeakInfo method to retrieve peak height
					particle_record.incandPeakInfo()
					incand_max = particle_record.incandMax
					
					#check for a double peak
					try:
						particle_record.isSingleParticle()
					except:
						print record_index
						print actual_max_value

					#note: zero-crossing calc will depend on the slope of the zero-crossing from the split detector
					zero_crossing_pt = particle_record.zeroCrossing()
					
					
					#check to see if incandescencen is negligible, scattering signal is over threshold, is in a reasonable position, and no double peaks
					if incand_max < 5. and actual_max_value > min_peakheight and actual_max_value < max_peakheight and actual_max_pos > min_peakpos and actual_max_pos < max_peakpos and particle_record.doublePeak==False and zero_crossing_pt > 0 : 
						
						particle_record.fullGaussFit()
						
						fit_peak_pos = particle_record.FF_peak_pos
						fit_gauss_width = particle_record.FF_gauss_width
						fit_scattering_amp = particle_record.FF_scattering_amp
						zero_cross_to_peak = (zero_crossing_pt - fit_peak_pos)
						
						#put particle into database or update record
						c.execute('''INSERT or IGNORE into SP2_coating_analysis (sp2b_file, file_index, instr, instr_locn, particle_type, particle_dia) VALUES (?,?,?,?,?,?)''', (file, record_index,instrument, instrument_locn,type_particle,PSL_size))
						c.execute('''UPDATE SP2_coating_analysis SET 
						date=?, 
						actual_scat_amp=?, 
						actual_peak_pos=?, 
						FF_scat_amp=?, 
						FF_peak_pos=?, 
						FF_gauss_width=?, 
						zeroX_to_peak=?
						WHERE sp2b_file=? and file_index=? and instr=?''', 
						(event_time,
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
							
							print record_index, actual_max_value
							
							fig = plt.figure()
							ax1 = fig.add_subplot(111)
							ax1.plot(x_vals,y_vals,'o', markerfacecolor='None')   
							ax1.plot(x_vals,fit_result, 'red')
							plt.show()

							

				record_index+=1   
					
			f.close()
			
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
				gaussFullFit(parameters)
				os.chdir(data_dir)
	conn.close()	

else:
	parameters['directory']=os.path.abspath(analysis_dir)
	os.chdir(parameters['directory'])
	gaussFullFit(parameters)
	conn.close()


	