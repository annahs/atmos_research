import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
import math
import traceback
import time


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('raw size and number distributions by air mass for 69.76nm to 220.11nm.binpickl', 'r')
distr_data = pickle.load(file)
file.close()

modified_distr_data = {}

interval_length = 5.0

fit_bins = []
for x in range (30,800,5):
	fit_bins.append(x+2)



def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	

for air_mass, distribution_data in distr_data.iteritems():
	print air_mass
	#distribution_data.pop(70, None)
	distr_bins_p = []
	mass_distr_values = []
	numb_distr_values = []
	for bin, distr_values in distribution_data.iteritems(): 	#normalize
		n_mass_val = distr_values[0]/(math.log(bin+interval_length)-math.log(bin)) #dM/dlog(VED)
		mass_distr_values.append(n_mass_val)
		n_numb_val = distr_values[1]/(math.log(bin+interval_length)-math.log(bin)) #d/dlog(VED)
		numb_distr_values.append(n_numb_val)
		distr_bins_p.append(bin+interval_length/2.0) #correction for our binning code recording bin starts as keys instead of midpoints
		
	
	norm_mass_distr_values_p = []
	for mass in mass_distr_values:
		norm_mass = mass/np.max(mass_distr_values)
		norm_mass_distr_values_p.append(norm_mass)
	norm_mass_distr_values = np.array(norm_mass_distr_values_p)
		
	norm_numb_distr_values_p = []
	for numb in numb_distr_values:
		norm_numb = numb/np.max(numb_distr_values)
		norm_numb_distr_values_p.append(norm_numb)
	norm_numb_distr_values = np.array(norm_numb_distr_values_p)
	
	distr_bins = np.array(distr_bins_p)
	
	
	fit_failure = False
	try:
		popt, pcov = curve_fit(lognorm, distr_bins, norm_numb_distr_values)	
		perr = np.sqrt(np.diag(pcov)) #from docs:  To compute one standard deviation errors on the parameters use perr = np.sqrt(np.diag(pcov))
		err_variables =  [popt[0]-perr[0], popt[1]-perr[1], popt[2]-perr[2]]
	except:
		print 'fit_failure' 
		fit_failure = True
		
		
	fit_y_vals = []
	for bin in fit_bins:
		if fit_failure == True:
			fit_val = np.nan
		else:
			fit_val = lognorm(bin, popt[0], popt[1], popt[2])
			
		fit_y_vals.append(fit_val)
	
	err_fit_y_vals = []
	for bin in fit_bins:
		if fit_failure == True:
			err_fit_val = np.nan
		else:
			err_fit_val = lognorm(bin, err_variables[0], err_variables[1], err_variables[2])
		err_fit_y_vals.append(err_fit_val)
	
	modified_distr_data[air_mass] = [distr_bins,norm_numb_distr_values,fit_bins,fit_y_vals]

pprint(modified_distr_data['GBPS'])
	

#plotting


fig = plt.figure()
ax1 = fig.add_subplot(111)

colors=['magenta', 'red', 'green', 'cyan', 'blue', 'black']

i=0
for air_mass, distr in modified_distr_data.iteritems():
	bins = modified_distr_data[air_mass][0]
	data = modified_distr_data[air_mass][1]	
	fit_bins = modified_distr_data[air_mass][2]
	fits = modified_distr_data[air_mass][3]
	
	
	m_distr = ax1.scatter(bins,data, label = air_mass,color = colors[i])
	f_distr = ax1.semilogx(fit_bins,fits,color = colors[i])
	ax1.set_xlim(40,500)
	ax1.set_ylim(0,1.1)
			
	i+=1

plt.legend()

plt.show()


