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
start = datetime(2012,3,27)
end =   datetime(2013,1,1)
avg_period = 20 #days

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

list = []


date = start
while date < end:
	month_end = date + timedelta(days = avg_period)
	UNIX_start = calendar.timegm(date.utctimetuple())
	UNIX_end = calendar.timegm(month_end.utctimetuple())
	cursor.execute(('SELECT FF_gauss_width,FF_peak_posn,actual_zero_x_posn,FF_scat_amp,LF_scat_amp,LF_ratio_scat_amp FROM alert_leo_params_from_nonincands WHERE instrument_ID =%s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(SP2_ID,UNIX_start,UNIX_end))
	data = cursor.fetchall()
	
	
	FF_width = np.mean([row[0] for row in data])
	FF_width = np.mean([row[0] for row in data])
	FF_zerox_to_pk =np.mean([(row[2]-row[1]) for row in data])
	FF_zerox_to_pk =np.mean([(row[2]-row[1]) for row in data])
	actual_scat_amp = np.mean([row[3] for row in data])
	
	LF_scat_amps = []
	LF_ratio_scat_amps = []
	for row in data:
		LF_scat_amp = row[4] 
		LF_ratio_scat_amp = row[5] 
		if LF_scat_amp != None:
			LF_scat_amps.append(LF_scat_amp)
		if LF_ratio_scat_amp != None:
			LF_ratio_scat_amps.append(LF_scat_amp)
	
	LF_scat_amp_mean = np.mean(LF_scat_amps)
	LF_ratio_scat_amp_mean = np.mean(LF_ratio_scat_amps)
	#print [(date + timedelta(days = avg_period/2)),FF_width,FF_zerox_to_pk,actual_scat_amp,LF_scat_amp_mean,LF_ratio_scat_amp_mean]
	list.append([(date + timedelta(days = avg_period/2)),FF_width,FF_zerox_to_pk,actual_scat_amp,LF_scat_amp_mean,LF_ratio_scat_amp_mean])
	date = date + timedelta(days = avg_period)
	
cnx.close()	
plot_dates = [dates.date2num(row[0]) for row in list]
FF_width = [row[1] for row in list]
FF_zerox_to_pk = [row[2] for row in list]
actual_scat_amp = [row[3] for row in list]
LF_scat_amp = [row[4] for row in list]
LF_ratio_scat_amp = [row[5] for row in list]
print actual_scat_amp

hfmt = dates.DateFormatter('%Y %b')
display_month_interval = 1

#fit params
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax1.xaxis.set_major_formatter(hfmt)
ax1.plot(plot_dates,FF_width,marker = 'o', color = 'b',label = 'Gauss width')
ax1.set_ylim(6,10)
ax1.set_ylabel('FF Gauss width')


ax2 = fig.add_subplot(212)
ax2.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax2.xaxis.set_major_formatter(hfmt)
ax2.plot(plot_dates,FF_zerox_to_pk,marker = 's', color = 'g',label = 'zero X to Peak')
ax2.set_ylim(-10,-6)
ax2.set_ylabel('FF zero X to Peak')


plt.show()

#LF VS FF
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax1.xaxis.set_major_formatter(hfmt)
ax1.plot(plot_dates,actual_scat_amp,marker = 'o', color = 'b',label = 'actual_scat_amp')
ax1.plot(plot_dates,LF_scat_amp,marker = 'o', color = 'g',label = 'LF_scat_amp')
ax1.plot(plot_dates,LF_ratio_scat_amp,marker = 'o', color = 'r',label = 'LF_ratio_scat_amp')
ax1.set_ylim(0,60000)
#ax1.set_ylabel('FF Gauss width')
plt.legend()

plt.show()