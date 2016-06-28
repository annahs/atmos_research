import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math


SP2_ID = 17
timestep = 24 #hours
size_incr = 10 #nm    
start = datetime(2011,1,1)
end =   datetime(2012,1,1)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

bins={}
for i in range(80,240,20):
	bins[i] = []


file_data = []
	
while start <= end:
	print start
	UNIX_start = calendar.timegm(start.utctimetuple())
	UNIX_end = UNIX_start + timestep*3600
	
	start += timedelta(days = 2)

	cursor.execute('''(SELECT 
		BB_incand_HG,
		NB_incand_HG
		FROM alert_mass_number_data_2011
		FORCE INDEX (time_binning)
		WHERE
		UNIX_UTC_ts_int_start >= %s
		AND UNIX_UTC_ts_int_end < %s)''',
		(UNIX_start,UNIX_end))
	data  = cursor.fetchall()
	
	for row in data:
		bbhg_incand_pk_amp = row[0]
		nbhg_incand_pk_amp = row[1]
		
		if nbhg_incand_pk_amp !=0:
			ratio = bbhg_incand_pk_amp/nbhg_incand_pk_amp
			
			bbhg_mass_uncorr = -0.017584 + 0.00647*bbhg_incand_pk_amp #SP217
			#bbhg_mass_uncorr = 0.29069 + 1.49267E-4*bbhg_incand_pk_amp + 5.02184E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  #SP258
			#bbhg_mass_uncorr = 0.18821 + 1.36864E-4*bbhg_incand_pk_amp + 5.82331E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  #SP244
			bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05

			VED = (((bbhg_mass_corr/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm

			for bin in bins:
				if bin <= VED < (bin+10):
					bins[bin].append(ratio)
				
	for bin in bins:
		avg_ratio = float(np.mean(bins[bin]))
		if np.isnan(avg_ratio):
			avg_ratio = None
		bins[bin] = avg_ratio
	
	#put data into database
	add_interval = ('''INSERT INTO alert_color_ratios (		
		SP2_ID, 
		UNIX_UTC_ts_int_start,  
		UNIX_UTC_ts_int_end,  
		ratio_80_90, 
		ratio_100_110, 
		ratio_120_130, 
		ratio_140_150, 
		ratio_160_170, 
		ratio_180_190, 
		ratio_200_210, 
		ratio_220_230
		)
		VALUES (
		%(instrument_ID)s,
		%(UNIX_UTC_ts_int_start)s,
		%(UNIX_UTC_ts_int_end)s,
		%(ratio_80_90)s,
		%(ratio_100_110)s,
		%(ratio_120_130)s,
		%(ratio_140_150)s,
		%(ratio_160_170)s,
		%(ratio_180_190)s,
		%(ratio_200_210)s,
		%(ratio_220_230)s
		)''')
				
	interval_data = {
	'instrument_ID':SP2_ID,
	'UNIX_UTC_ts_int_start':UNIX_start,
	'UNIX_UTC_ts_int_end':UNIX_end,
	'ratio_80_90':bins[80],
	'ratio_100_110':bins[100],
	'ratio_120_130':bins[120],
	'ratio_140_150':bins[140],
	'ratio_160_170':bins[160],
	'ratio_180_190':bins[180],
	'ratio_200_210':bins[200],
	'ratio_220_230':bins[220]
	}
	
	for bin in bins:
		bins[bin] = []
	
	cursor.execute(add_interval, interval_data)

	cnx.commit()

cnx.close()
