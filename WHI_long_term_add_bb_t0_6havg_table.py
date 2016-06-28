import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
from matplotlib import dates
import pickle
import copy
from pyhdf.SD import SD, SDC, SDS
import collections
import calendar
import mysql.connector


#database tables

###
filter_by_RH = True
high_RH_limit = 90

if filter_by_RH == False:
	high_RH_limit = 101
####

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

############Meaurements

rBC_all_data = {}

##
#select data (spikes already rmoved) and exclude fire times 
SP2_data_query = ('''SELECT UNIX_GMT_ts,BC_mass_conc FROM whi_sp2_rbc_record_2009to2012_spikes_removed''')
cursor.execute(SP2_data_query)
SP2_data = cursor.fetchall()

#fire times for plotting shaded areas
fire_span2_09s=datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span2_09f=datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span1_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')

for row in SP2_data:	
	UNIX_UTC_ts = row[0]
	date_time_UTC = datetime.utcfromtimestamp(UNIX_UTC_ts)
	date_time_PST = date_time_UTC + timedelta(hours = -8)
	if (fire_span2_09s <= date_time_PST < fire_span2_09f) or (fire_span1_10s <= date_time_PST < fire_span1_10f):
		BC_mass_conc = row[1]
		date_to_hour = datetime(date_time_UTC.year,date_time_UTC.month,date_time_UTC.day,date_time_UTC.hour)
		if  4 <= date_to_hour.hour < 16:
			if 4 <= date_to_hour.hour < 10:
				int_midpoint = datetime(date_to_hour.year,date_to_hour.month,date_to_hour.day,7) 
			if 10 <= date_to_hour.hour < 16:
				int_midpoint = datetime(date_to_hour.year,date_to_hour.month,date_to_hour.day,13) 
						
			correction_factor_for_massdistr = 1/0.4574
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			
			if int_midpoint not in rBC_all_data:
				rBC_all_data[int_midpoint] = []
			rBC_all_data[int_midpoint].append(corrected_mass_conc)

		
#create insert statement variable for database updating
add_interval = ('INSERT INTO whi_gc_and_sp2_6h_mass_concs'
			  '(UNIX_UTC_6h_midtime,meas_mean_mass_conc,RH_threshold,cluster,meas_rel_err)'
			  'VALUES (%(UNIX_UTC_ts)s,%(SP2_mean_mass_conc)s,%(RH_threshold)s,%(cluster)s,%(meas_rel_err)s)')
#1h means 	
for date in rBC_all_data:
	mass_concs = rBC_all_data[date]
	date_mean = np.mean(mass_concs)
	UNIX_UTC_ts = calendar.timegm(date.timetuple())
	
	print date, date_mean
	
	interval_data = {
	'UNIX_UTC_ts': UNIX_UTC_ts,
	'SP2_mean_mass_conc': float(date_mean),
	'RH_threshold': high_RH_limit,
	'cluster': 'BB',
	'meas_rel_err': 0.18,
	}
			
	cursor.execute(add_interval, interval_data)
	cnx.commit()
	
#####################################################################################
###################GEOS-Chem
					
lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg
level = 9 #0-46 #9 is closest to WHI avg P (WHI 95% CI = 770-793) also note this is level 10 in the vertical feild but we enter 9 here b/c python indexes from 0

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

start_hour = 4
end_hour = 16

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/default/'
os.chdir(data_dir)

for file in os.listdir(data_dir):
	if file.endswith('.hdf'): 
		
		file_year = int(file[2:6])
		file_month = int(file[6:8])
		file_day = int(file[8:10])
		file_hour = int(file[11:13])


		hdf_file = SD(file, SDC.READ)

		GC_hour = datetime(file_year,file_month,file_day,file_hour) 
		GC_hour_PST = GC_hour + timedelta(hours = -8)
		
		if (fire_span2_09s <= GC_hour_PST < fire_span2_09f) or (fire_span1_10s <= GC_hour_PST < fire_span1_10f):
			if  4 <= GC_hour.hour < 16:
				if 4 <= GC_hour.hour < 10:
					int_midpoint = datetime(GC_hour.year,GC_hour.month,GC_hour.day,7) 
				if 10 <= GC_hour.hour < 16:
					int_midpoint = datetime(GC_hour.year,GC_hour.month,GC_hour.day,13) 
							
			
				hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
				hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')

				total_BC_ppbv = hydrophilic_BC[level,lat,lon] + hydrophobic_BC[level,lat,lon]
				BC_conc_ngm3_lvl = total_BC_ppbv*molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	
				
				time_ts = calendar.timegm(int_midpoint.timetuple())

				cursor.execute(('UPDATE whi_gc_and_sp2_6h_mass_concs SET GC_v10_default = %s WHERE UNIX_UTC_6h_midtime = %s and cluster = %s'),(BC_conc_ngm3_lvl,time_ts,'BB'))	
				cnx.commit()

		hdf_file.end()	

	
cnx.close()
	
