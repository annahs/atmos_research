import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import calendar
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib import dates



SP2_ID = 58
saved_1_of_every = 10
start = datetime(2014,1,15)
end =   datetime(2014,3,1)
timestep = 1 #hours


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

file_data = []
	
while start <= end:
	print start
	UNIX_start = calendar.timegm(start.utctimetuple())
	UNIX_end = UNIX_start + timestep*3600
	
	cursor.execute('''(SELECT 
	mn.UNIX_UTC_ts_int_start,
	mn.UNIX_UTC_ts_int_end,
	mn.BB_incand_HG,
	mn.BB_incand_LG,
	hk.sample_flow
	FROM alert_mass_number_data_2014 mn
	JOIN alert_hk_data hk on mn.hk_id = hk.id
	WHERE
	mn.UNIX_UTC_ts_int_start >= %s
	AND mn.UNIX_UTC_ts_int_end < %s)''',
	(UNIX_start,UNIX_end))
	
	masses={
	'rBC_mass_fg_HG_low':[],
	'rBC_mass_fg_HG_high':[],
	'rBC_mass_fg_LG_low':[],
	'rBC_mass_fg_LG_high':[],
	}
	
	mass_uncertainties={
	'rBC_mass_fg_HG_low':[],
	'rBC_mass_fg_HG_high':[],
	'rBC_mass_fg_LG_low':[],
	'rBC_mass_fg_LG_high':[],
	}
	
	ind_data = cursor.fetchall()
	ind_mass_tot = 0
	ind_mass_uncer_tot = 0
	ind_number_tot = 0
	total_sample_vol = 0
	for row in ind_data:
		ind_start_time = row[0]
		ind_end_time = row[1]
		bbhg_incand_pk_amp = row[2]
		bblg_incand_pk_amp = row[3]
		sample_flow = row[4]  #in vccm
		if sample_flow == None:
			print 'no flow'
			continue
		sample_vol =  (sample_flow*(ind_end_time-ind_start_time)/60)    #/60 b/c sccm and time in secs  0.87 = STP corr?????
		total_sample_vol = total_sample_vol + sample_vol
		
		#calculate masses and uncertainties
		#HG
		bbhg_mass_uncorr = 0.29069 + 1.49267E-4*bbhg_incand_pk_amp + 5.02184E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  
		bbhg_mass_uncertainty_uncorr = 0.06083 + 7.67522E-6*bbhg_incand_pk_amp + 1.60111E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp
		
		bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
		bbhg_mass_only_rel_err = bbhg_mass_uncertainty_uncorr/bbhg_mass_uncorr
		bbhg_ADcorr_rel_err = (0.05/0.7)
		bbhg_mass_abs_uncertainty_corr = (bbhg_ADcorr_rel_err + bbhg_mass_only_rel_err) * bbhg_mass_corr
		
		#LG
		bblg_mass_uncorr = -0.15884 + 0.00176*bblg_incand_pk_amp + 3.19118E-8*bblg_incand_pk_amp*bblg_incand_pk_amp
		bblg_mass_uncertainty_uncorr = 0.47976 + 1.93451E-4*bblg_incand_pk_amp + 1.53274E-8*bblg_incand_pk_amp*bblg_incand_pk_amp
		
		bblg_mass_corr = bblg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
		bblg_mass_only_rel_err = bblg_mass_uncertainty_uncorr/bblg_mass_uncorr
		bblg_ADcorr_rel_err = (0.05/0.7)
		bblg_mass_abs_uncertainty_corr = (bblg_ADcorr_rel_err + bblg_mass_only_rel_err) * bblg_mass_corr
		
		if 0.33 <= bbhg_mass_corr < 1.8:
			masses['rBC_mass_fg_HG_low'].append(bbhg_mass_corr)  
			mass_uncertainties['rBC_mass_fg_HG_low'].append(bbhg_mass_abs_uncertainty_corr)  
		if 1.8 <= bbhg_mass_corr < 12.8:
			masses['rBC_mass_fg_HG_high'].append(bbhg_mass_corr)
			mass_uncertainties['rBC_mass_fg_HG_high'].append(bbhg_mass_abs_uncertainty_corr)
		if 1.8 <= bblg_mass_corr < 12.8:
			masses['rBC_mass_fg_LG_low'].append(bblg_mass_corr)
			mass_uncertainties['rBC_mass_fg_LG_low'].append(bblg_mass_abs_uncertainty_corr)
		if 12.8 <= bblg_mass_corr < 41:
			masses['rBC_mass_fg_LG_high'].append(bblg_mass_corr)		
			mass_uncertainties['rBC_mass_fg_LG_high'].append(bblg_mass_abs_uncertainty_corr)		
	
	tot_rBC_mass_fg_HG_low =  sum(masses['rBC_mass_fg_HG_low'])
	tot_rBC_mass_uncer_HG_low =  sum(mass_uncertainties['rBC_mass_fg_HG_low'])
	rBC_number_HG_low =  len(masses['rBC_mass_fg_HG_low'])
	
	tot_rBC_mass_fg_HG_high = sum(masses['rBC_mass_fg_HG_high'])
	tot_rBC_mass_uncer_HG_high = sum(mass_uncertainties['rBC_mass_fg_HG_high'])
	rBC_number_HG_high = len(masses['rBC_mass_fg_HG_high'])
	
	tot_rBC_mass_fg_LG_low =  sum(masses['rBC_mass_fg_LG_low'])
	tot_rBC_mass_fg_uncer_low =  sum(mass_uncertainties['rBC_mass_fg_LG_low'])
	rBC_number_LG_low = len(masses['rBC_mass_fg_LG_low'])
	
	tot_rBC_mass_fg_LG_high = sum(masses['rBC_mass_fg_LG_high'])
	tot_rBC_mass_fg_uncer_high = sum(mass_uncertainties['rBC_mass_fg_LG_high'])
	rBC_number_LG_high = len(masses['rBC_mass_fg_LG_high'])

	ind_mass_tot = ind_mass_tot + (tot_rBC_mass_fg_HG_low + (tot_rBC_mass_fg_HG_high+tot_rBC_mass_fg_LG_low)/2 + tot_rBC_mass_fg_LG_high)
	ind_mass_uncer_tot = ind_mass_uncer_tot + (tot_rBC_mass_uncer_HG_low + (tot_rBC_mass_uncer_HG_high+tot_rBC_mass_fg_uncer_low)/2 + tot_rBC_mass_fg_uncer_high)
	ind_number_tot = ind_number_tot + (rBC_number_HG_low + (rBC_number_HG_high+rBC_number_LG_low)/2 + rBC_number_LG_high)
	
	if total_sample_vol == 0:
		file_data.append([start,start + timedelta(hours = timestep), np.nan, np.nan, np.nan,total_sample_vol])
	else:
		file_data.append([start,start + timedelta(hours = timestep), ind_mass_tot*saved_1_of_every/total_sample_vol,ind_mass_uncer_tot*saved_1_of_every/total_sample_vol,ind_number_tot*saved_1_of_every/total_sample_vol,total_sample_vol])
		
	next_hour = start + timedelta(hours = timestep)

	#if this is the last hour of the day write to file
	if next_hour.day != start.day:
		if start.day < 10:
			file_name = str(start.year) + '0' +  str(start.month) + '0' + str(start.day) + ' - hourly mass and number concentration'
		else:
			file_name = str(start.year) + '0' +  str(start.month) + str(start.day) + ' - hourly mass and number concentration'
		file = open('C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/' + file_name +'.txt', 'w')
		file.write('mass and number concentration for SP2#58 at Alert \n')
		file.write('all concentrations have been corrected for sampling filter set at 1 of Every ' + str(saved_1_of_every) + ' particles saved \n')
		file.write('interval_start(UTC) \t interval_end(UTC) \t rBC_mass_concentration(ng/m3) \t rBC_mass_concentration_uncertainty(ng/m3) \t rBC_number_concentration(#/cm3) \t sampling_volume(cc) \n')
		for row in file_data:
			line = '\t'.join(str(x) for x in row)
			file.write(line + '\n')
		file.close()
		file_data = []
		
	start += timedelta(hours = timestep)
	
	
cnx.close()
