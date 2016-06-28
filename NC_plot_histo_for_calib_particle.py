import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates
import matplotlib.mlab as mlab
import calendar

calib_date_start = calendar.timegm(datetime(2015,1,28,0,0,0).utctimetuple())
calib_date_end = calendar.timegm(datetime(2015,1,30,0,0,0).utctimetuple())

calib_date_start2 = calendar.timegm(datetime(2015,4,9,0,0,0).utctimetuple())
calib_date_end2 = calendar.timegm(datetime(2015,4,11,0,0,0).utctimetuple())
calib_particle_type = 'Aquadag'
instr = 'UBCSP2'

sizes = [
#80 ,	
#100 ,  ##
#125 ,
150 ,
200,
#240 ,  ##
250 ,
269 ,  ##
#300 ,
#350 ,  ##
]



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

amps = []
amps2 = []
jan_plot_data=[]
alert_plot_data = []
for size in sizes:
	#cursor.execute(('SELECT actual_scat_amp from polar6_calibration_data where particle_dia = %s and instrument = %s and particle_type = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and actual_scat_amp < %s'),(size,instr,calib_particle_type,calib_date_start,calib_date_end,3800))
	cursor.execute(('SELECT LF_scat_amp from polar6_coating_2015 where particle_dia = %s and instrument = %s and particle_type = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and actual_scat_amp < %s and LF_scat_amp IS NOT NULL'),(size,instr,calib_particle_type,calib_date_start,calib_date_end,3800))
	calib_data = cursor.fetchall()
	print len(calib_data)
	meas_amp   = [row[0] for row in calib_data]
	print 'Jan', np.mean(meas_amp), np.median(meas_amp), np.percentile(meas_amp,25),np.percentile(meas_amp,75)
	amps.append(meas_amp)
	
	#cursor.execute(('SELECT actual_scat_amp from polar6_calibration_data where particle_dia = %s and instrument = %s and particle_type = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and actual_scat_amp < %s'),(size,instr,calib_particle_type,calib_date_start2,calib_date_end2,3800))
	cursor.execute(('SELECT LF_scat_amp from polar6_coating_2015 where particle_dia = %s and instrument = %s and particle_type = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and actual_scat_amp < %s and LF_scat_amp IS NOT NULL'),(size,instr,calib_particle_type,calib_date_start2,calib_date_end2,3800))
	calib_data2 = cursor.fetchall()
	print len(calib_data2)
	meas_amp2   = [row[0] for row in calib_data2]
	print 'Alert', np.mean(meas_amp2), np.median(meas_amp2), np.percentile(meas_amp2,25),np.percentile(meas_amp2,75)
	amps2.append(meas_amp2)

	print 'ratio Jan/Alert', np.mean(meas_amp)/np.mean(meas_amp2), np.median(meas_amp)/np.median(meas_amp2)

	jan_plot_data.append([np.median(meas_amp), np.median(meas_amp)-np.percentile(meas_amp,25),np.percentile(meas_amp,75)-np.median(meas_amp)])
	alert_plot_data.append([np.median(meas_amp2), np.median(meas_amp2)-np.percentile(meas_amp2,25),np.percentile(meas_amp2,75)-np.median(meas_amp2)])
	
	
#plotting
fig = plt.figure()

ax1 = fig.add_subplot(111)

for item in amps:
	ax1.hist(item, bins = 100 , range = (0,4000), normed=True, alpha = 0.75, histtype='step',color = 'r', label = 'Jan')
for item in amps2:
	ax1.hist(item, bins = 100 , range = (0,4000), normed=True, alpha = 0.75, histtype='step',color='b', label = 'Alert')
	#(n, bins, patches) = ax1.hist(item, bins = 100 , normed=True, alpha = 0.75, histtype='step')
	#max = np.argmax(n)
	#print bins[max]

	
	mean = np.mean(item)
	variance = np.var(item)
	sigma = np.sqrt(variance)
	x = np.linspace(min(item), max(item),1000)
	#plt.plot(x,mlab.normpdf(x,mean,sigma))
	#print mean
	
plt.legend()
ax1.set_ylabel('freq')
ax1.set_xlabel('amp')


plt.show()

###
fig = plt.figure()
jan_meds = [row[0] for row in jan_plot_data]
alert_meds = [row[0] for row in alert_plot_data]
jan_25 = [row[1] for row in jan_plot_data]
alert_25 = [row[1] for row in alert_plot_data]
jan_75 = [row[2] for row in jan_plot_data]
alert_75 = [row[2] for row in alert_plot_data]

m,b = np.polyfit(alert_meds, jan_meds, 1)
print m,b
line=[]
for x in range(0,10000):
	y = m*x+b
	line.append([x,y])

ax1 = fig.add_subplot(111)

ax1.errorbar(alert_meds, jan_meds, xerr=[alert_25,alert_75], yerr=[jan_25,jan_75], fmt='o')
ax1.plot([row[0] for row in line],[row[1] for row in line])
ax1.set_ylabel('Jan median LEO scattering amplitude for Aquadag')
ax1.set_xlabel('Alert median LEO scattering amplitude for Aquadag')
ax1.set_ylim(0,2500)
ax1.set_xlim(0,2500)
plt.text(0.7,0.2,'slope = 2.68',transform=ax1.transAxes)

plt.show()

