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

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/size_distrs/'
os.chdir(data_dir)


filec1 = 'AD_corr - size distr - FT - c1.sdbinpickl'
filec2 = 'AD_corr - size distr - FT - c2.sdbinpickl'
filec3 = 'AD_corr - size distr - FT - c3.sdbinpickl'
filec4 = 'AD_corr - size distr - FT - c4.sdbinpickl'
filec5 = 'AD_corr - size distr - FT - c5.sdbinpickl'
filec6 = 'AD_corr - size distr - FT - c6.sdbinpickl'
filefresh = 'AD_corr - size distr - FT - fresh.sdbinpickl'
fileGBPS = 'AD_corr - size distr - FT - GBPS.sdbinpickl'
#fileallFT = 'AD_corr - size distr - FT - all_FT.sdbinpickl'

distributions = {
'Bering':[filec1],
'Northern Coastal/Continental':[filec2],
'Northern Pacific':[filec3],
'Southern Pacific':[filec4],
'Western Pacific/Asia':[filec5],
'Southern Pacific -2':[filec6],
'Fresh Emissions':[filefresh],
'>= 24hrs in GBPS':[fileGBPS],
#'All_FT':[fileallFT],

}

fit_bins = []
for x in range (30,800,5):
	fit_bins.append(x+2)



def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	

for distribution, distribution_data in distributions.iteritems():
	file_name = distribution_data[0]
	with open(file_name, 'r') as f:
		size_distribution_file = pickle.load(f)
		bins = np.array([row[0] for row in size_distribution_file])
		lognorm_masses = np.array([row[1] for row in size_distribution_file])
		
		temp = []
		for mass in lognorm_masses:
			norm_mass = mass/np.max(lognorm_masses)
			temp.append(norm_mass)
		lognorm_masses_max1 = np.array(temp)
		
		distribution_data.append(bins)
		distribution_data.append(lognorm_masses)
		distribution_data.append(lognorm_masses_max1)
		
		mass_bins = distribution_data[1]#[2:]
		norm_log_masses = distribution_data[2]#[2:]
		norm_1_masses = distribution_data[3]
		#print mass_bins
		
		popt, pcov = curve_fit(lognorm, mass_bins, norm_1_masses)	
		perr = np.sqrt(np.diag(pcov)) #from docs:  To compute one standard deviation errors on the parameters use perr = np.sqrt(np.diag(pcov))
		err_variables =  [popt[0]-perr[0], popt[1]-perr[1], popt[2]-perr[2]]
		
		fit_y_vals = []
		for bin in fit_bins:
			fit_val = lognorm(bin, popt[0], popt[1], popt[2])
			fit_y_vals.append(fit_val)
		
		err_fit_y_vals = []
		for bin in fit_bins:
			err_fit_val = lognorm(bin, err_variables[0], err_variables[1], err_variables[2])
			err_fit_y_vals.append(err_fit_val)
			
		distribution_data.append(fit_y_vals)
		distribution_data.append(fit_bins)
		
		max_percent_of_distr_measured = sum(norm_1_masses)*100./sum(err_fit_y_vals)
		
		percent_of_distr_measured = sum(norm_1_masses)*100./sum(fit_y_vals)
		print distribution, percent_of_distr_measured,max_percent_of_distr_measured, 2*(max_percent_of_distr_measured-percent_of_distr_measured)

		
#plotting
data = 3
fit = 4 
fit_bins = 5

fig, axes = plt.subplots(4,2, figsize=(10, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0.00, wspace=0.00)

axs = axes.ravel()
for i in [-1,-2]:
	axes[-1, i].axis('off')
	axes[-2, i].axis('off')
	axes[-3, i].axis('off')
	axes[-4, i].axis('off')



colors = ['b','g','r','c','m','k','y','#DF7401','#585858','grey','#663300']
air_mass_labels = ['Bering','Northern Coastal/Continental','Northern Pacific','Southern Pacific','Western Pacific/Asia','>= 24hrs in GBPS']
markers = ['o','*','>','<','s','^','d','h','+']
ticks = [70,80,100,120,160,200,300,600,800]

i=0
for distribution, distribution_data in distributions.iteritems():
	bins = distribution_data[1]
	normed_log_masses = distribution_data[2]
	normed_1_masses = distribution_data[3]
	fit_bins = distribution_data[5]
	fit_masses = distribution_data[4]
	

	axs[i] = fig.add_subplot(4,2,i+1)
	axs[i].plot(bins,normed_1_masses,color=colors[i], marker = markers[i], linewidth=0)
	axs[i].plot(fit_bins,fit_masses,color =colors[i], linewidth = 1.5)
	axs[i].set_xscale('log')
	axs[i].set_xlim(60,400)
	axs[i].set_ylim(0,1.1)
	axs[i].xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	axs[i].xaxis.set_major_locator(plt.FixedLocator(ticks))
	axs[i].axes.get_yaxis().set_visible(False)	
	if i < 6:
		axs[i].axes.get_xaxis().set_visible(False)
	plt.text(0.05,0.05,distribution, transform=axs[i].transAxes)
	i+=1

	
	
plt.savefig('FT mass distributions - by cluster.png', bbox_inches = 'tight')

plt.show()

sys.exit()
