import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates
from mpl_toolkits.basemap import Basemap
import calendar
from scipy.optimize import curve_fit


flight = 'test'
incand_calib_intercept = 0.19238  #alert = 0.19238
incand_calib_slope = 0.00310  #alert = 0.00310
R = 8.3144621 # in m3*Pa/(K*mol)



flight_times = {
'science 1'  : [''],	
'ferry 1'    : ['UHSAS_Polar6_20150406_R0_V1.ict'],  
'ferry 2'    : ['UHSAS_Polar6_20150406_R0_V2.ict'],
'science 2'  : ['UHSAS_Polar6_20150407_R0_V1.ict'],
'science 3'  : ['UHSAS_Polar6_20150408_R0_V1.ict'],  
'science 4'  : ['UHSAS_Polar6_20150408_R0_V2.ict'],
'science 5'  : ['UHSAS_Polar6_20150409_R0_V1.ict'],
'ferry 3'    : ['UHSAS_Polar6_20150410_R0_V1.ict'],
'science 6'  : ['UHSAS_Polar6_20150411_R0_V1.ict'],
'science 7'  : ['UHSAS_Polar6_20150413_R0_V1.ict'],
'science 8'  : ['UHSAS_Polar6_20150420_R0_V1.ict'],
'science 9'  : ['UHSAS_Polar6_20150420_R0_V2.ict'],
'science 10' : ['UHSAS_Polar6_20150421_R0_V1.ict'],  ###
'test'       : ['UHSAS_Polar6_20150421_R0_V1.ict'],  ###
}



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#MySQL data insert statement
add_data = ('INSERT INTO polar6_UHSAS_rBC_binned_data'
	  '(UNIX_UTC_ts, bin_LL, bin_UL, binned_property, value)'
	  'VALUES (%(UNIX_UTC_ts)s,%(binLL)s,%(binUL)s,%(property)s,%(prop_value)s)')

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/1Hz-ict-R0/')
UHSAS_file = flight_times[flight][0]

no_prev_particle = False

with open(UHSAS_file, 'r') as f:
	print UHSAS_file
	file_date = UHSAS_file[13:21]
	date = datetime.strptime(file_date, '%Y%m%d')

	##get bin limits
	i=0
	while i < 9:  #indep_var_number is always on line 10
		f.readline()
		i+=1
	indep_var_number = float(f.readline()) 
	i=0
	while i < (indep_var_number + 11): #check that 11 is right for each set of files
		f.readline()
		i+=1
	bin_LL_line = (f.readline()).split() 
	f.readline() #skip this line 
	bin_UL_line = (f.readline()).split() 
	
	
	##create bins dict
	bin_dict = {}
	i=0
	for LL_limit in bin_LL_line:
		bin_dict[i] = [float(LL_limit),float(bin_UL_line[i])]
		i+=1


	#start analysis
	data_start = False
	for line in f:
		no_prev_particle = False
		if line.startswith('time,flow,pressure,total_number_conc'):
			data_start = True
			continue

		if data_start == True:
			newline = line.split()
			time_stamp = date + timedelta(seconds = float(newline[0].rstrip(',')))
			UNIX_time_stamp = calendar.timegm(time_stamp.utctimetuple())	
			time_min = UNIX_time_stamp - 1
			time_max = UNIX_time_stamp

			
			#get the sample flow from the hk data to calc sampled volume 
			cursor.execute(('SELECT sample_flow from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(time_min,time_max))
			hk_data = cursor.fetchall()
			
			#if no hk data collected we can't get a number conc, but we can still get a mean coating and core size, so continue
			if hk_data == []: 
				print 'no hk data'
				sample_flow = np.nan
			else:
				sample_flow = hk_data[0][0] #in vccm
			
			#drops in the sample flow are an issue!
			if sample_flow <= 100: 
				sample_flow = np.nan
			
			#get the timestamp from the last particle in the interval so we can calculate the volume samlped
			cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts < %s AND instrument = %s order by UNIX_UTC_ts desc limit 1'),(time_max, 'UBCSP2'))
			last_particle_data = cursor.fetchall()
			
			#get timestamp from last particle before this interval so we can caluculate the volume sampled
			cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts < %s AND instrument = %s order by UNIX_UTC_ts desc limit 1'),(time_min, 'UBCSP2'))
			prev_particle_data = cursor.fetchall()
			
			#take care of the edge-case where we're looking at the first particle of the run, in this case we'll ignore the first particle in the interval since we don't know when we started waiting for it to be detected
			if prev_particle_data == []:
				no_prev_particle = True
				cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts > %s AND instrument = %s order by UNIX_UTC_ts asc limit 1'),(time_min, 'UBCSP2'))
				prev_particle_ts = cursor.fetchall()[0][0]
			else:
				prev_particle_ts = prev_particle_data[0][0]
				
			last_particle_ts = last_particle_data[0][0]
			
			#calc total interval sampling time and mid time
			interval_sampling_time = last_particle_ts - prev_particle_ts
			interval_sampled_volume = sample_flow*interval_sampling_time/60 #factor of 60 to convert minutes to secs, result is in cc
				
			#get T and P for correction to STP/SCCM
			cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts > %s and UNIX_UTC_ts <= %s'),(time_min,time_max))
			TandP_data = cursor.fetchall()
				
			#now get the particle data per bin
			for bin_number in range(0,len(bin_dict)):
				bin_LL =  bin_dict[bin_number][0]
				bin_UL =  bin_dict[bin_number][1]
						
				#### UHSAS data
				UHSAS_norm_number = float(newline[bin_number+4].rstrip(','))	#this is dN/dLogD per sccm	
				if UHSAS_norm_number >= 0:  #only record valid data
					UHSAS_number = UHSAS_norm_number*(math.log(bin_UL)-math.log(bin_LL)) #this is dN per sccm
				else:  #if there's no UHSAS data we're not going to bother getting SP2 data for comparison
					continue
				
				##### SP2 data	
				#get core + coating data unless the bin_LL is < 65 (SP2 DL), in that case just move to the next bin
				if bin_LL >= 65:
					cursor.execute(('SELECT count(*) from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and instrument = %s and (POW(rBC_mass_fg,(1/3.0))*101.994391398+2*coat_thickness_nm) >=%s and (POW(rBC_mass_fg,(1/3.0))*101.994391398+2*coat_thickness_nm) <=%s'),
						(time_min,time_max, 'incand', 'UBCSP2',bin_LL,bin_UL))
					core_plus_coating_count = cursor.fetchall()[0][0]
					
					cursor.execute(('SELECT rBC_mass_fg, coat_thickness_nm from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and instrument = %s and (POW(rBC_mass_fg,(1/3.0))*101.994391398) >=%s and (POW(rBC_mass_fg,(1/3.0))*101.994391398) <=%s'),
						(time_min,time_max, 'incand', 'UBCSP2',bin_LL,bin_UL))
					core_only_data = cursor.fetchall()
					
				else:
					continue

				#if there's no particle data we can stop here
				if core_only_data == []: 
					continue
				
				#there isn't flight data for all periods, so we can't correct to stp/sccm for all periods, but if we have it calculate SP2 number conc
				if TandP_data == []:
					print UNIX_time_stamp, 'no T and P data'
					core_plus_coating_number_conc = None
					core_only_number_conc = None
				else:
					temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
					pressure = TandP_data[0][1]
					correction_factor_for_STP = (101325/pressure)*(temperature/273.15)
					core_only_count = len(core_only_data)
					core_plus_coating_number_conc = core_plus_coating_count*correction_factor_for_STP/interval_sampled_volume  #dN/sccm
					core_only_number_conc = core_only_count*correction_factor_for_STP/interval_sampled_volume
					if no_prev_particle == True:  #in this case need to ignore first particle
						core_plus_coating_number_conc = (core_plus_coating_count-1)*correction_factor_for_STP/interval_sampled_volume  #dN/sccm
						core_only_number_conc = (core_only_count-1)*correction_factor_for_STP/interval_sampled_volume
					if np.isnan(sample_flow) == True:
						core_plus_coating_number_conc = None
						core_only_number_conc = None
				
				#coating values
				#write all data to db

				
				if bin_LL >=130 and bin_UL <= 200:
					
				
					new_list = []
					for row in core_only_data:
						mass = row[0]
						coat = row[1]
						
						if mass != None and coat != None:
							new_list.append([mass, coat])
					
					if new_list != []:
						mean_rBC_mass = np.mean([row[0] for row in new_list])
						mean_core_dia = (((mean_rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
						mean_coating = np.mean([row[1] for row in new_list])

						
						binned_data = {
						'UNIX_UTC_ts': UNIX_time_stamp,
						'binLL':  bin_LL,
						'binUL':  bin_UL,
						'property': 'mean_core_dia',
						'prop_value': float(mean_core_dia),
						}				
						cursor.execute(add_data, binned_data)
						cnx.commit()

						binned_data = {
						'UNIX_UTC_ts': UNIX_time_stamp,
						'binLL':  bin_LL,
						'binUL':  bin_UL,
						'property': 'mean_coating_th',
						'prop_value': float(mean_coating),
						}
						cursor.execute(add_data, binned_data)
						cnx.commit()
				
				binned_data = {
				'UNIX_UTC_ts': UNIX_time_stamp,
				'binLL':  bin_LL,
				'binUL':  bin_UL,
				'property': 'UHSAS_#',
				'prop_value': UHSAS_number,
				}			
				cursor.execute(add_data, binned_data)
				cnx.commit()
				
				binned_data = {
				'UNIX_UTC_ts': UNIX_time_stamp,
				'binLL':  bin_LL,
				'binUL':  bin_UL,
				'property': 'SP2_coated_#',
				'prop_value': core_plus_coating_number_conc,
				}
				cursor.execute(add_data, binned_data)
				cnx.commit()
				
				binned_data = {
				'UNIX_UTC_ts': UNIX_time_stamp,
				'binLL':  bin_LL,
				'binUL':  bin_UL,
				'property': 'SP2_core_#',
				'prop_value': core_only_number_conc,
				}
				cursor.execute(add_data, binned_data)
				cnx.commit()

				

	
cnx.close()
