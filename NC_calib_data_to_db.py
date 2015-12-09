import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
from matplotlib import dates
import calendar
from SP2_particle_record_UTC import ParticleRecord

size = '300'
instr = 'UBCSP2'
instr_loc = 'POLAR6'
particle_type = 'PSL'
path = 'D:/2015/NETCARE_UBC_SP2/calibration data/20150129/'

#Jan PSL Calib
sizes = {
'269' : ['20150129x001.sp2b']	,	
'150' : ['20150129x002.sp2b']   ,
'240' : ['20150129x003.sp2b']   ,
'200' : ['20150129x004.sp2b']   ,
'300' : ['20150129x005.sp2b']   ,
'350' : ['20150129x006.sp2b']   ,
}

##bad hk durations for Jan PSL calib
bad_durations = [
[1422550636.5,1422550657.5 ],
[1422550723.5,1422550765.5 ],
[1422550741.5,1422554067.5 ],
[1422553476.5,1422553477.5 ],
[1422556306.5,1422556368.5 ],
[1422559955.5,1422559977.5 ],
[1422560497.5,1422560538.5 ],
[1422560621.5,1422560635.5 ],
[1422560660.5,1422560698.5 ],
[1422561169.5,1422561185.5 ],
[1422562205.5,1422562246.5 ],
[1422562683.5,1422562704.5 ],
[1422562911.5,1422562950.5 ],
[1422563234.5,1422563255.5 ],
[1422563272.5,1422563324.5 ],
[1422563368.5,1422563416.5 ],
[1422563635.5,1422563673.5 ],
[1422563778.5,1422563810.5 ],
[1422563859.5,1422563862.5 ],
[1422564076.5,1422564098.5 ],
[1422564212.5,1422564257.5 ],
[1422564699.5,1422564721.5 ],
[1422564907.5,1422564953.5 ],
[1422565044.5,1422565064.5 ],
[1422565106.5,1422565153.5 ],
[1422565320.5,1422565442.0 ],
[1422565425.0,1422565442.0 ],
]


##Alert PSL Calib
#sizes = {
#'200' : ['20150409x054.sp2b']	,	
#'350' : ['20150409x055.sp2b']   ,
#'100' : ['20150409x056.sp2b']   ,
#'269' : ['20150409x057.sp2b']   ,
#}
#
###bad hk durations for Alert PSL calib
#bad_durations = [
#[1428585881.6,1428585882.6],
#[1428586381.6,1428586490.6],
#[1428612439.5,1428612441.4],
#[1428620358.9,1428620360.8],
#]

# Jan AD calib
#sizes = {
#'80'  : ['20150128x001.sp2b']	,	
#'100' : ['20150128x002.sp2b']   ,
#'125' : ['20150128x003.sp2b']   ,
#'150' : ['20150128x004.sp2b']   ,
#'200' : ['20150128x005.sp2b']   ,
#'250' : ['20150128x006.sp2b']   ,
#'269' : ['20150128x007.sp2b']   ,
#'300' : ['20150128x008.sp2b']   ,
#'350' : ['20150128x009.sp2b']   ,
#}

#bad hk durations for Jan AD calib
#bad_durations = [
#[1422480565.1, 1422480567.1],
#[1422481030.1, 1422481036.1],
#[1422481218.1, 1422481223.1],
#[1422481452.1, 1422481457.1],
#[1422481642.1, 1422481647.1],
#[1422481816.1, 1422481821.1],
#[1422482200.1, 1422482204.1],
#[1422482493.1, 1422482497.1],
#[1422482696.1, 1422482700.1],
#[1422482998.1, 1422483005.1],
#[1422483239.1, 1422483244.1],
#[1422483444.1, 1422483448.2],
#[1422483644.1, 1422483649.1],
#[1422483963.0, 1422484011.0],
#[1422484202.0, 1422484206.0],
#[1422484517.0, 1422484522.0],
#[1422484729.0, 1422484734.0],
#[1422484878.9, 1422484920.9],
#[1422485081.9, 1422485086.9],
#[1422485263.9, 1422485268.9],
#[1422485459.9, 1422485463.9],
#[1422485960.9, 1422485962.9],
#[1422485989.9, 1422485999.9],
#[1422486482.9, 1422486487.9],
#[1422486569.9, 1422486570.9],
#[1422486704.9, 1422486705.9],
#]


## Alert AD calib
#sizes = {
#'80'  : ['20150410x001.sp2b']	,	
#'100' : ['20150410x002.sp2b']   ,
#'125' : ['20150410x003.sp2b']   ,
#'150' : ['20150410x005.sp2b']   ,
#'200' : ['20150410x006.sp2b']   ,
#'250' : ['20150410x007.sp2b']   ,
#'269' : ['20150410x008.sp2b']   ,
#'300' : ['20150410x009.sp2b']   ,
#'350' : ['20150410x010.sp2b']   ,
#}

##bad hk durations for Alert AD calib
#bad_durations = [
#[calendar.timegm(datetime(2015,1,1,0,0,0).utctimetuple()),   calendar.timegm(datetime(2015,4,10,1,9,11).utctimetuple())],
#[calendar.timegm(datetime(2015,4,10,1,12,13).utctimetuple()),calendar.timegm(datetime(2015,4,10,1,12,45).utctimetuple())],
#[calendar.timegm(datetime(2015,4,10,1,23,18).utctimetuple()),calendar.timegm(datetime(2015,4,10,1,24,45).utctimetuple())],
#[calendar.timegm(datetime(2015,4,10,1,28,56).utctimetuple()),calendar.timegm(datetime(2015,4,10,1,32,23).utctimetuple())],
#]

#setup analysis
num_records_to_analyse = 'all'
record_size = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)
acq_rate = 5000000

#files

data_dir = os.path.abspath(path)
file =  sizes[size][0]
print file
os.chdir(data_dir)
f = open(file, 'rb')
path = data_dir + '/' + file
file_bytes = os.path.getsize(path) #size of entire file in bytes
number_of_records = (file_bytes/record_size)-1


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()
add_data = ('INSERT INTO polar6_calibration_data'
            '(sp2b_file,file_index,instrument,instrument_locn,particle_type,particle_dia,UNIX_UTC_ts,actual_scat_amp,incand_amp)'
            'VALUES (%(sp2b_file_name)s,%(index)s,%(instrument)s,%(instrument_locn)s,%(particle_type)s,%(particle_dia)s,%(UNIX_UTC_ts)s,%(actual_scat_amp)s,%(incand_amp)s)')

record_index = 0      
while record_index < number_of_records:
	##Import and parse binary
	record = f.read(record_size)
	try:
		particle_record = ParticleRecord(record, acq_rate)
	except:
		print 'corrupt particle record', record_index
		input("Press Enter to continue...")
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
		particle_record.scatteringPeakInfo()
		scat_max = particle_record.scatteringMax
		incand_max = particle_record.incandMax
		event_timestamp = particle_record.timestamp
		
		calib_data ={
		'sp2b_file_name' : file[:-5],
		'index' :record_index,
		'instrument' : instr,
		'instrument_locn' :instr_loc,
		'particle_type' :particle_type,
		'particle_dia' :int(size),  
		'UNIX_UTC_ts' : event_timestamp, 
		'actual_scat_amp' :float(scat_max),
		'incand_amp' : float(incand_max),
		}
		
		
		cursor.execute(('DELETE FROM polar6_calibration_data WHERE UNIX_UTC_ts = %s and %s'),(event_timestamp,1))
		cnx.commit()
		cursor.execute(add_data, calib_data)
		cnx.commit()
		
		
		
	record_index+=1
	
	

cnx.close()