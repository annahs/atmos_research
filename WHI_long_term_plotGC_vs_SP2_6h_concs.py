import matplotlib.pyplot as plt
import sys
import os
import numpy as np
from pprint import pprint
import mysql.connector
from scipy import stats
import math


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

RH_of_interest = 101
cluster_to_view = 'NPac'

cursor.execute('SELECT meas_mean_mass_conc,GC_v10_default, cluster from whi_gc_and_sp2_6h_mass_concs where RH_threshold = %s and cluster = %s',(RH_of_interest, cluster_to_view))
#cursor.execute('SELECT meas_mean_mass_conc,GC_v10_all_together, cluster from whi_gc_and_sp2_6h_mass_concs where RH_threshold = 90')
data_raw = cursor.fetchall()



#log-log
log_meas = [np.log10(row[0])for row in data_raw]
log_GC = [np.log10(row[1])for row in data_raw]

slope, intercept, r_value, p_value, std_err = stats.linregress(log_meas,log_GC)
print slope, intercept, r_value, p_value, std_err
print r_value*r_value

fit = []
for value in log_meas:
	GC_fit = intercept + slope*(value)
	fit_meas_val = 10**value
	fit_GC_val = 10**GC_fit
	fit.append([fit_meas_val, fit_GC_val])
	
fit.sort()

fit_meas = [row[0] for row in fit]
fit_GC = [row[1] for row in fit]
	
##lin
meas = [row[0] for row in data_raw]
GC = [row[1] for row in data_raw]

slope_lin, intercept_lin, r_value_lin, p_value_lin, std_err_lin = stats.linregress(meas,GC)
print slope, intercept, r_value, p_value, std_err
print r_value*r_value

fit_lin = []
for value in meas:
	GC_fit = intercept_lin + slope_lin*(value)
	fit_lin.append([value,GC_fit])

fit_lin.sort()

fit_meas_lin = [row[0] for row in fit_lin]
fit_GC_lin = [row[1] for row in fit_lin]


#pprint(fit)
	
	
###
fig = plt.figure()
ax = fig.add_subplot(111)
plt.ylim(1,400)
plt.xlim(1,400)

ax.scatter(meas,GC)

ax.plot([1,500],[1,500])
ax.plot([1,500],[2,1000], '--k')
ax.plot([1,500],[0.5,250], '--k')

ax.plot(fit_meas,fit_GC,color='r',linewidth=2)
ax.set_yscale('log')
ax.set_xscale('log')

#ax.plot(fit_meas_lin,fit_GC_lin,color='r',linewidth=2)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/GCvsSP2plots/')
  
plt.savefig('GC vs SP2 plots for WHI - NPac cluster - default scenario - no RH threshold.png',bbox_inches='tight')
plt.show()

cnx.close()