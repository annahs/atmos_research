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

instr_ID = 'UBCSP2'

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_interval = ('INSERT INTO whi_hk_data'
              '(UNIX_UTC_ts,sample_flow,yag_power,sheath_flow,yag_xtal_temp,SP2_ID)'
              'VALUES (%(time)s,%(sample_flow)s,%(yag_power)s,%(sheath_flow)s,%(yag_xtal_temp)s,%(SP2_ID)s)')


######get data
i=1
multiple_records = []

data_dir = 'D:/2012/WHI_UBCSP2/Binary/'  
os.chdir(data_dir)
plot = []
for directory in os.listdir(data_dir):
	
	if os.path.isdir(directory) == True and directory.startswith('20'):
		folder_date = datetime.strptime(directory, '%Y%m%d')
		folder_path = os.path.join(data_dir, directory)
		
		os.chdir(folder_path)

		for file in os.listdir('.'):

			if file.endswith('.hk'):
				print file
				folder_date = datetime.strptime(file[0:8], '%Y%m%d')
				print folder_date
				with open(folder_path + '/' + file, 'r') as f:

					f.readline()
					current_minute = 0
					temp={
					'sample_flow':  [],
					'yag_power':    [],
					'sheath_flow':  [],
					'yag_xtal_temp':[],
					}
					for line in f:
						newline = line.split()
						UNIX_time_stamp_UTC = float(newline[1])-2082844800
						UNIX_date = calendar.timegm(folder_date.utctimetuple())
						#UNIX_time_stamp_UTC = UNIX_date + seconds_past_midnight + 3600*-8  #assuming PST
						timestamp = datetime.utcfromtimestamp(UNIX_time_stamp_UTC)
						if timestamp >= datetime(2012,6,1,8):
							sys.exit()
				
						sample_flow=float(newline[3]), 
						yag_power=float(newline[4]),
						sheath_flow=float(newline[7]),
						yag_xtal_temp=float(newline[10]),
						
						if timestamp.minute == current_minute:
							temp['sample_flow'].append(sample_flow)  
							temp['yag_power'].append(yag_power)
							temp['sheath_flow'].append(sheath_flow)
							temp['yag_xtal_temp'].append(yag_xtal_temp)		
						else:
							ts_minute = datetime(timestamp.year,timestamp.month,timestamp.day,timestamp.hour,current_minute) #use current minute because this is the data from the past interval, not the new minute we've moved to
							avg_sample_flow =   float(np.mean(temp['sample_flow']))
							avg_yag_power =     float(np.mean(temp['yag_power']))
							avg_sheath_flow =   float(np.mean(temp['sheath_flow']))
							avg_yag_xtal_temp = float(np.mean(temp['yag_xtal_temp']))
						
							plot.append([dates.date2num(ts_minute),avg_sample_flow,avg_yag_power,avg_sheath_flow,avg_yag_xtal_temp])
							
							if np.isnan(avg_sample_flow):
								avg_sample_flow = None
							if np.isnan(avg_yag_power):
								avg_yag_power = None
							if np.isnan(avg_sheath_flow):
								avg_sheath_flow = None
							if np.isnan(avg_yag_xtal_temp):
								avg_yag_xtal_temp = None
							
							single_record = {
							'time': calendar.timegm(ts_minute.utctimetuple()),
							'sample_flow':  avg_sample_flow, 
							'yag_power':    avg_yag_power,
							'sheath_flow':  avg_sheath_flow,
							'yag_xtal_temp':avg_yag_xtal_temp,
							'SP2_ID':instr_ID,
							}

							multiple_records.append((single_record))
							i+= 1
							#bulk insert to db table
							if i%1000 == 0:
								cursor.executemany(add_interval, multiple_records)
								cnx.commit()
								multiple_records = []
									
																		
							temp={
							'sample_flow':  [sample_flow],
							'yag_power':    [yag_power],
							'sheath_flow':  [sheath_flow],
							'yag_xtal_temp':[yag_xtal_temp],
							}

						current_minute = timestamp.minute

				#bulk insert of remaining records to db
				if multiple_records != []:
					cursor.executemany(add_interval, multiple_records)
					cnx.commit()
					multiple_records = []
				
			os.chdir(data_dir)

cnx.close()			

plot.sort()
times = [row[0] for row in plot]
sample_flow = [row[1] for row in plot]
yag_power = [row[2] for row in plot]
sheath_flow = [row[3] for row in plot]
yag_xtal_temp = [row[4] for row in plot]
hfmt = dates.DateFormatter('%y-%m-%d %H:%M')

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_formatter(hfmt)
ax1.plot(times,sample_flow, 'r')   
ax1.plot(times,yag_power, 'b')
ax1.plot(times,sheath_flow, 'g')
ax1.plot(times,yag_xtal_temp, 'k')
plt.show()
