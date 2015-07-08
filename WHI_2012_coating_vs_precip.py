import sys
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.cm as cm


VED_min = 155	
VED_max = 180

start_date = datetime.strptime('2012/05/16 00:00', '%Y/%m/%d %H:%M')
end_date = datetime.strptime('2012/05/31 00:00', '%Y/%m/%d %H:%M')


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating thicknesses by air mass for 140.25nm to 181.12nm-spikes_fixed-2hr_clusters-precip_amt.binpickl', 'r')
coating_data = pickle.load(file)
file.close()

coating_info = {}
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
		
	temp=[]
	start = True
	for row in air_mass_info:
		rBC_VED = row[0]
		coat_th = row[1]
		date = row[2]
		rain = row[3]
		
		if start == True:
			prev_rain = rain
			start = False
		
		
		Dshell_Dcore = (rBC_VED+2*coat_th)/rBC_VED
		var_of_interest =Dshell_Dcore #coat_th or Dshell_Dcore
		
		if rain == prev_rain:
			temp.append(var_of_interest)
		else:
			
			mean = np.mean(temp)
			if air_mass in coating_info:
				coating_info[air_mass].append([mean,rain])
			else:
				coating_info[air_mass] = [[mean,rain]]
			temp = []
			
		prev_rain = rain
#####plotting

#for key,data in coating_info_sig_rain.iteritems():
#	air_mass = key
#	air_mass_coating_info = data
#	print air_mass, np.median(air_mass_coating_info), np.mean(air_mass_coating_info), len(air_mass_coating_info)
#	print '\n'

	
fig, axes = plt.subplots(7,1, figsize=(6, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.08)

axs = axes.ravel()

bin_number = 40
y_ulim = 0.01

distrs_to_plot = ['Bering','N. Coastal/Continental','N. Pacific','S. Pacific','W. Pacific/Asia','>= 24hrs in GBPS']#,'Fresh Emissions']


i = 0
for distr_to_plot in distrs_to_plot:
	var_of_int = [row[0] for row in coating_info[distr_to_plot]]
	precip = [row[1] for row in coating_info[distr_to_plot]]

	try:
		#axs[i].hexbin(precip,var_of_int,cmap=cm.jet, gridsize = (10,100), bins='log')
		axs[i].scatter(precip,var_of_int)
	except:
		print 'uhoh'
		
	axs[i].text(0.6, 0.8,distr_to_plot, transform=axs[i].transAxes)
	axs[i].axes.get_yaxis().set_visible(False)
	#if var_of_interest == Dshell_Dcore:
	#	data_type = 'Dshell_Dcore'
	#	axs[i].set_xlim(0.5,2.5)
	#if var_of_interest == coat_th:
	#	data_type = 'Coating Thickness (nm)'
	#	axs[i].set_xlim(-40,150)
	if i == 6: 
		axs[i].set_xlabel(data_type)
	i+=1

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
#plt.savefig('coating (' + data_type + ') histos by air mass - '+ str(VED_min) + '-' +str(VED_max) + 'nm rBC cores-precip_correlation.png', bbox_inches='tight')

#plt.savefig('coating (' + data_type + ') histos by air mass - ' + str(start_date.month) + str(start_date.day) + '-' + str(end_date.month)+ str(end_date.day) + ' - '+ str(VED_min) + '-' +str(VED_max) + 'nm rBC cores-v2.png', bbox_inches='tight')

plt.show()      
