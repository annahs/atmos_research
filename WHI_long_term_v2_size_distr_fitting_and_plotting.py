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


data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/size_distrs/'
os.chdir(data_dir)


#fileFR = 'AD_corr - size distr - FRlessFT - FR.sdbinpickl'
#fileBB = 'AD_corr - size distr - FRlessFT - BB.sdbinpickl'
#fileCont = 'AD_corr - size distr - FRlessFT - Cont.sdbinpickl'
#fileNPac = 'AD_corr - size distr - FRlessFT - NPac.sdbinpickl'
#fileSPac = 'AD_corr - size distr - FRlessFT - SPac.sdbinpickl'
#fileLRT = 'AD_corr - size distr - FRlessFT - LRT.sdbinpickl'
#fileGBPS = 'AD_corr - size distr - FRlessFT - GBPS.sdbinpickl'

fileFR = 'AD_corr - size distr - FRlessFT - FR.sdbinpickl'
fileBB = 'AD_corr - size distr - FRlessFT - BB.sdbinpickl'
fileCont = 'AD_corr - size distr - FT - Cont.sdbinpickl'
fileNPac = 'AD_corr - size distr - FT - NPac.sdbinpickl'
fileSPac = 'AD_corr - size distr - FT - SPac.sdbinpickl'
fileLRT = 'AD_corr - size distr - FT - LRT.sdbinpickl'
fileGBPS = 'AD_corr - size distr - FT - GBPS.sdbinpickl'
fileallFT = 'AD_corr - size distr - FT - all_FT.sdbinpickl'

#fileFR = 'AD_corr - size distr - FR.sdbinpickl'
#fileBB = 'AD_corr - size distr - BB.sdbinpickl'
#fileCont = 'AD_corr - size distr - Cont.sdbinpickl'
#fileNPac = 'AD_corr - size distr - NPac.sdbinpickl'
#fileSPac = 'AD_corr - size distr - SPac.sdbinpickl'
#fileLRT = 'AD_corr - size distr - LRT.sdbinpickl'
#fileGBPS = 'AD_corr - size distr - GBPS.sdbinpickl'

distributions = {
'FR':[fileFR],
'BB':[fileBB],
'Cont':[fileCont],
'NPac':[fileNPac],
'SPac':[fileSPac],
'LRT':[fileLRT],
'GBPS':[fileGBPS],
'All_FT':[fileallFT],

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
fig = plt.figure()
ax1 = fig.add_subplot(111)

data = 3
fit = 4 
fit_bins = 5

bins = []
colors = ['k','grey','magenta','cyan','g','b','r']
ticks = [50,60,70,80,100,120,160,200,300,400,600,800]


for distribution, distribution_data in distributions.iteritems():
	bins = distribution_data[1]
	normed_log_masses = distribution_data[2]
	normed_1_masses = distribution_data[3]
	fit_masses = distribution_data[4]

	
#ax1.scatter	(distributions['FR'][1]		,distributions['FR'][data],		color = colors[0], )
#ax1.plot	(distributions['FR'][1]		,distributions['FR'][fit], 		color = colors[0], label = 'FR')
#ax1.scatter	(distributions['BB'][1]		,distributions['BB'][data],		color = colors[1], )
#ax1.plot	(distributions['BB'][1]		,distributions['BB'][fit], 		color = colors[1], label = 'BB')
ax1.plot	(distributions['LRT'][1]	,distributions['LRT'][data],	'sb-', linewidth=0,label = 'W. Pacific/Asia')
ax1.plot	(distributions['LRT'][5]	,distributions['LRT'][fit],	 	color = colors[5],   linewidth = 1.5)
ax1.plot	(distributions['SPac'][1]	,distributions['SPac'][data],	'og-', linewidth=0,label = 'S. Pacific')
ax1.plot	(distributions['SPac'][5]	,distributions['SPac'][fit],	color = colors[4], linewidth =  1.5)
ax1.plot	(distributions['GBPS'][1]	,distributions['GBPS'][data],	'^r-', linewidth=0,label = 'Georgia Basin/Puget Sound')
ax1.plot	(distributions['GBPS'][5]	,distributions['GBPS'][fit],	color = colors[6],  linewidth =  1.5)
ax1.plot	(distributions['NPac'][1]	,distributions['NPac'][data],	'*c-', linewidth=0,label = 'N. Pacific')
ax1.plot	(distributions['NPac'][5]	,distributions['NPac'][fit],	color = colors[3],  linewidth =  1.5)
ax1.plot	(distributions['Cont'][1]	,distributions['Cont'][data],	'>m-', linewidth=0,label = 'N. Canada')
ax1.plot	(distributions['Cont'][5]	,distributions['Cont'][fit],	color = colors[2],  linewidth =  1.5)
ax1.plot	(distributions['All_FT'][1]	,distributions['All_FT'][data],	'dk-', linewidth=0,label = 'All nighttime data')
ax1.plot	(distributions['All_FT'][5]	,distributions['All_FT'][fit],	color = colors[0],  linewidth = 1.5)


legend = ax1.legend(loc='upper center', numpoints=1, bbox_to_anchor=(0.5, 1.18), ncol=3)

ax1.set_xscale('log')
ax1.set_xlim(60,400)
ax1.set_ylim(0,1.1)
ax1.set_xlabel('VED (nm)')
ax1.set_ylabel('dM/dlogVED')
ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
#plt.text(0.9,0.9, '(b)',transform=ax1.transAxes)
plt.savefig('FT mass distributions - by cluster -t.png', bbox_inches = 'tight',bbox_extra_artists=(legend,))

plt.show()

sys.exit()
##
fig = plt.figure()
ax1 = fig.add_subplot(111)

data = 2
fit = 4 
fit_bins = 5

bins = []
colors = ['k','grey','magenta','grey','g','b','r']
ticks = [50,60,70,80,100,120,160,200,300,400,600,800]


for distribution, distribution_data in distributions.iteritems():
	bins = distribution_data[1]
	normed_log_masses = distribution_data[2]
	normed_1_masses = distribution_data[3]
	fit_masses = distribution_data[4]

	
ax1.scatter	(distributions['FR'][1]		,distributions['FR'][data],		color = colors[0], )
ax1.plot	(distributions['FR'][5]		,distributions['FR'][fit], 		color = colors[0], label = 'FR')
ax1.scatter	(distributions['BB'][1]		,distributions['BB'][data],		color = colors[1], )
ax1.plot	(distributions['BB'][5]		,distributions['BB'][fit], 		color = colors[1], linestyle = '--',label = 'BB')
#ax1.scatter	(distributions['LRT'][1]	,distributions['LRT'][data],	color = colors[5], marker = 'o' ,  s = 40)
#ax1.plot	(distributions['LRT'][5]	,distributions['LRT'][fit],	 	color = colors[5], label = 'LRT',  linewidth = 1.5)
#ax1.scatter	(distributions['SPac'][1]	,distributions['SPac'][data],	color = colors[4], marker = '>' ,)
#ax1.plot	(distributions['SPac'][5]	,distributions['SPac'][fit],	color = colors[4], label = 'SPac', linewidth = 1.5)
#ax1.scatter	(distributions['GBPS'][1]	,distributions['GBPS'][data],	color = colors[6], marker = '*' ,)
#ax1.plot	(distributions['GBPS'][5]	,distributions['GBPS'][fit],	color = colors[6], label = 'GBPS', linewidth = 1.5)
#ax1.scatter	(distributions['NPac'][1]	,distributions['NPac'][data],	color = colors[3], marker = 's' ,)
#ax1.plot	(distributions['NPac'][5]	,distributions['NPac'][fit],	color = colors[3], label = 'NPac', linewidth = 1.5)
#ax1.scatter	(distributions['Cont'][1]	,distributions['Cont'][data],	color = colors[2], marker = '<' ,)
#ax1.plot	(distributions['Cont'][5]	,distributions['Cont'][fit],	color = colors[2], label = 'Cont', linewidth = 1.5)



plt.legend(numpoints=1)
ax1.set_xscale('log')
ax1.set_xlim(40,750)
ax1.set_ylim(0,130)
ax1.set_xlabel('VED (nm)')
ax1.set_ylabel('dM/dlogVED')
ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
plt.text(0.9,0.9, '(a)',transform=ax1.transAxes)
#plt.savefig('FR and BB mass distributions.png', bbox_inches = 'tight')

plt.show()