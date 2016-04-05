import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
import calendar

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#cursor.execute(('SELECT UNIX_GMT_ts,BC_mass_conc from whi_sp2_rbc_record_2009to2012_spikes_removed WHERE UNIX_GMT_ts <= 1251763200')) #2009
#cursor.execute(('SELECT UNIX_GMT_ts,BC_mass_conc from whi_sp2_rbc_record_2009to2012_spikes_removed WHERE UNIX_GMT_ts <= 1283299200 and UNIX_GMT_ts > 1251763200'))#2010
#cursor.execute(('SELECT UNIX_GMT_ts,BC_mass_conc from whi_sp2_rbc_record_2009to2012_spikes_removed WHERE UNIX_GMT_ts > 1283299200'))#2012
#cursor.execute(('SELECT UNIX_GMT_ts,BC_mass_conc from whi_sp2_rbc_record_2009to2012_spikes_removed'))#all
#cursor.execute(('SELECT UNIX_UTC_6h_midtime,meas_mean_mass_conc from whi_gc_and_sp2_6h_mass_concs'))#all
mass_data = cursor.fetchall()
data = []
night = []
day = []
for row in mass_data:
	pst =  datetime.utcfromtimestamp(row[0]+8*3600)
	bc_mass = row[1]
	if pst.hour >= 20 or pst.hour < 8:
		color = 'b'
		night.append(bc_mass)
	else:
		color = 'r'
		day.append(bc_mass)
	data.append([pst,bc_mass,color])
	
	
print np.median(day), np.median(night)
time = [row[0] for row in data]
mass = [row[1] for row in data]
colors = [row[2] for row in data]

fig = plt.figure()
ax1 = plt.subplot(1, 1, 1)
ax1.scatter(time,mass,marker='o', color = colors)
plt.show()
	
	
fig = plt.figure()
ax1 = plt.subplot(2, 1, 1)
ax1.hist(night, bins = 50, range = (0,200),color = 'b', alpha = 0.5)
ax2 = plt.subplot(2, 1, 2)
ax2.hist(day, bins = 50, range = (0,200),color = 'r', alpha = 0.5)
plt.show()
	
	
	
cnx.close()