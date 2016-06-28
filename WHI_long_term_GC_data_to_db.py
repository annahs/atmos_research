import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
from pyhdf.SD import SD, SDC, SDS
import collections
import calendar
import mysql.connector



cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

GC_runs = ['default','Vancouver_emission','wet_scavenging','no_biomass','All_together']

lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg
level = 9 #1-47 #9 is closest to WHI avg P (WHI 95% CI = 770-793)

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

#query to add 1h mass conc data
add_data = ('INSERT INTO whi_gc_hourly_bc_data'
			  '(UNIX_UTC_start_time,UNIX_UTC_end_time,def_BC,wetscav_BC,nobb_BC,Van_BC,all_BC)'
			  'VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(def_BC)s,%(wetscav_BC)s,%(nobb_BC)s,%(Van_BC)s,%(all_BC)s)'
			  )


GC_run = 'All_together'
print GC_run
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/' + GC_run +'/'
os.chdir(data_dir)

i=1
multiple_records = []
for file in os.listdir(data_dir):
	if file.endswith('.hdf'): 
		
		file_year = int(file[2:6])
		file_month = int(file[6:8])
		file_day = int(file[8:10])
		file_hour = int(file[11:13])
		GC_datetime = datetime(file_year,file_month,file_day,file_hour)
		GC_UNIX_UTC_ts = calendar.timegm(GC_datetime.utctimetuple())
		
		hdf_file = SD(file, SDC.READ)

		hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
		hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')
		total_BC_ppbv = hydrophilic_BC[level,lat,lon] + hydrophobic_BC[level,lat,lon]
		BC_conc_ngm3 = total_BC_ppbv*molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	

		hdf_file.end()

		cursor.execute('''UPDATE whi_gc_hourly_bc_data
			SET all_BC = %s
			WHERE UNIX_UTC_start_time = %s ''',
			(BC_conc_ngm3,GC_UNIX_UTC_ts)
		)	
		cnx.commit()
		
		#single_record ={
		#	'UNIX_UTC_start_time':
		#	'UNIX_UTC_end_time':
		#	'def_BC': BC_conc_ngm3,
		#	'wetscav_BC': 
		#	'nobb_BC':  
		#	'Van_BC': 
		#	'all_BC': 
		#}	
			
		#multiple_records.append((single_record))
        #
		##bulk insert to db table
		#if i%5000 == 0:
		#	cursor.executemany(add_data, multiple_records)
		#	cnx.commit()
		#	multiple_records = []
		#	
		#increment count 
		i+= 1
		
##bulk insert of remaining records to db
#if multiple_records != []:
#	cursor.executemany(add_data, multiple_records)
#	cnx.commit()
#	multiple_records = []		
#


cnx.close()



