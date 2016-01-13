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
from scipy.stats import t
from scipy import stats

scat_amp = 500
meas_scat_amp_min = scat_amp-scat_amp*0.02
meas_scat_amp_max = scat_amp+scat_amp*0.02



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

		
cursor.execute(('SELECT LF_scat_amp FROM polar6_coating_2015 WHERE LF_scat_amp IS NOT NULL AND particle_type = %s AND actual_scat_amp >= %s AND actual_scat_amp < %s'),('nonincand',meas_scat_amp_min,meas_scat_amp_max))
scat_data = cursor.fetchall()

plot_data = []
for row in scat_data:
	plot_data.append(row[0])

sample_size = 100#len(plot_data)
mean = np.mean(plot_data)
std = np.std(plot_data)

print sample_size,mean,std

print '***', 1.96*(std/math.sqrt(sample_size))




R = stats.norm.interval(0.95,loc=mean,scale=std/math.sqrt(sample_size))
print R

test=t.interval(0.95, plot_data, loc=mean, scale=std/math.sqrt(sample_size))  # 95% confidence interval
print test[0][0], test[1][0]

sys.exit()	
######

# Define model function to be used to fit to the data:
def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

	
fig = plt.figure()


ax1 = plt.subplot(1, 1, 1)
n, bins, patches = ax1.hist(plot_data, 60,facecolor='green', alpha=0.75)

bin_edges = np.array(bins)
bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

pguess = [np.max(n),meas_scat_amp_min,std]
coeff, var_matrix = curve_fit(gauss, bin_centres, n,p0=pguess)
print coeff
# Get the fitted curve
fit_result = []
for x in bin_centres:
	fit_result.append(gauss(x,coeff[0],coeff[1],coeff[2]))

#ax1.plot(bin_centres, n)
ax1.plot(bin_centres, fit_result)

# Finally, lets get the fitting parameters, i.e. the mean and standard deviation:
print 'Fitted mean = ', coeff[1]
print 'Fitted standard deviation = ', coeff[2]
#ax1.set_xscale('log')
plt.show()