import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
from datetime import datetime
import mysql.connector
import math


start = datetime(2009,7,1)
end =   datetime(2009,7,2)
UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

#need to filter on 



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

bins={}
for i in range(70,220,10):
	bins[i] = []


cursor.execute('''(SELECT 
	rBC_mass_fg_BBHG
	FROM whi_sp2_particle_data 
	WHERE
	UNIX_UTC_ts_int_start >= %s
	AND UNIX_UTC_ts_int_end < %s
	AND )''',
	(UNIX_start,UNIX_end))
data  = cursor.fetchall()
	
for row in data:
	bbhg_mass_corr = row[0]
	VED = (((bbhg_mass_corr/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm

	for bin in bins:
		if bin <= VED < (bin+10):
			bins[bin].append([bbhg_mass_corr])
			
distr_data = []			
for bin in bins:
	size = bin +5
	mass = sum([row[0] for row in bins[bin]])/(math.log(size+10)-math.log(size))
	number = len([row[0] for row in bins[bin]])/(math.log(size+10)-math.log(size))

	distr_data.append([size,mass,number])


distr_data.sort()
size = [row[0] for row in distr_data]
mass = [row[1] for row in distr_data]
number = [row[2] for row in distr_data]

#plotting
fig = plt.figure()

ax1 = fig.add_subplot(111)
ax1.semilogx(size,mass,marker='o')
ax1.semilogx(size,number,marker='o')

plt.xlabel('VED (nm)')
plt.ylabel('dM/dlog(VED)')

plt.legend()

plt.show()