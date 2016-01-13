import sys
import os
from pprint import pprint
from decimal import Decimal
import pickle
from SP2_particle_record_UTC import ParticleRecord
import matplotlib.pyplot as plt
import numpy as np


lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor545.lupckl'
lookup_file_max = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor570-calib_max-120nmstart.lupckl'
lookup_file_min = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor520-calib_min-120nmstart.lupckl'
rBC_density = 1.8
incand_pkht = 2775  #605.9 = 130  2775 = 210
scat_pkht = 2250

lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()

lookup_max = open(lookup_file_max, 'r')
lookup_table_max = pickle.load(lookup_max)
lookup_max.close()

lookup_min = open(lookup_file_min, 'r')
lookup_table_min = pickle.load(lookup_min)
lookup_min.close()



avg_alert_calib_mass = 0.0031*incand_pkht + 0.19238
min_alert_calib_mass = (0.0031-0.09*0.0031)*incand_pkht + (0.19238-0.068)
max_alert_calib_mass = (0.0031+0.09*0.0031)*incand_pkht + (0.19238+0.068)
rBC_avg_dia = (((avg_alert_calib_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
rBC_min_dia = (((min_alert_calib_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
rBC_max_dia = (((max_alert_calib_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm

print rBC_avg_dia, rBC_min_dia, rBC_max_dia



def get_coating_thickness(BC_VED,LEO_amp,coating_lookup_table):
	#get the coating thicknesses from the lookup table which is a dictionary of dictionaries, the 1st keyed with BC core size and the second being coating thicknesses keyed with calc scat amps                  
	core_diameters = sorted(coating_lookup_table.keys())
	prev_diameter = core_diameters[0]

	for core_diameter in core_diameters:
		if core_diameter > BC_VED:
			core_dia_to_use = prev_diameter
			break
		prev_diameter = core_diameter

	#now get the coating thickness for the scat_amp this is the coating thickness based on the raw scattering max
	scattering_amps = sorted(coating_lookup_table[core_dia_to_use].keys())
	prev_amp = scattering_amps[0]
	for scattering_amp in scattering_amps:
		if LEO_amp < scattering_amp:
			scat_amp_to_use = prev_amp
			break
		prev_amp = scattering_amp

	scat_coating_thickness = coating_lookup_table[core_dia_to_use].get(scat_amp_to_use, np.nan) # returns value for the key, or none
	return scat_coating_thickness


avg_coat_th = get_coating_thickness(rBC_avg_dia,scat_pkht,lookup_table)
min_coat_th = get_coating_thickness(rBC_max_dia,scat_pkht,lookup_table_max)
max_coat_th = get_coating_thickness(rBC_min_dia,scat_pkht,lookup_table_min)

print avg_coat_th,min_coat_th,max_coat_th
print max_coat_th-avg_coat_th, avg_coat_th-min_coat_th
	
	