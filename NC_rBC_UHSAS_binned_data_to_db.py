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


flight = 'science 4' 
incand_calib_intercept = 0.19238  #alert = 0.19238
incand_calib_slope = 0.00310  #alert = 0.00310
R = 8.3144621 # in m3*Pa/(K*mol)
sample_flow_lower_limit = 100
min_BC_VED = 70
max_BC_VED = 220
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
incand_min = (min_rBC_mass-incand_calib_intercept)/incand_calib_slope
incand_max = (max_rBC_mass-incand_calib_intercept)/incand_calib_slope


flight_times = {
'science 1'  : [''],	
'ferry 1'    : ['UHSAS_Polar6_20150406_R0_V1.ict'], #no flight data 
'ferry 2'    : ['UHSAS_Polar6_20150406_R0_V2.ict'], #no flight data
'science 2'  : ['UHSAS_Polar6_20150407_R0_V1.ict'], #no flight data
'science 3'  : ['UHSAS_Polar6_20150408_R0_V1.ict'],  ###
'science 4'  : ['UHSAS_Polar6_20150408_R0_V2.ict'],	 ###
'science 5'  : ['UHSAS_Polar6_20150409_R0_V1.ict'],  ###
'ferry 3'    : ['UHSAS_Polar6_20150410_R0_V1.ict'],	 ###
'science 6'  : ['UHSAS_Polar6_20150411_R0_V1.ict'],	 ###
'science 7'  : ['UHSAS_Polar6_20150413_R0_V1.ict'],	 ###
'science 8'  : ['UHSAS_Polar6_20150420_R0_V1.ict'],	 ###
'science 9'  : ['UHSAS_Polar6_20150420_R0_V2.ict'],	 ###
'science 10' : ['UHSAS_Polar6_20150421_R0_V1.ict'],  ###
}



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#MySQL data insert statement
add_data = ('INSERT INTO polar6_UHSAS_rBC_binned_data'
	  '(UNIX_UTC_ts, bin_LL, bin_UL, binned_property, value)'
	  'VALUES (%(UNIX_UTC_ts)s,%(binLL)s,%(binUL)s,%(property)s,%(prop_value)s)')

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/1Hz-ict-R0/')
#UHSAS_file = flight_times[flight][0]

no_prev_particle = False


printcounter = 0

for UHSAS_file in ['UHSAS_Polar6_20150410_R0_V1.ict','UHSAS_Polar6_20150411_R0_V1.ict','UHSAS_Polar6_20150413_R0_V1.ict','UHSAS_Polar6_20150420_R0_V1.ict','UHSAS_Polar6_20150420_R0_V2.ict']:

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

				#print progress reports
				if printcounter == 100:
					print time_stamp
					printcounter = 0
				printcounter += 1
				####
				
				
				#get the sample flow from the hk data to calc sampled volume 
				cursor.execute(('SELECT sample_flow from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(time_min,time_max))
				hk_data = cursor.fetchall()
				
				#if no hk data collected we can't get a number conc, but we can still get a mean coating and core size, so continue, but sample flow is nan
				if hk_data == []: 
					sample_flow = np.nan
				else:
					sample_flow = hk_data[0][0] #in vccm
				
				#drops in the sample flow are an issue so don't calc a conc for these periods
				if sample_flow <= sample_flow_lower_limit: 
					sample_flow = np.nan
				
				
				#get the timestamp from the last valid particle in the interval
				cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts < %s AND particle_type = %s and instrument = %s and incand_amp >=%s and incand_amp <=%s order by UNIX_UTC_ts desc limit 1'),(time_max, 'incand', 'UBCSP2',incand_min,incand_max))
				last_particle_data = cursor.fetchall()
				last_particle_ts = last_particle_data[0][0]
				
				#get timestamp from last valid particle before this interval so we can caluculate the volume sampled 
				cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts < %s AND particle_type = %s and instrument = %s and  incand_amp >=%s and incand_amp <=%s order by UNIX_UTC_ts desc limit 1'),(time_min, 'incand', 'UBCSP2',incand_min,incand_max))
				prev_particle_data = cursor.fetchall()			
				#take care of the edge-case where we're looking at the first particle of the run, in this case we'll ignore the first particle in the interval since we don't know when we started waiting for it to be detected
				if prev_particle_data == []:
					#in this case get the timestamp from the first valid particle in the interval
					cursor.execute(('SELECT UNIX_UTC_ts FROM polar6_coating_2015 WHERE UNIX_UTC_ts >= %s AND particle_type = %s and instrument = %s and incand_amp >=%s and incand_amp <=%s order by UNIX_UTC_ts limit 1'),(time_min, 'incand', 'UBCSP2',incand_min,incand_max))
					substitute_prev_particle_data = cursor.fetchall()
					prev_particle_ts = substitute_prev_particle_data[0][0]
					no_prev_particle = True
				else:
					prev_particle_ts = prev_particle_data[0][0]
					
						
				#calc total interval sampling time and sampled volume
				interval_sampling_time = last_particle_ts - prev_particle_ts
				if interval_sampling_time <= 0:
					#print  'interval_sampling_time bad', interval_sampling_time
					interval_sampled_volume = np.nan
				else:
					interval_sampled_volume = sample_flow*interval_sampling_time/60 #factor of 60 to convert minutes to secs, result is in cc
			
			
				#get T and P for correction to STP/SCCM
				cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts > %s and UNIX_UTC_ts <= %s'),(time_min,time_max))
				TandP_data = cursor.fetchall()
				
					
				#now get the particle data per bin
				for bin_number in range(0,len(bin_dict)):
					bin_LL =  bin_dict[bin_number][0]
					bin_UL =  bin_dict[bin_number][1]
							
								
					##### SP2 data	
					#get core + coating count				
					cursor.execute(('SELECT count(*) from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and instrument = %s and (POW(rBC_mass_fg,(1/3.0))*101.994391398+2*coat_thickness_nm) >=%s and (POW(rBC_mass_fg,(1/3.0))*101.994391398+2*coat_thickness_nm) <=%s'),
						(time_min,time_max, 'incand', 'UBCSP2',bin_LL,bin_UL))
					core_plus_coating_count = cursor.fetchall()[0][0]
					#get core only data 
					cursor.execute(('SELECT rBC_mass_fg, coat_thickness_nm from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and instrument = %s and (POW(rBC_mass_fg,(1/3.0))*101.994391398) >=%s and (POW(rBC_mass_fg,(1/3.0))*101.994391398) <=%s'),
						(time_min,time_max, 'incand', 'UBCSP2',bin_LL,bin_UL))
					core_only_data = cursor.fetchall()		

					
					#### UHSAS data
					UHSAS_norm_number = float(newline[bin_number+4].rstrip(','))	#this is dN/dLogD per sccm	
					
								
					#check that we have both valid UHSAS and SP2 data, we can only make a meaningful UHSAS/SP2 conc ratio if we have valid measurements for both
					if UHSAS_norm_number < 0: #-9999 is missing data and any other negative is a data problem
						#print UNIX_time_stamp, 'no UHSAS data'
						UHSAS_number = None
						core_plus_coating_number_conc = None
						core_only_number_conc = None
					elif TandP_data == []:
						#print UNIX_time_stamp, 'no SP2 data: T and P missing'
						UHSAS_number = None
						core_plus_coating_number_conc = None
						core_only_number_conc = None
					elif np.isnan(interval_sampled_volume) == True:
						#print UNIX_time_stamp, 'no SP2 data: no, or bad, sample flow data'
						UHSAS_number = None
						core_plus_coating_number_conc = None
						core_only_number_conc = None
					else:
						temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
						pressure = TandP_data[0][1]
						correction_factor_for_STP = (101325/pressure)*(temperature/273.15)
						UHSAS_number = UHSAS_norm_number*(math.log(bin_UL)-math.log(bin_LL)) #this is dN per sccm
						core_plus_coating_number_conc = core_plus_coating_count*correction_factor_for_STP/interval_sampled_volume  #dN/sccm
						core_only_number_conc = len(core_only_data)*correction_factor_for_STP/interval_sampled_volume
						
						if no_prev_particle == True:  #in this case need to ignore first particle (but don't want negative if the count is zero)
							if core_only_count > 0:
								core_only_number_conc = (len(core_only_data)-1)*correction_factor_for_STP/interval_sampled_volume
							else:
								core_only_number_conc = 0
								
							if core_plus_coating_count > 0:
								core_plus_coating_number_conc = (core_plus_coating_count-1)*correction_factor_for_STP/interval_sampled_volume  #dN/sccm
							else:
								core_plus_coating_number_conc = 0
						
							
					#calcualte and write mean core and coating sizes (need a core and a coating value)
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
				
					#write number concs if we have the available data
					if UHSAS_number != None and core_plus_coating_number_conc != None and core_only_number_conc != None:
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
