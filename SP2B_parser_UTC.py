#parse SP2 binary files and record particles incandesence data 
#data recorded is particle_event_start_time(UNIXtime UTC), particle_event_end_time(UNIXtime UTC), incand_flag, incand_sat_flag, BC_mass(fg), incand_height(au), NB_incand_height(au)
#time is in UTC

import sys
import os
from pprint import pprint
from decimal import Decimal
import pickle
from SP2_particle_record_UTC import ParticleRecord


def parse_sp2b_files(parameters):

	current_dir = parameters['directory']
	os.chdir(current_dir)
	
	first_file = True
	

	#set thresholds for scattering and incandescence and saturation levels 
	BC_min = parameters['BC_min']
	incand_sat = parameters['incand_sat']

	#get BC mass calibration factors in fg/counts
	BC_calib1 = parameters['BC_calib1']  
	BC_calib2 = parameters['BC_calib2']
	BC_calib3 = parameters['BC_calib3']
	BC_density = parameters['BC_density']

	#set interval to detect gaps in the data 
	#ie if we don't see a trigger for this interval, we can assume the data collection has gone haywire
	data_gap = parameters['data_gap'] #in secs

	#initializa array for the processed data
	processed_data = [] 
	duration_start = 0
						
	#initialize all variables for our analysis
	end_time = None
	BC_mass_to_write = 0
	incand_flag = 0
	incand_sat_flag = 0
	
	#read bad hk durations from pickled file 
	for file in os.listdir('.'):
		if file.endswith('.hkpckl'):
			f = open(file, 'r')
			bad_durations = pickle.load(f)
			f.close()
	
	for file in os.listdir('.'):
		if file.endswith('.sp2b')==True and file.endswith('bkgnd.sp2b') == False :

			print file
			
			path = current_dir + '/' + str(file)
			file_bytes = os.path.getsize(path) #size of entire file in bytes
			record_size =  parameters['record_size'] #size of a single particle record in bytes
			number_of_records = (file_bytes/record_size)
			
			#start reading files
			f = open(file, 'rb')
			
				
			if number_of_records < 5:
				continue
			
			#sometimes the particle records are written to file out of time order
			#build a queue of the first 5 particle records
			record_queue = []
			for i in range(5):
				record = f.read(record_size)
				record_queue.append(ParticleRecord(record, parameters['acq_rate'], parameters['timezone']))

			#start running through the particle records
			while len(record_queue):
				
				##Import the Next record 
				record = f.read(record_size)

				#if we successfully imported a new record (ie we're not at the end of the file) add it to the queue
				if record: 
					record_queue.append(ParticleRecord(record, parameters['acq_rate'], parameters['timezone']))

				
				# set current particle record to the record in the queue with the smallest timestamp and then pop it off the array so we don't use it again
				particle_record = min(record_queue, key=lambda x: x.timestamp)     
				record_queue.pop(record_queue.index(particle_record))               
				
				#UTC eventtime 
				event_time = particle_record.timestamp
				
				number_bad_durations = len(bad_durations)

				#if there are any bad durations, note the beginning and end times of the first one
				if number_bad_durations:               
					bad_duration_start_time = bad_durations[0][0]
					bad_duration_end_time = bad_durations[0][1]

					#if bad durations remain and the current particle event is after the end of the first in the list, pop that one off and check the next one
					while event_time >= bad_duration_end_time:
						bad_durations.pop(0)
						if len(bad_durations):
							bad_duration_start_time = bad_durations[0][0]
							bad_duration_end_time = bad_durations[0][1]
							continue
						else:
							break
							
					number_bad_durations = len(bad_durations)

				#if this event is not in a bad hk duration we'll grab some data
				if not number_bad_durations or event_time < bad_duration_start_time: 

					particle_record.incandPeakInfo()
					particle_record.narrowIncandPeakInfo()
					incand_ht = particle_record.incandMax
					narrow_incand_ht = particle_record.narrowIncandMax
					BC_mass = BC_calib1 + incand_ht*BC_calib2 + incand_ht*incand_ht*BC_calib3 # gives BC in fg
										
					if BC_mass >= BC_min:
						BC_mass_to_write = BC_mass
						start_time = duration_start  #the start of an acquisition duration is when the last event was written to file (and we started waiting for a new trigger)
						end_time = event_time  #the end of an acquisition duration is the when the current event was written to file 
						incand_flag = 1
						if incand_ht > incand_sat:
							incand_sat_flag = 1
							
						#check for big gaps in data collection (maybe instrument failures)                        
						if (end_time - start_time) < data_gap: 
							processed_row = [Decimal(start_time), Decimal(end_time), incand_flag, incand_sat_flag, BC_mass_to_write, incand_ht, narrow_incand_ht] 
							processed_data.append(processed_row)                        
					
						#reset flags and variables for next loop iteration
						duration_start = end_time   #now the current events end time becomes the start time when waiting for the next trigger
						BC_mass_to_write = 0
						incand_flag = 0
						incand_sat_flag = 0
				
				
			#write to file after each sp2bfile/loop to avoid bogging down from holding huge array in memory
			print 'to file'
			file = open('processed_SP2_data_' + parameters['folder'] + '.ptxt', 'a')
			if first_file == True:
				file.truncate(0)
				file.write('particle_event_start_time(UNIXtime UTC)'+ '\t' + 'particle_event_end_time(UNIXtime UTC)'+ '\t' + 'incand_flag'+ '\t' + 'incand_sat_flag'+ '\t' + 'BC_mass(fg)' + '\t' + 'incand_height(au)' + '\t' +'NB_incand_height(au)' + '\n')
				first_file = False
			for row in processed_data:
				line = '\t'.join(str(x) for x in row)
				file.write(line + '\n')
			file.close()
			
			processed_data = []
				
			f.close()   
		
