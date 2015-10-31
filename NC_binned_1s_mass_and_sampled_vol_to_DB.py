import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
import matplotlib.pyplot as plt
import copy


start_time = datetime(2015,4,5,7,0)
end_time = datetime(2015,4,6,0,0)
min_BC_VED = 70
max_BC_VED = 220


UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())


min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

interval_start_time = UNIX_start_time + 0.5

add_interval_data = ('INSERT INTO polar6_binned_mass_and_sampled_volume'
              '(UNIX_UTC_ts,70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220,total_mass,sampled_vol)'
              'VALUES (%(UNIX_UTC_ts)s,%(70)s,%(80)s,%(90)s,%(100)s,%(110)s,%(120)s,%(130)s,%(140)s,%(150)s,%(160)s,%(170)s,%(180)s,%(190)s,%(200)s,%(210)s,%(total_mass)s,%(sampled_vol)s)')

no_prev_particle = False
while (interval_start_time + 1) <= UNIX_end_time:
	
	interval_end_time = interval_start_time + 1
	
	#get the sample flow from the hk data to calc sampled volume 
	cursor.execute(('SELECT sample_flow from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(interval_start_time,interval_end_time))
	hk_data = cursor.fetchall()
	
	#skip times when no hk data collected
	if hk_data == []: 
		interval_start_time += 1
		continue
	
	sample_flow = hk_data[0][0] #in vccm
	
	cursor.execute(('SELECT UNIX_UTC_ts, rBC_mass_fg from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and instrument = %s order by UNIX_UTC_ts'),(interval_start_time,interval_end_time, 'incand', 'UBCSP2'))
	particle_data = cursor.fetchall()
	
	#skip times when hk data collected but no particle data collected
	if particle_data == []: 
		interval_start_time += 1
		continue
	
	#get timestamp from last particle before this interval so we can caluculate the volume sampled
	cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts < %s AND particle_type = %s AND instrument = %s order by UNIX_UTC_ts desc limit 1'),(interval_start_time, 'incand', 'UBCSP2'))
	prev_particle_data = cursor.fetchall()
	
	#take care of the edge-case where we're looking at the first particle of the run, in this case we'll ignore the first particle in the interval since we don't know when we started waiting for it to be detected
	if prev_particle_data == []:
		no_prev_particle = True
		prev_particle_ts = particle_data[0][0]
	else:
		prev_particle_ts = prev_particle_data[0][0]
		
	last_particle_ts = particle_data[-1][0]
	
	#calc total interval sampling time and mid time
	interval_sampling_time = last_particle_ts - prev_particle_ts
	interval_mid_time = interval_start_time + interval_sampling_time/2
	interval_sampled_volume = sample_flow*interval_sampling_time/60 #factor of 60 to convert minutes to secs, result is in cc
	
	binned_data = {
	'UNIX_UTC_ts':interval_mid_time,
	70:0,
	80:0,
	90:0,
	100:0,
	110:0,
	120:0,
	130:0,
	140:0,
	150:0,
	160:0,
	170:0,
	180:0,
	190:0,
	200:0,
	210:0,
	'total_mass':0,
	'sampled_vol':interval_sampled_volume,
	}
	
	for row in particle_data:
		if no_prev_particle == True:
			no_prev_particle = False
			continue
		particle_mass = row[1]
		
		#we don't have mass values for very large particles ie signal >3800au but we'll just ignore these
		try:
			particle_VED = (((particle_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
		except:
			continue
		
		for bin in binned_data:
			if bin <= particle_VED < (bin+10):	
				binned_data[bin] = binned_data[bin] + particle_mass

		binned_data['total_mass'] = binned_data['total_mass'] + particle_mass

	
	
	cursor.execute(('DELETE FROM polar6_binned_mass_and_sampled_volume WHERE UNIX_UTC_ts = %s and %s'),(interval_mid_time,1))
	cnx.commit()
	cursor.execute(add_interval_data, binned_data)
	cnx.commit()
	
	
	interval_start_time += 1
	
	
cnx.close()