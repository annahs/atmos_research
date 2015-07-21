import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import nanmean
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
import math
import traceback
import time

distr_type = 1 #1 for mass, 2 for number


#data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/size_distrs/sig_precip_anytime/'
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/size_distrs/sig_precip_final_72hrs/'
os.chdir(data_dir)


filec1_precip = 'AD_corr - size distr - FT - c1_precip.sdbinpickl'
filec2_precip = 'AD_corr - size distr - FT - c2_precip.sdbinpickl'
filec3_precip = 'AD_corr - size distr - FT - c3_precip.sdbinpickl'
filec4_precip = 'AD_corr - size distr - FT - c4_precip.sdbinpickl'
filec5_precip = 'AD_corr - size distr - FT - c5_precip.sdbinpickl'
filec6_precip = 'AD_corr - size distr - FT - c6_precip.sdbinpickl'
filefresh_precip = 'AD_corr - size distr - FT - fresh_precip.sdbinpickl'
fileGBPS_precip = 'AD_corr - size distr - FT - GBPS_precip.sdbinpickl'

filec1_no_precip = 'AD_corr - size distr - FT - c1_no_precip.sdbinpickl'
filec2_no_precip = 'AD_corr - size distr - FT - c2_no_precip.sdbinpickl'
filec3_no_precip = 'AD_corr - size distr - FT - c3_no_precip.sdbinpickl'
filec4_no_precip = 'AD_corr - size distr - FT - c4_no_precip.sdbinpickl'
filec5_no_precip = 'AD_corr - size distr - FT - c5_no_precip.sdbinpickl'
filec6_no_precip = 'AD_corr - size distr - FT - c6_no_precip.sdbinpickl'
filefresh_no_precip = 'AD_corr - size distr - FT - fresh_no_precip.sdbinpickl'
fileGBPS_no_precip = 'AD_corr - size distr - FT - GBPS_no_precip.sdbinpickl'

distributions_precip = {
'Bering':						[filec1_precip],
'Northern Coastal/Continental':	[filec2_precip],
'Northern Pacific':				[filec3_precip],
'Southern Pacific':				[filec4_precip],
'Western Pacific/Asia':			[filec5_precip],
'Southern Pacific -2':			[filec6_precip],
'Fresh Emissions':				[filefresh_precip],
'>= 24hrs in GBPS':				[fileGBPS_precip],
#'All_FT':[fileallFT],
}

distributions_no_precip = {
'Bering':						[filec1_no_precip],
'Northern Coastal/Continental':	[filec2_no_precip],
'Northern Pacific':				[filec3_no_precip],
'Southern Pacific':				[filec4_no_precip],
'Western Pacific/Asia':			[filec5_no_precip],
'Southern Pacific -2':			[filec6_no_precip],
'Fresh Emissions':				[filefresh_no_precip],
'>= 24hrs in GBPS':				[fileGBPS_no_precip],
#'All_FT':[fileallFT],
}

fit_bins = []
for x in range (30,800,5):
	fit_bins.append(x+2)



def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	

for distribution, distribution_data in distributions_precip.iteritems():
	file_name = distribution_data[0]
	
	if file_name == 'AD_corr - size distr - FT - c6_precip.sdbinpickl':
		file_c6 = open(file_name, 'r')
		c6_data = pickle.load(file_c6)
		file_c6.close()

		
		
	else:
		with open(file_name, 'r') as f:
			size_distribution_file = pickle.load(f)
			if distr_type == 2:
				size_distribution_file.pop(0)
			bins = np.array([row[0] for row in size_distribution_file])
						
						
			#combine clusters 4 and 6 (S PAc)
			if file_name == 'AD_corr - size distr - FT - c4_precip.sdbinpickl':
				i=0
				lognorm_masses_l = []
				for row in size_distribution_file:
					lognorm_mass_c4 = row[distr_type]
					lognorm_mass_c6 = c6_data[i][distr_type]
					mean_mass = (lognorm_mass_c4+lognorm_mass_c6)/2
					lognorm_masses_l.append(mean_mass)
					lognorm_masses = np.array(lognorm_masses_l)
					i+=1

			#other clusters	
			else:
				lognorm_masses = np.array([row[distr_type] for row in size_distribution_file])
			
			#continue with analysis
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
			
			try:
				popt, pcov = curve_fit(lognorm, mass_bins, norm_log_masses)
				perr = np.sqrt(np.diag(pcov)) #from docs:  To compute one standard deviation errors on the parameters use perr = np.sqrt(np.diag(pcov))
				err_variables =  [popt[0]-perr[0], popt[1]-perr[1], popt[2]-perr[2]]
			except:
				popt = [np.nan,np.nan,np.nan]
				err_variables = [np.nan,np.nan,np.nan]
				
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
			print 'precip',distribution, percent_of_distr_measured,max_percent_of_distr_measured, 2*(max_percent_of_distr_measured-percent_of_distr_measured)

			
first_SP = 0
for distribution, distribution_data in distributions_no_precip.iteritems():
	file_name = distribution_data[0]
	
	if file_name == 'AD_corr - size distr - FT - c6_no_precip.sdbinpickl' or file_name == 'AD_corr - size distr - FT - c4_no_precip.sdbinpickl' and first_SP == 0:
		file = open(file_name, 'r')
		SP1 = pickle.load(file)
		if distr_type == 2:
			SP1.pop(0)
		file.close()
		first_SP = 1
		
		
	else:
		with open(file_name, 'r') as f:
			size_distribution_file = pickle.load(f)
			if distr_type == 2:
				size_distribution_file.pop(0)
			bins = np.array([row[0] for row in size_distribution_file])
						
						
			#combine clusters 4 and 6 (S PAc)
			if file_name == 'AD_corr - size distr - FT - c6_no_precip.sdbinpickl' or file_name == 'AD_corr - size distr - FT - c4_no_precip.sdbinpickl' and first_SP == 0:
				continue
			if file_name == 'AD_corr - size distr - FT - c6_no_precip.sdbinpickl' or file_name == 'AD_corr - size distr - FT - c4_no_precip.sdbinpickl' and first_SP == 1:
				first_SP = 2
				i=0
				lognorm_masses_l = []
				for row in size_distribution_file:
					lognorm_mass_c4 = row[distr_type]
					lognorm_mass_c6 = SP1[i][distr_type]
					mean_mass = nanmean([lognorm_mass_c4,lognorm_mass_c6])
					lognorm_masses_l.append(mean_mass)
					lognorm_masses = np.array(lognorm_masses_l)
					i+=1

			#other clusters	
			else:
				lognorm_masses = np.array([row[distr_type] for row in size_distribution_file])
			
			#continue with analysis
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
			
			try:
				popt, pcov = curve_fit(lognorm, mass_bins, norm_log_masses)
				perr = np.sqrt(np.diag(pcov)) #from docs:  To compute one standard deviation errors on the parameters use perr = np.sqrt(np.diag(pcov))
				err_variables =  [popt[0]-perr[0], popt[1]-perr[1], popt[2]-perr[2]]
			except:
				popt = [np.nan,np.nan,np.nan]
				err_variables = [np.nan,np.nan,np.nan]
				
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
			print 'no_precip',distribution, percent_of_distr_measured,max_percent_of_distr_measured, 2*(max_percent_of_distr_measured-percent_of_distr_measured)



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

distrs_to_plot = ['Bering','Northern Coastal/Continental','Northern Pacific','Southern Pacific','Western Pacific/Asia','>= 24hrs in GBPS','Fresh Emissions']


i=0
for distr_to_plot in distrs_to_plot:
	
	bins_precip = distributions_precip[distr_to_plot][1]
	normed_log_masses_precip = distributions_precip[distr_to_plot][2]
	normed_1_masses_precip = distributions_precip[distr_to_plot][3]
	fit_bins_precip = distributions_precip[distr_to_plot][5]
	fit_masses_precip = distributions_precip[distr_to_plot][4]
	
	bins_no_precip = distributions_no_precip[distr_to_plot][1]
	normed_log_masses_no_precip = distributions_no_precip[distr_to_plot][2]
	normed_1_masses_no_precip = distributions_no_precip[distr_to_plot][3]
	fit_bins_no_precip = distributions_no_precip[distr_to_plot][5]
	fit_masses_no_precip = distributions_no_precip[distr_to_plot][4]

	axs[i] = fig.add_subplot(4,2,i+1)
	
	axs[i].plot(bins_precip,normed_log_masses_precip,color='b', marker = 'o', linewidth=0)
	#axs[i].plot(fit_bins_precip,fit_masses_precip,color='b', linewidth = 1.5)
	axs[i].plot(bins_no_precip,normed_log_masses_no_precip,color='r', marker = 's', linewidth=0)
	#axs[i].plot(fit_bins_no_precip,fit_masses_no_precip,color='r', linewidth = 1.5)
	axs[i].set_xscale('log')
	axs[i].set_xlim(60,400)
	#axs[i].set_ylim(0,16)	
	axs[i].set_xlabel('VED (nm)')
	axs[i].xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	axs[i].xaxis.set_major_locator(plt.FixedLocator(ticks))
		
	if i < 5:
		axs[i].axes.get_xaxis().set_visible(False)

	if distr_type == 1:
		axs[i].set_ylabel('dM/dlogVED')
	if distr_type == 2:
		axs[i].set_ylabel('d#/dlogVED')
	
	if i in [1,3,5]:
		axs[i].yaxis.tick_right()
		axs[i].yaxis.set_label_position('right')
		
	plt.text(0.05,0.05,distr_to_plot, transform=axs[i].transAxes)
	i+=1

	
	
plt.savefig('FT mass distributions - by cluster - sep by sig precip last 72hrs.png', bbox_inches = 'tight')

plt.show()

