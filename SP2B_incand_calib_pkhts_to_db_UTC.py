import sys
import os
import pickle
import numpy as np
from pprint import pprint
from SP2_particle_record_UTC import ParticleRecord
from struct import *
import hk_new
import hk_new_no_ts_LEO
import math
import sqlite3
from datetime import datetime




analysis_dir = 'D:/2015/NETCARE_UBC_SP2/calibration data/20150128/AD450/'
instrument = 'UBCSP2' #'UBCSP2' #ECSP2
instrument_locn = 'POLAR6'
type_particle = 'Aquadag' #PSL, nonincand, incand, Aquadag
particle_diameter = 450
start_analysis_at = datetime.strptime('20150101','%Y%m%d')
end_analysis_at = datetime.strptime('20160101','%Y%m%d')


#setup analysis
num_records_to_analyse = 'all'
record_size_bytes = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)


#**********parameters dictionary**********
parameters = {
'directory':os.path.abspath(analysis_dir),
'acq_rate': 5000000,
#date and time
'timezone':-8,
#will be set by hk analysis
'avg_flow':120, #in vccm
#parameter to find bad flow durations
'flow_min' : 118,
'flow_max' : 122,
'YAG_min' : 4,
'YAG_max' : 6,
'min_good_points' : 10,
#show hk plots?
'show_plot':True
}
parameters ['folder'] = '20150128' 


#setup database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

#c.execute('''CREATE TABLE if not exists SP2_coating_analysis(
#id INTEGER PRIMARY KEY AUTOINCREMENT,
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
#UNIQUE (sp2b_file, file_index, instr)
#)''')


os.chdir(parameters['directory'])



#********** start ANALYSIS ************ 


###HK

####use for hk files with no timestamp (just time since midnight) (this should work for the EC polar flights in spring 2012,also for ECSP2 for WHI 20100610 to 20100026, UBCSP2 prior to 20120405)
#avg_flow = hk_new_no_ts_LEO.find_bad_hk_durations_no_ts(parameters) 
#parameters['avg_flow'] = avg_flow
#bad_durations = []

##use for hk files with timestamp (this is for the UBCSP2 after 20120405)
#avg_flow = hk_new.find_bad_hk_durations(parameters)  #writes bad durations in UTC
#parameters['avg_flow'] = avg_flow

###Incand
for file in os.listdir('.'):
	
	if file.endswith('.sp2b'):
		
		print file
		
		path = parameters['directory'] + '/' + str(file)
		file_bytes = os.path.getsize(path) #size of entire file in bytes
		record_size = record_size_bytes  
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
			try:
				particle_record = ParticleRecord(record, parameters['acq_rate'])
			except:
				#print 'corrupt particle record'
				#input("Press Enter to continue...")
				continue
			event_time = particle_record.timestamp  #this is in UTC
			
			###### FITTING AND ANALYSIS ########          
			number_bad_durations = len(bad_durations)
			
			
			#if there are any bad hk durations, note the beginning and end times of the first one (these are in UTC too!)
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

			
				#run the incandPeakInfo method to retrieve peak height
				particle_record.incandPeakInfo()
				incand_max = particle_record.incandMax

			
				#put particle into database or update record
				c.execute('''INSERT or IGNORE into SP2_coating_analysis (sp2b_file, file_index, instr, instr_locn, particle_type) VALUES (?,?,?,?,?)''', 
				(file, record_index, instrument, instrument_locn, type_particle))
				
				c.execute('''UPDATE SP2_coating_analysis SET 
				unix_ts_utc=?, 
				particle_dia=?,
				incand_amp=?
				WHERE sp2b_file=? and file_index=? and instr=?''', 
				(event_time,
				particle_diameter,
				incand_max,
				file,record_index,instrument))


			
			record_index+=1   
				
		f.close()
	conn.commit()



conn.close()	