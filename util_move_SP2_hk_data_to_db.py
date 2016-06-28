import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
import os.path
from matplotlib import dates
import matplotlib.pyplot as plt


##database connection
#cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
#cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT INTO alert_hk_data'
              '(UNIX_UTC_ts,sample_flow,yag_power,sheath_flow,yag_xtal_temp)'
              'VALUES (%(time)s,%(sample_flow)s,%(yag_power)s,%(sheath_flow)s,%(yag_xtal_temp)s)')


######get data

data_dir = 'F:/Alert/2013/SP2B_files/'  #Alert data is in UTC - see email from Dan Veber
os.chdir(data_dir)
plot = []
for directory in os.listdir(data_dir):
	
	if os.path.isdir(directory) == True and directory.startswith('20'):
		folder_date = datetime.strptime(directory, '%Y%m%d')
		folder_path = os.path.join(data_dir, directory)
		if folder_date.day ==15:
			os.chdir(folder_path)
	
			
			for file in os.listdir('.'):
				
				if file.endswith('.hk'):
					print file
					with open(file, 'r') as f:

						f.readline()
						
						for line in f:
							newline = line.split()
							seconds_past_midnight = float(newline[0])
							UNIX_date = calendar.timegm(folder_date.utctimetuple())
							UNIX_time_stamp_UTC = UNIX_date + seconds_past_midnight
							p_timestamp = datetime.utcfromtimestamp(UNIX_time_stamp_UTC)
							
							
							sample_flow=float(newline[2]), 
							yag_power=float(newline[3]),
							sheath_flow=float(newline[6]),
							yag_xtal_temp=float(newline[7]),
							
							plot.append([dates.date2num(p_timestamp), sample_flow,yag_power,sheath_flow,yag_xtal_temp])
							
							
							#interval_data = {
							#'time': UNIX_time_stamp_UTC,
							#'sample_flow':  float(newline[2]), 
							#'yag_power':    float(newline[3]),
							#'sheath_flow':  float(newline[6]),
							#'yag_xtal_temp':float(newline[7]),
							#}
							#
							#cursor.execute(add_interval, interval_data)
							#cnx.commit()
					
			os.chdir(data_dir)
#cnx.close()			
plot.sort()
times = [row[0] for row in plot]
sample_flow = [row[1] for row in plot]
yag_power = [row[2] for row in plot]
sheath_flow = [row[3] for row in plot]
yag_xtal_temp = [row[4] for row in plot]
hfmt = dates.DateFormatter('%H:%M')

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_formatter(hfmt)
ax1.plot(times,sample_flow, 'r')   
ax1.plot(times,yag_power, 'b')
ax1.plot(times,sheath_flow, 'g')
ax1.plot(times,yag_xtal_temp, 'k')
plt.show()
