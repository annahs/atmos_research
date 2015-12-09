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

calib_date_start = calendar.timegm(datetime(2015,1,29,0,0,0).utctimetuple())
calib_date_end = calendar.timegm(datetime(2015,1,30,0,0,0).utctimetuple())

calib_date_start2 = calendar.timegm(datetime(2015,4,9,0,0,0).utctimetuple())
calib_date_end2 = calendar.timegm(datetime(2015,4,10,0,0,0).utctimetuple())
parameter_to_plot = 'actual_scat_amp' #'incand_amp'
calib_particle_type = 'PSL'
instr = 'UBCSP2'

sizes = [
#80 ,	
#100 ,  ##
#125 ,
#150 ,
#200,
#240 ,  ##
#250 ,
269 ,  ##
#300 ,
#350 ,  ##
]



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

amps = []
amps2 = []

for size in sizes:
	#cursor.execute(('SELECT %s from polar6_calibration_data where particle_dia = %s and instrument = %s and incand_amp > %s and incand_amp < %s and UNIX_UTC_ts > %s'),(parameter_to_plot,size,'UBCSP2',150,360, calib_date))
	cursor.execute(('SELECT actual_scat_amp from polar6_calibration_data where particle_dia = %s and instrument = %s and particle_type = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and actual_scat_amp < %s'),(size,instr,calib_particle_type,calib_date_start,calib_date_end,3800))
	calib_data = cursor.fetchall()
	print len(calib_data)
	meas_amp   = [row[0] for row in calib_data]
	amps.append(meas_amp)
	
	cursor.execute(('SELECT actual_scat_amp from polar6_calibration_data where particle_dia = %s and instrument = %s and particle_type = %s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and actual_scat_amp < %s'),(size,instr,calib_particle_type,calib_date_start2,calib_date_end2,3800))
	calib_data2 = cursor.fetchall()
	print len(calib_data2)
	meas_amp2   = [row[0] for row in calib_data2]
	amps2.append(meas_amp2)
##


#plotting
fig = plt.figure()

ax1 = fig.add_subplot(111)

for item in amps:
	ax1.hist(item, bins = 100 , normed=True, alpha = 0.75, histtype='step',color = 'r', label = 'Jan')
for item in amps2:
	ax1.hist(item, bins = 100 , normed=True, alpha = 0.75, histtype='step',color='b', label = 'Alert')
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

