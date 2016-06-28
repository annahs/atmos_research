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


SP2_ID = 58
start = datetime(2013,10,10)
end =   datetime(2013,10,15)
UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

bins={}
for i in range(70,310,10):
	bins[i] = []


cursor.execute('''(SELECT 
	BB_incand_HG,
	NB_incand_HG,
	BB_incand_LG
	FROM alert_mass_number_data_2013 
	WHERE
	UNIX_UTC_ts_int_start >= %s
	AND UNIX_UTC_ts_int_end < %s)''',
	(UNIX_start,UNIX_end))
data  = cursor.fetchall()
	
for row in data:
	bbhg_incand_pk_amp = row[0]
	nbhg_incand_pk_amp = row[1]
	bblg_incand_pk_amp = row[2]

	#calculate masses and uncertainties
	#HG
	bbhg_mass_uncorr = 0.29069 + 1.49267E-4*bbhg_incand_pk_amp + 5.02184E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  
	bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
	
	#LG
	bblg_mass_uncorr = -0.15884 + 0.00176*bblg_incand_pk_amp + 3.19118E-8*bblg_incand_pk_amp*bblg_incand_pk_amp	
	bblg_mass_corr = bblg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05

	
	if 0.33 <= bbhg_mass_corr < 1.8:
		mass = bbhg_mass_corr  
	if 12.8 <= bblg_mass_corr < 41:
		mass = bblg_mass_corr
	if (1.8 <= bbhg_mass_corr < 12.8) or (1.8 <= bblg_mass_corr < 12.8):
		mass = (bbhg_mass_corr + bblg_mass_corr)/2
	
	VED = (((mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm

	for bin in bins:
		if bin <= VED < (bin+10):
			bins[bin].append([mass,(bbhg_incand_pk_amp/nbhg_incand_pk_amp)])
			
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