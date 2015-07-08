import sys
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

VED_min = 155	
VED_max = 180
file_info = '_RI2.26-1.26_density1.8_calib_factor250-sig_precip_anytime'

start_date = datetime.strptime('2012/04/01 00:00', '%Y/%m/%d %H:%M')
end_date = datetime.strptime('2012/05/31 00:00', '%Y/%m/%d %H:%M')



os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating thicknesses by air mass for 153.37nm to 181.12nm-density_1.8-RI_ (2.26+1.26j)-2hr_clusters-sig_precip_anytime-calib_factor250.binpickl', 'r')
coating_data = pickle.load(file)
file.close()

coating_info = {}
coating_info_sig_rain = {}
lists = []
for air_mass_name, air_mass_info in coating_data.iteritems():
	print air_mass_name
	
	if air_mass_name in ['cluster_1']:
		air_mass = 'Bering'
	if air_mass_name in ['cluster_2']:
		air_mass = 'N. Coastal/Continental'
	if air_mass_name in ['cluster_3']:
		air_mass = 'N. Pacific'	
	if air_mass_name in ['cluster_4','cluster_6']:
		air_mass = 'S. Pacific'	
	if air_mass_name in ['cluster_5']:
		air_mass = 'W. Pacific/Asia'	
	if air_mass_name in ['cluster_GBPS']:
		air_mass = '>= 24hrs in GBPS'	
	if air_mass_name in ['fresh']:
		air_mass = 'Fresh Emissions'
		
	coatings=[]
	for row in air_mass_info:
		rBC_VED = row[0]
		coat_th = row[1]
		date = row[2]
		sig_rain_str = row[3]
		if sig_rain_str == 'True':
			sig_rain = True
		if sig_rain_str == 'False':
			sig_rain = False
		
		if  (VED_min <= rBC_VED <VED_max) and (start_date <= date <= end_date):

			Dshell_Dcore = (rBC_VED+2*coat_th)/rBC_VED
			var_of_interest =Dshell_Dcore #coat_th or Dshell_Dcore
			if var_of_interest == Dshell_Dcore:
				data_type = 'Dshell_Dcore'
			if var_of_interest == coat_th:
				data_type = 'Coating Thickness (nm)'
			

		
			if sig_rain == False:
				if air_mass in coating_info:
					coating_info[air_mass].append(var_of_interest)
				else:
					coating_info[air_mass] = [var_of_interest]
					
			if sig_rain == True:
				if air_mass in coating_info_sig_rain:
					coating_info_sig_rain[air_mass].append(var_of_interest)
				else:
					coating_info_sig_rain[air_mass] = [var_of_interest]

#####plotting
stats = []
for key,data in coating_info.iteritems():
	air_mass = key
	air_mass_coating_info = data
	print air_mass, np.median(air_mass_coating_info), np.mean(air_mass_coating_info), len(air_mass_coating_info)
	stats.append([air_mass, np.median(air_mass_coating_info), np.mean(air_mass_coating_info), np.percentile(air_mass_coating_info, 10),np.percentile(air_mass_coating_info, 90), len(air_mass_coating_info)])
	print '\n'
	
stats_precip = []
for key,data in coating_info_sig_rain.iteritems():
	air_mass = key
	air_mass_coating_info = data
	print air_mass, np.median(air_mass_coating_info), np.mean(air_mass_coating_info), len(air_mass_coating_info)
	stats_precip.append([air_mass, np.median(air_mass_coating_info), np.mean(air_mass_coating_info), np.percentile(air_mass_coating_info, 10),np.percentile(air_mass_coating_info, 90), len(air_mass_coating_info)])
	print '\n'
	
	
#save stats to file 
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating (' + data_type + ') histos by air mass - '+ str(VED_min) + '-' +str(VED_max) + 'nm rBC cores_' + file_info +'-no precip.txt', 'w')
file.write('air_mass' + '\t' +  'median'  + '\t'+ 'mean' + '\t' + '10th_percentile' + '\t' + '90th_percentile' + '\t' +'number_of_particles' +'\n')
for row in stats:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()	
	
#save stats_precip to file 
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating (' + data_type + ') histos by air mass - '+ str(VED_min) + '-' +str(VED_max) + 'nm rBC cores_' + file_info +'-precip.txt', 'w')
file.write('air_mass' + '\t' +  'median'  + '\t'+ 'mean' + '\t' + '10th_percentile' + '\t' + '90th_percentile' + '\t' +'number_of_particles' +'\n')
for row in stats_precip:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()	
	
#plotting
	
	
fig, axes = plt.subplots(7,1, figsize=(6, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)

axs = axes.ravel()

bin_number = 40
y_ulim = 0.01

distrs_to_plot = ['Bering','N. Coastal/Continental','N. Pacific','S. Pacific','W. Pacific/Asia','>= 24hrs in GBPS','Fresh Emissions']


i = 0
for distr_to_plot in distrs_to_plot:
	try:
		axs[i].hist(coating_info[distr_to_plot], bins=bin_number,histtype='step', normed = 1, color='red')
		axs[i].hist(coating_info_sig_rain[distr_to_plot], bins=bin_number,histtype='step', normed = 1, color='blue')
		#axs[i].axvline(np.median(coating_info[distr_to_plot]), color='r', linestyle='--')
	except:
		axs[i].hist([0,0], bins=1,histtype='step', normed = 1)
		
	axs[i].text(0.6, 0.8,distr_to_plot, transform=axs[i].transAxes)
	axs[i].axes.get_yaxis().set_visible(False)
	if var_of_interest == Dshell_Dcore:
		axs[i].set_xlim(0.5,2.5)
	if var_of_interest == coat_th:
		axs[i].set_xlim(-40,150)
	#if i == 6: 
	#	axs[i].set_xlabel(data_type)
	i+=1

plt.savefig('coating (' + data_type + ') histos by air mass - '+ str(VED_min) + '-' +str(VED_max) + 'nm rBC cores_' + file_info +'.png', bbox_inches='tight')


plt.show()      
