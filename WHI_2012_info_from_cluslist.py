import sys
import os
import datetime
import pickle
import numpy as np
import math


#open cluslist and read into a python list (convert UTC to local time here)
cluslist = []
CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip_added-sig_precip_72hrs_pre_arrival'

traj_1 = 0
traj_2 = 0
traj_3 = 0
traj_4 = 0
traj_5 = 0
traj_6 = 0

traj_1_rainy = 0
traj_2_rainy = 0
traj_3_rainy = 0
traj_4_rainy = 0
traj_5_rainy = 0
traj_6_rainy = 0



data = {}
with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		air_mass_name = newline[0]
		significant_rainfall = newline[8]
		
		if air_mass_name in ['1']:
			air_mass = 'Bering'
			traj_1 +=1
			if significant_rainfall == 'True':
				traj_1_rainy +=1
		if air_mass_name in ['2']:
			air_mass = 'N. Coastal/Continental'
			traj_2 +=1
			if significant_rainfall == 'True':
				traj_2_rainy +=1
		if air_mass_name in ['3']:
			air_mass = 'N. Pacific'	
			traj_3 +=1
			if significant_rainfall == 'True':
				traj_3_rainy +=1
		if air_mass_name in ['4','6']:
			air_mass = 'S. Pacific'	
			traj_4 +=1
			if significant_rainfall == 'True':
				traj_4_rainy +=1
		if air_mass_name in ['5']:
			air_mass = 'W. Pacific/Asia'
			traj_5 +=1
			if significant_rainfall == 'True':
				traj_5_rainy +=1			
		if air_mass_name in ['7']:
			air_mass = '>= 24hrs in GBPS'
			traj_6 +=1
			if significant_rainfall == 'True':
				traj_6_rainy +=1			

		
print 'Bering', traj_1, 'frac_rainy',traj_1_rainy*1.0/traj_1
print 'NCC', traj_2, 'frac_rainy',traj_2_rainy*1.0/traj_2
print 'NPAC', traj_3, 'frac_rainy',traj_3_rainy*1.0/traj_3
print 'SPAC', traj_4, 'frac_rainy',traj_4_rainy*1.0/traj_4
print 'WPA', traj_5, 'frac_rainy',traj_5_rainy*1.0/traj_5
print 'GBPS', traj_6, 'frac_rainy',traj_6_rainy*1.0/traj_6
			
			
