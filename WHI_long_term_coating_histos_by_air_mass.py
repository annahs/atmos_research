import sys
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt

VED_min = 155	
VED_max = 180


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
#file = open('coating thicknesses by air mass for 69.76nm to 220.11nm-spikes_fixed-2hr_clusters.binpickl', 'r')
file = open('coating thicknesses by air mass for 69.76nm to 220.11nm-spikes_fixed-2hr_clusters-DMT269_coating_calib.binpickl', 'r')
coating_data = pickle.load(file)
file.close()

coating_info = {}
lists = []
for air_mass_name, air_mass_info in coating_data.iteritems():
	print air_mass_name
	coatings=[]
	for row in air_mass_info:
		rBC_VED = row[0]
		coat_th = row[1]
		Dshell_Dcore = (rBC_VED+2*coat_th)/rBC_VED
		var_of_interest =coat_th #coat_th or Dshell_Dcore
		
		if rBC_VED >= VED_min and rBC_VED < VED_max:
			if air_mass_name in ['cluster_1']:
				air_mass = 'Bering'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]
					
			if air_mass_name in ['cluster_2']:
				air_mass = 'N. Coastal/Continental'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]
					
			if air_mass_name in ['cluster_3']:
				air_mass = 'N. Pacific'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]
					
			if air_mass_name in ['cluster_4','cluster_6']:
				air_mass = 'S. Pacific'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]
					
			if air_mass_name in ['cluster_5']:
				air_mass = 'W. Pacific/Asia'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]

			if air_mass_name in ['cluster_GBPS']:
				air_mass = '>= 24hrs in GBPS'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]
					
			if air_mass_name in ['fresh']:
				air_mass = 'Fresh Emissions'
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]

		
#####plotting

for key,data in coating_info.iteritems():
	air_mass = key
	air_mass_coating_info = data
	print air_mass, np.median(air_mass_coating_info), np.mean(air_mass_coating_info), len(air_mass_coating_info)
	print '\n'

	
fig, axes = plt.subplots(7,1, figsize=(6, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)

axs = axes.ravel()

bin_number = 20
y_ulim = 0.01

distrs_to_plot = ['Bering','N. Coastal/Continental','N. Pacific','S. Pacific','W. Pacific/Asia','>= 24hrs in GBPS','Fresh Emissions']


i = 0
for distr_to_plot in distrs_to_plot:
	axs[i].hist(coating_info[distr_to_plot], bins=bin_number,histtype='step', normed = 1)
	axs[i].text(0.6, 0.8,distr_to_plot, transform=axs[i].transAxes)
	axs[i].axvline(np.median(coating_info[distr_to_plot]), color='r', linestyle='--')
	axs[i].axes.get_yaxis().set_visible(False)
	if var_of_interest == Dshell_Dcore:
		data_type = 'Dshell_Dcore'
		axs[i].set_xlim(0.5,2.5)
	if var_of_interest == coat_th:
		data_type = 'Coating Thickness (nm)'
		axs[i].set_xlim(-40,250)
	if i == 6: 
		axs[i].set_xlabel(data_type)
	i+=1

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
plt.savefig('coating (' + data_type + ') histos by air mass' + str(VED_min) + '-' +str(VED_max) + 'nm rBC cores-v2-2014DMTcalib269.png', bbox_inches='tight')

plt.show()      
