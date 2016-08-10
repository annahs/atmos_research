import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
import collections
import calendar
import mysql.connector

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#fire times
timezone = timedelta(hours = -8)
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M')+timezone, datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')+timezone] #row_datetimes following Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M')+timezone, datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')+timezone] #jason's BC clear report #PST


start = datetime(2009,7,1,4)  #2009 - 20090628  2010 - 20100610   2012 - 20100405
end =   datetime(2009,8,16)  #2009 - 20090816  2010 - 20100726   2012 - 20100601
UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

cursor.execute('''(SELECT 
	UNIX_UTC_start_time,
	rBC_mass_conc,
	sampling_duration,
	number_particles
	FROM whi_sp2_2min_data
	WHERE
	UNIX_UTC_start_time >= %s
	AND	UNIX_UTC_start_time < %s
	AND id > %s
	)''',
	(UNIX_start,UNIX_end,0))	

#cursor.execute('''(SELECT 
#	UNIX_UTC_start_time,
#	rBC_mass,
#	volume_air_sampled,
#	whi_sampling_cond_id
#	FROM whi_sp2_hourly_data 
#	WHERE
#	UNIX_UTC_start_time >= %s
#	AND	UNIX_UTC_start_time < %s
#	AND volume_air_sampled >%s
#	)''',
#	(UNIX_start,UNIX_end,0))	
	
new_data = cursor.fetchall()



cursor.execute('''(SELECT 
	UNIX_GMT_ts,
	BC_mass_conc,
	interval_sampling_duration,
	interval_incand_count
	FROM whi_sp2_rbc_record_2009to2012_spikes_removed 
	WHERE
	UNIX_GMT_ts >= %s
	AND	UNIX_GMT_ts < %s
	)''',
	(UNIX_start,UNIX_end))	
	#AND (hy.cluster_number_6h = %s OR hy.cluster_number_6h = %s OR hy.cluster_number_6h = %s OR hy.cluster_number_6h = %s)

old_data = cursor.fetchall()

new_plot_data = []
for row in new_data:
	mid_date_time = datetime.utcfromtimestamp(row[0]+1800)
	new_mass_conc = row[1]/0.4
	new_duration = row[2]
	new_number  = row[3]
	new_plot_data.append([dates.date2num(mid_date_time),new_mass_conc,new_number,new_duration])
	
old_plot_data = []
for row in old_data:
	mid_date_time = datetime.utcfromtimestamp(row[0])
	old_mass_conc = row[1]
	old_duration = row[2]
	old_number  = row[3]
	old_plot_data.append([dates.date2num(mid_date_time),old_mass_conc,old_number,old_duration])
	
new_dates =     [row[0] for row in new_plot_data]
new_mass_conc = [row[1] for row in new_plot_data]
new_number =    [row[2] for row in new_plot_data]
new_d =    [row[3] for row in new_plot_data]

old_dates =     [row[0] for row in old_plot_data]
old_mass_conc = [row[1] for row in old_plot_data]
old_number =    [row[2] for row in old_plot_data]
old_d =    [row[3] for row in old_plot_data]

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.plot(new_dates,new_mass_conc,color = 'b',linestyle = '--',marker = 'o')
ax1.scatter(old_dates,old_mass_conc,color = 'r',linestyle = '--')
#ax1.set_xlim(0,300)
#ax1.set_ylim(0,60)
ax1.set_ylabel('mass conc')

#ax2 = fig.add_subplot(212)
#ax2.scatter(new_dates,new_number,color = 'b',linestyle = '--')
#ax2.scatter(old_dates,old_number,color = 'r',linestyle = '--')
##ax2.set_xlim(0,300)
##ax2.set_ylim(0,60)
#ax1.set_ylabel('number')


plt.show()	


cnx.close()
