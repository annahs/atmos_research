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
from mpl_toolkits.basemap import Basemap
import calendar
from scipy.optimize import curve_fit


bin_min = 245
bin_max = 265

start_time = datetime(2012,7,25,8,0)
end_time = datetime(2012,7,29,8,0)

print start_time
print end_time


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

data = []
current_time = start_time
while current_time <= end_time:
	UNIX_current_time = calendar.timegm(current_time.utctimetuple())
	UNIX_interval_end_time = UNIX_current_time + 3600
	
	cursor.execute(('''SELECT avg(value) FROM whi_smps_data 
						WHERE UNIX_UTC_start_time >= %s 
						AND UNIX_UTC_end_time <= %s 
						AND bin_lower_limit_nm >= %s 
						AND bin_upper_limit_nm <=%s 
						AND binned_property = %s'''),
						(UNIX_current_time, UNIX_interval_end_time,bin_min,bin_max,'nonincand_number_per_cc'))
	nonincand_number = cursor.fetchall()
	nonincand_number_mean = nonincand_number[0][0] 

	cursor.execute(('''SELECT avg(value) FROM whi_smps_data 
						WHERE UNIX_UTC_start_time >= %s 
						AND UNIX_UTC_end_time <= %s 
						AND bin_lower_limit_nm >= %s 
						AND bin_upper_limit_nm <=%s 
						AND binned_property = %s'''),
						(UNIX_current_time, UNIX_interval_end_time,bin_min,bin_max,'SMPS_number_per_cc'))
	SMPS_number = cursor.fetchall()
	SMPS_number_mean = SMPS_number[0][0] 

	
	if nonincand_number_mean != None and nonincand_number_mean != 0:
		ratio = SMPS_number_mean*1.0/nonincand_number_mean
	else:
		ratio = np.nan
		
	data.append([current_time, nonincand_number_mean,SMPS_number_mean, ratio])
	current_time = current_time + timedelta(minutes=60)

data.append([datetime(2012,7,26,9),np.nan,np.nan,np.nan])
data.sort()
pprint(data)
	
##plotting
	
plot_time = [dates.date2num((row[0]-timedelta(hours=8))) for row in data]
smps = [row[2] for row in data]
sp2 = [row[1] for row in data]
ratio = [row[3] for row in data]
hfmt = dates.DateFormatter('%b %d %H:%M')	

fig = plt.figure(figsize=(10,12))
ax1 = plt.subplot(3, 1, 1)
ax1.plot(plot_time,smps ,marker = 'o',color='b')
ax1.xaxis.set_major_formatter(hfmt)
ax1.set_ylabel('SMPS #/cc')


ax2 = plt.subplot(3, 1, 2)
ax2.plot(plot_time,sp2  ,marker = 'o',color='r')
ax2.xaxis.set_major_formatter(hfmt)
ax2.set_ylabel('SP2 nonincandescent #/cc')

ax3 = plt.subplot(3, 1,3)
ax3.plot(plot_time,ratio,marker = 'o',color='k')
ax3.xaxis.set_major_formatter(hfmt)
ax3.set_ylabel('ratio SMPS/SP2')
ax3.set_ylim(2,6)


plt.show()	