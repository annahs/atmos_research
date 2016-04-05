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

calib_stability_uncertainty = 0.1

#fire times
timezone = timedelta(hours = -8)

fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time1_UNIX_UTC_start = float(calendar.timegm((fire_time1[0]-timezone).utctimetuple()))
fire_time1_UNIX_UTC_end = float(calendar.timegm((fire_time1[1]-timezone).utctimetuple()))

fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST
fire_time2_UNIX_UTC_start = float(calendar.timegm((fire_time2[0]-timezone).utctimetuple()))
fire_time2_UNIX_UTC_end = float(calendar.timegm((fire_time2[1]-timezone).utctimetuple()))


############Meaurements
#get full rBC record (in PST and 10 min binned intervals) and put in dictionaries keyed by date 
rBC_24h_data = {} #does not include BB data
rBC_BB_24h_data = {}
rBC_FT_data_cluster_NPac = {}
rBC_FT_data_cluster_SPac = {}
rBC_FT_data_cluster_Cont = {}
rBC_FT_data_cluster_LRT = {}
rBC_FT_data_cluster_GBPS = {}
rBC_FT_data_cluster_BB = {}


##
#select data (spikes already rmoved) and exclude fire times 
SP2_data_query = ('SELECT * FROM whi_sp2_rbc_record_2009to2012_spikes_removed WHERE UNIX_GMT_ts NOT BETWEEN %(fire_time1_start)s AND %(fire_time1_end)s AND UNIX_GMT_ts NOT BETWEEN %(fire_time2_start)s AND %(fire_time2_end)s')
			

query_terms ={
'fire_time1_start':fire_time1_UNIX_UTC_start,
'fire_time1_end':fire_time1_UNIX_UTC_end,
'fire_time2_start':fire_time2_UNIX_UTC_start,
'fire_time2_end':fire_time2_UNIX_UTC_end
}		

cursor.execute(SP2_data_query,query_terms)
SP2_data = cursor.fetchall()

start_hour = 4 #PST 20000
end_hour = 16 #PST 0800

for row in SP2_data:	
	UNIX_UTC_ts = row[8]
	date_time_UTC = datetime.utcfromtimestamp(UNIX_UTC_ts)
	BC_mass_conc = row[3]
	BC_mass_conc_LL = row[4] 
	BC_mass_conc_UL = row[5] 

	#avoid high RH times
	if filter_by_RH == True:
		cursor.execute(('SELECT RH from whi_high_rh_times_2009to2012 where high_RH_start_time <= %s and high_RH_end_time > %s'),(UNIX_UTC_ts,UNIX_UTC_ts))
		RH_data = cursor.fetchall()
		if len(RH_data):
			if RH_data[0] > high_RH_limit:
				continue
		
	#use night only data
	if start_hour <= date_time_UTC.hour < end_hour:
		cursor.execute(('SELECT * from whi_ft_cluster_times_2009to2012 where cluster_start_time <= %s and cluster_end_time >= %s'),(UNIX_UTC_ts,UNIX_UTC_ts))
		cluster_data = cursor.fetchall()
		#we have a few samples from teh first day of 2009 and 2012 that are before our first cluster, so this ignores those . . 
		if len(cluster_data) == 0:
			continue
			
		cluster_midtime = datetime.strptime(cluster_data[0][4], '%Y-%m-%d %H:%M:%S')
		cluster_number = cluster_data[0][3]

		#####get abs err
		if np.isnan(BC_mass_conc_LL):
			abs_err = np.nan
		else:
			abs_err = (BC_mass_conc-BC_mass_conc_LL)
		
				
		#add data to list in cluster dictionaries (1 list per cluster time early night/late night)
		if cluster_number == 9:
			correction_factor_for_massdistr = 1./0.5411
			mass_distr_correction_error = 0.015  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]
			if cluster_midtime in rBC_FT_data_cluster_SPac:
				rBC_FT_data_cluster_SPac[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_SPac[cluster_midtime] = [row_data] 
			
		if cluster_number == 4:
			correction_factor_for_massdistr = 1./0.4028
			mass_distr_correction_error = 0.028  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_Cont:
				rBC_FT_data_cluster_Cont[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_Cont[cluster_midtime] = [row_data]
				
		if cluster_number in [6,8]:
			correction_factor_for_massdistr = 1./0.4626
			mass_distr_correction_error = 0.032  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_SPac:
				rBC_FT_data_cluster_SPac[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_SPac[cluster_midtime] = [row_data]
				
		if cluster_number in [2,7]:
			correction_factor_for_massdistr = 1./0.5280
			mass_distr_correction_error = 0.019  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_LRT:
				rBC_FT_data_cluster_LRT[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_LRT[cluster_midtime] = [row_data]
				
		if cluster_number in [1,3,5,10]:
			correction_factor_for_massdistr = 1./0.3525
			mass_distr_correction_error = 0.015  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_NPac:
				rBC_FT_data_cluster_NPac[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_NPac[cluster_midtime] = [row_data]


##print data set lengths
#for cluster in [rBC_FT_data_cluster_NPac,rBC_FT_data_cluster_SPac,rBC_FT_data_cluster_Cont,rBC_FT_data_cluster_GBPS,rBC_FT_data_cluster_LRT]:				
#	print len(cluster)
#	data_pts = 0
#	for midtime in cluster:
#		data_pts = data_pts + len(cluster[midtime])
#	print data_pts
#	print '\n'
#sys.exit()

#6h rBC-meas avgs (FT data)
SP2_6h_NPac = [] 
SP2_6h_SPac = [] 
SP2_6h_Cont = [] 
SP2_6h_LRT  = [] 
SP2_6h_BB = [] 
SP2_6h_all_non_BB = []

all_dict = {}

#6h means 	
for date, mass_data in rBC_FT_data_cluster_NPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_NPac.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]
		
for date, mass_data in rBC_FT_data_cluster_SPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_SPac.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]
	
for date, mass_data in rBC_FT_data_cluster_Cont.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_Cont.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])

	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]
	
for date, mass_data in rBC_FT_data_cluster_LRT.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_LRT.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]


	
for date, mass_data in rBC_FT_data_cluster_BB.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_BB.append([date_mean,date_mean_err])	
	
	


	
###################GEOS-Chem


##sampling times
sampling_times_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/WHI_SP2_6h_rBC_mass_concs.txt'
sampling_times = []
with open(sampling_times_file,'r') as f:
	f.readline()
	for line in f:
		newline = line.split()
		sampling_date = newline[0]
		sampling_time = newline[1]
		sampling_datetime = datetime(int(sampling_date[0:4]),int(sampling_date[5:7]),int(sampling_date[8:10]),int(sampling_time[0:2]))
		sampling_times.append(sampling_datetime+timedelta(hours=8))  #get into UTC




GC_data = {}

GC_runs = ['default','Vancouver_emission','wet_scavenging','no_biomass','All_together']

lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg
level = 9 #1-47 #9 is closest to WHI avg P (WHI 95% CI = 770-793)

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

#start_hour = 3
#end_hour = 15
GC_run = 'default' #the runs are 'default','Vancouver_emission','wet_scavenging','no_biomass','All_together'
print GC_run
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/' + GC_run +'/'
os.chdir(data_dir)
for file in os.listdir(data_dir):
	if file.endswith('.hdf'): 
		
		file_year = int(file[2:6])
		file_month = int(file[6:8])
		file_day = int(file[8:10])
		file_hour = int(file[11:13])
		GC_datetime = datetime(file_year,file_month,file_day,file_hour)
		GC_UNIX_UTC_ts = calendar.timegm(GC_datetime.utctimetuple())
		
		
		#avoid high RH times
		if filter_by_RH == True:
			cursor.execute(('SELECT RH from whi_high_rh_times_2009to2012 where high_RH_start_time <= %s and high_RH_end_time > %s'),(GC_UNIX_UTC_ts,GC_UNIX_UTC_ts))
			RH_data = cursor.fetchone()
			if RH_data != None:
				if RH_data[0] > high_RH_limit:
					continue
		
		############
		
		if start_hour <= file_hour < end_hour:  #ignore any times not in the 2000-0800 PST window (0400-1600 UTC)
			hdf_file = SD(file, SDC.READ)
	
			if start_hour <= file_hour < (start_hour+6):
				period_midtime = datetime(file_year,file_month,file_day,7)
				period_starttime = datetime(file_year,file_month,file_day,4)
				period_endtime = datetime(file_year,file_month,file_day,10)
				
			if (start_hour+6) <= file_hour < end_hour:	
				period_midtime = datetime(file_year,file_month,file_day,13)  
				period_starttime = datetime(file_year,file_month,file_day,10)
				period_endtime = datetime(file_year,file_month,file_day,16)
			
			GC_CO = hdf_file.select('IJ-AVG-$::CO') #3d CO data in ppbv (molBC/molAIR)
			CO_ppbv = GC_CO[level,lat,lon]
			GC_CO_lvl = CO_ppbv#*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	

			if period_midtime in all_dict:  #this excludes BB times already
				if period_midtime not in GC_data:
					GC_data[period_midtime] = []
				GC_data[period_midtime].append(CO_ppbv)
							

			hdf_file.end()


#query to add 6h mass ocnc data
add_6h_data = ('INSERT INTO whi_gc_co_data'
              '(UNIX_UTC_start_time,UNIX_UTC_end_time,CO_ppbv,RH_threshold,GC_scenario)'
              'VALUES (%(UNIX_UTC_start_time)s,%(UNIX_UTC_end_time)s,%(CO_ppbv)s,%(RH_threshold)s,%(GC_scenario)s)'
			  )


			  
#get the means for each 6-h period
for period_midtime in GC_data:
		period_starttime = period_midtime - timedelta(hours = 3)
		period_endtime = period_midtime + timedelta(hours = 3)
		CO_mean = np.mean(GC_data[period_midtime])
		
		CO_data = {
		'UNIX_UTC_start_time':float(calendar.timegm(period_starttime.utctimetuple())),
		'UNIX_UTC_end_time':float(calendar.timegm(period_endtime.utctimetuple())),
		'CO_ppbv':float(CO_mean),
		'RH_threshold':high_RH_limit,
		'GC_scenario': GC_run,
		}

		cursor.execute(('''UPDATE whi_gc_co_data SET CO_ppbv = %(CO_ppbv)s 
						   WHERE UNIX_UTC_start_time = %(UNIX_UTC_start_time)s AND UNIX_UTC_end_time = %(UNIX_UTC_end_time)s and GC_scenario = %(GC_scenario)s and RH_threshold = %(RH_threshold)s'''),(CO_data))	

		#cursor.execute(add_6h_data, CO_data)
		cnx.commit()	




cnx.close()



