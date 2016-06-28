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

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

calib_stability_uncertainty = 0.1

#fire times
timezone = timedelta(hours = -8)

fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M')+timezone, datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')+timezone] #row_datetimes following Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M')+timezone, datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')+timezone] #jason's BC clear report #PST

start = datetime(2009,6,28)  #2009 - 20090628  2010 - 20100610   2012 - 20100405
end =   datetime(2012,6,1)  #2009 - 20090816  2010 - 20100726   2012 - 20100601
timestep = 24 

data_6h = []
while start <= end:
	print start
	UNIX_start = calendar.timegm(start.utctimetuple())
	UNIX_end = UNIX_start + timestep*3600 
	cursor.execute('''(SELECT 
		hrly.UNIX_UTC_start_time,
		hrly.rBC_mass,
		hrly.volume_air_sampled,
		hrly.sample_factor,
		gc.def_BC	
		FROM whi_sp2_hourly_data hrly
		JOIN whi_hysplit_hourly_data hy on hrly.hysplit_hourly_id = hy.id
		JOIN whi_sampling_conditions met on hrly.whi_sampling_cond_id = met.id
		JOIN whi_gc_hourly_bc_data gc on hrly.gc_hourly_id = gc.id
		WHERE
		hrly.UNIX_UTC_start_time >= %s
		AND hrly.UNIX_UTC_start_time < %s
		AND met.RH <= %s
		
		)''',
		(UNIX_start,UNIX_end,90))	
	hrly_data = cursor.fetchall()

	corr_factor_for_massdistr = 1./0.3525	
	R = 8.3144621 # in m3*Pa/(K*mol)
	early_concs = []
	late_concs = []
	for row in hrly_data:
		date_time = datetime.utcfromtimestamp(row[0])
		sp2_mass = row[1]
		sp2_vol  = row[2]
		sp2_sample_factor  = row[3]
		gc_default = row[4] #ng/m3
		if (4 <= date_time.hour < 16): #nighttime data only
			if (fire_time1[0] <= date_time < fire_time1[1]) or (fire_time2[0] <= date_time < fire_time2[1]): #skip bb times
				continue
			if sp2_vol == 0:
				print 'no_vol'
				continue
			
			sp2_conc = ((sp2_mass/sp2_vol)*(101325/(R*273))*corr_factor_for_massdistr)60 #ng/m3
			
			if (4 <= date_time.hour < 10):
				early_concs.append([sp2_conc,gc_default])
			if (10 <= date_time.hour < 16):
				late_concs.append([sp2_conc,gc_default])
			
	early_sp2 = np.mean([row[0] for row in early_concs ])
	early_gcd = np.mean([row[1] for row in early_concs ])
	data_6h.append([early_sp2,early_gcd])	
	
	late_sp2 = np.mean([row[0] for row in late_concs])
	late_gcd = np.mean([row[1] for row in late_concs])	
	data_6h.append([late_sp2,late_gcd])		
			
	start += timedelta(hours = timestep)
	
sp2 = [row[0] for row in data_6h]
gcd = [row[1] for row in data_6h]

fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.hist(sp2,bins=22,range = (0,300),color = 'b')
ax1.set_xlim(0,280)
ax1.set_ylim(0,60)
ax1.set_ylabel('freq')
ax1.set_xlabel('mass conc')

ax2 = fig.add_subplot(212)
ax2.hist(gcd,bins=22,range = (0,300),color = 'r')
ax2.set_xlim(0,280)
ax2.set_ylim(0,60)
ax2.set_ylabel('freq')
ax2.set_xlabel('mass conc')
plt.show()	


cnx.close()



