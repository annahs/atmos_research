import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
from datetime import datetime
import mysql.connector
from coating_info_from_raw_signal import CoatingData
from datetime import timedelta

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

start_date = datetime(2012,3,27)
end_date =   datetime(2012,5,1)
hour_step = 96
lookup_file_2012 = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/lookup_tables/coating_lookup_table_Alert_SP244_2012PSLcalib_F19060.lupckl'
#lookup_file_2012 = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/lookup_tables/coating_lookup_table_Alert_SP258_2012PSLcalib_F10852.lupckl'
#lookup_file_2015 = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/lookup_tables/coating_lookup_table_Alert_SP258_2015PSLcalib_F4062.lupckl'
rBC_density = 1.8 
incand_sat = 50000


while start_date < end_date:
	print start_date
	period_end = start_date + timedelta(hours = hour_step)
	UNIX_time_stamp_start = calendar.timegm(start_date.utctimetuple())
	UNIX_time_stamp_end   = calendar.timegm(period_end.utctimetuple())

	cursor.execute(('SELECT id, BB_incand, LF_scat_amp, LF_ratio_scat_amp from alert_leo_coating_data where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and BB_incand <=%s'),
		(UNIX_time_stamp_start,UNIX_time_stamp_end, incand_sat))	
	data = cursor.fetchall()
	coating_record_2012 = CoatingData(lookup_file_2012,incand_sat)
	coating_record_2015 = CoatingData(lookup_file_2012,incand_sat)
	print 'onward'
	LOG_EVERY_N = 10000
	i = 0




	for row in data:
		row_id = row[0]
		BB_incand = row[1]  #HG
		LF_amp_fit = row[2]
		LF_amp_ratio = row[3]
		
		#calculate masses
		#rBC_mass = 0.41527 + 2.13238E-4*BB_incand + 7.17406E-10*BB_incand*BB_incand  #SP258 HG
		rBC_mass = 0.26887 + 1.9552E-4*BB_incand +  8.31906E-10*BB_incand*BB_incand  #SP244 HG  
				
		rBC_VED = (((rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7
		if rBC_VED >= 65 and rBC_VED <=220:
			if LF_amp_fit < 500000 and LF_amp_fit > 0:
				coat_th_2012 = float(coating_record_2012.get_coating_thickness(rBC_VED,LF_amp_fit))
				coat_th_2015 = float(coating_record_2015.get_coating_thickness(rBC_VED,LF_amp_fit))
				if np.isnan(coat_th_2012):
					coat_th_2012 = None
				if np.isnan(coat_th_2015):
					coat_th_2015 = None
			else:
				coat_th_2012 = None
				coat_th_2015 = None
			
			if LF_amp_ratio < 500000 and LF_amp_ratio > 0:
				coat_th_2012_r = float(coating_record_2012.get_coating_thickness(rBC_VED,LF_amp_ratio))
				coat_th_2015_r = float(coating_record_2015.get_coating_thickness(rBC_VED,LF_amp_ratio))
				if np.isnan(coat_th_2012_r):
					coat_th_2012_r = None
				if np.isnan(coat_th_2015_r):
					coat_th_2015_r = None
			else:
				coat_th_2012_r = None
				coat_th_2015_r = None
		else:
			continue
			
		
		

		cursor.execute(('UPDATE alert_leo_coating_data SET coat_thickness_nm_min = %s, coat_thickness_nm_max = %s,coat_thickness_nm_min_ratio = %s,coat_thickness_nm_max_ratio = %s, rBC_mass_fg = %s WHERE id = %s'),(coat_th_2012,coat_th_2015,coat_th_2012_r,coat_th_2015_r,rBC_mass,row_id))	
		cnx.commit()


		i+=1
		if (i % LOG_EVERY_N) == 0:
			print 'record: ', i
			
	start_date = start_date + timedelta(hours = hour_step)
		
cnx.close()


