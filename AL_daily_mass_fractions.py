import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
from matplotlib import dates

#data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/mass distributions/'
#file ='fraction of rBC mass measured in each day.txt'
#os.chdir(data_dir)
#
#list = []
#
#with open(file, 'r') as f:
#	f.readline()
#	f.readline()
#	for line in f:
#		newline = line.split()
#		date = newline[0]
#		file_date = datetime.strptime(date,'%Y-%m-%d')
#		ratio = float(newline[1])
#		err = float(newline[3])
#		
#		list.append([file_date,ratio,err])
#		
#date = [dates.date2num(row[0]) for row in list]
#ratio = [(1/row[1]) for row in list]
#err = [row[2] for row in list]
#
#hfmt = dates.DateFormatter('%Y%m%d %H:%M')
#
#fig = plt.figure()
#ax1 = fig.add_subplot(111)
#ax1.xaxis.set_major_formatter(hfmt)
#ax1.plot(date,ratio,'-ro')
##ax1.plot(date,err,'-bo')
#plt.show()
#

list = []
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/mass and number distributions 48hr/'
os.chdir(data_dir)
for file in os.listdir('.'):
			
	if file.startswith('rBC distributions'):
		file_date = datetime.strptime(file[22:32],'%Y-%m-%d')

		print file_date
		with open(file, 'r') as f:
			first = f.readline()
			new = first.split()
			
			print file_date, float(new[12])
			f.readline()
			bins = []
			fit_masses = []
			for line_str in f:
				line = line_str.split()
				bin_mid = float(line[0])
				meas_mass = line[1]
				fit_mass = float(line[2])
				bins.append(bin_mid)
				fit_masses.append(fit_mass)
			fit_maximum = np.max(fit_masses)
			if np.isnan(fit_maximum):
				continue
			index = fit_masses.index(fit_maximum)
			max_bin = bins[index]
			print 'peak',max_bin
			list.append([file_date,float(new[12]),max_bin])
			
date = [dates.date2num(row[0]) for row in list]
ratio = [(1/row[1]) for row in list]
max = [row[2]/100 for row in list]


hfmt = dates.DateFormatter('%Y%m%d %H:%M')

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_formatter(hfmt)
ax1.plot(date,ratio,'-ro')
ax1.plot(date,max,'-bo')
plt.axhline(y=240/100)
plt.show()