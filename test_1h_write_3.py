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



SP2_ID = 44
saved_1_of_every = 8
start = datetime(2013,8,1)
end =   datetime(2013,9,22)
timestep = 1 #hours
sample_min = 117
sample_max = 123
yag_min = 1.5
yag_max = 7

UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

file_data = []
	
while start <= end:
	print start
	UNIX_start = calendar.timegm(start.utctimetuple())
	UNIX_end = UNIX_start + timestep*3600
	start_t = datetime.now()
	cursor.execute('''(SELECT 
	mn.UNIX_UTC_ts_int_start,
	mn.UNIX_UTC_ts_int_end,
	mn.BB_incand_HG,
	mn.BB_incand_LG,
	hk.sample_flow
	FROM alert_mass_number_data_2013 mn
	FORCE INDEX (time_binning) 
	JOIN alert_hk_data hk on mn.hk_id = hk.id
	WHERE
	mn.UNIX_UTC_ts_int_start >= %s
	AND mn.UNIX_UTC_ts_int_end < %s
	AND hk.sample_flow >= %s
	AND hk.sample_flow < %s
	AND hk.yag_power >= %s
	AND hk.yag_power < %s)''',
	(UNIX_start,UNIX_end,sample_min,sample_max,yag_min,yag_max))
	
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
		bbhg_mass_uncorr = 0.18821 + 1.36864E-4*bbhg_incand_pk_amp + 5.82331E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  #SP244
		bbhg_mass_uncertainty_uncorr = 0.05827 + 7.26841E-6*bbhg_incand_pk_amp + 1.43898E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp #SP244
		
		bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
		bbhg_mass_only_rel_err = bbhg_mass_uncertainty_uncorr/bbhg_mass_uncorr
		bbhg_ADcorr_rel_err = (0.05/0.7)
		bbhg_mass_abs_uncertainty_corr = (bbhg_ADcorr_rel_err + bbhg_mass_only_rel_err) * bbhg_mass_corr
		
		masses['rBC_mass_fg_HG_low'].append(bbhg_mass_corr)  
		mass_uncertainties['rBC_mass_fg_HG_low'].append(bbhg_mass_abs_uncertainty_corr)  
				
	loop_end = datetime.now()			
	print 'loop end', (loop_end-start_t)
	
	tot_rBC_mass_fg_HG_low =  sum(masses['rBC_mass_fg_HG_low'])
	tot_rBC_mass_uncer_HG_low =  sum(mass_uncertainties['rBC_mass_fg_HG_low'])
	rBC_number_HG_low =  len(masses['rBC_mass_fg_HG_low'])
	
	ind_mass_tot = ind_mass_tot + tot_rBC_mass_fg_HG_low
	ind_mass_uncer_tot = ind_mass_uncer_tot + tot_rBC_mass_uncer_HG_low
	ind_number_tot = ind_number_tot + rBC_number_HG_low
	
	if total_sample_vol == 0:
		file_data.append([start,start + timedelta(hours = timestep), np.nan, np.nan, np.nan,total_sample_vol])
	else:
		file_data.append([start,start + timedelta(hours = timestep), ind_mass_tot*saved_1_of_every/total_sample_vol,ind_mass_uncer_tot*saved_1_of_every/total_sample_vol,ind_number_tot*saved_1_of_every/total_sample_vol,total_sample_vol])
		
	next_hour = start + timedelta(hours = timestep)

	#if this is the last hour of the day write to file
	if next_hour.day != start.day:
		if start.month <10:
			month_prefix = '0'
		else:
			month_prefix = ''
			
		if start.day < 10:
			file_name = str(start.year) + month_prefix + str(start.month) + '0' + str(start.day) + ' - hourly mass and number concentration'
		else:
			file_name = str(start.year) + month_prefix + str(start.month) + str(start.day) + ' - hourly mass and number concentration'
		file = open('C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013/' + file_name +'.txt', 'w')
		file.write('mass and number concentration for SP2#' + str(SP2_ID)+  ' at Alert \n')
		file.write('all concentrations have been corrected for sampling filter set at 1 of Every ' + str(saved_1_of_every) + ' particles saved \n')
		file.write('interval_start(UTC) \t interval_end(UTC) \t rBC_mass_concentration(ng/m3) \t rBC_mass_concentration_uncertainty(ng/m3) \t rBC_number_concentration(#/cm3) \t sampling_volume(cc) \n')
		for row in file_data:
			line = '\t'.join(str(x) for x in row)
			file.write(line + '\n')
		file.close()
		file_data = []
		
	start += timedelta(hours = timestep)
	
	
cnx.close()

#ind_dates = [row[0] for row in file_data]	
#ind_mass_tots = [row[2] for row in file_data]	
#ind_mass_uncer_tots = [row[3] for row in file_data]	
#ind_number_tots = [row[4] for row in file_data]
#
#	
#hfmt = dates.DateFormatter('%Y%m%d %H:%M')
#
#fig = plt.figure()
#ax1 = fig.add_subplot(211)
#ax1.xaxis.set_major_formatter(hfmt)
#ax1.plot(ind_dates,ind_number_tots,'-ro')
#
#
#ax2 = fig.add_subplot(212)
#ax2.xaxis.set_major_formatter(hfmt)
#ax2.errorbar(ind_dates,ind_mass_tots,yerr = ind_mass_uncer_tots,color = 'r', marker = 'o')
#
#
#
#plt.show()