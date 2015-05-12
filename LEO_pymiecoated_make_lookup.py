from pymiecoated import Mie
import numpy as np
import matplotlib.pyplot as plt
import pickle
import math
import sys
import os
from pprint import pprint 

#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/Forest Fires/2012/SP2-2012/Calibration/'
#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/LEO fitting/LJ-EC-SP2/lookup tables'
#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/SP2_2010/BB period 2010/EC_SP2/lookup tables/'
#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/SP2_2010/FT periods 2012/lookup tables/'
lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/lookup_tables/'

os.chdir(lookup_dir)

#************setup********************

wl = 1064 #nm
core_RI = complex(2.26,1.26)  #from Moteki 2010 (and Laborde and Taylor)
shell_RI = complex(1.5, 0)
PSL_RI = complex(1.59,0)

#WHI 2010 ECSP2
scat_cal_limit = 50000

def scat_amp(Itotal):
	#calc_scattering_amplitude = 112*Itotal  #calibration fit is in origin file for LJ-EC_SP2
	#calc_scattering_amplitude = 3.72*Itotal+9.65  #calibration from Aquadag numbers Jason sent for LJ
	#calc_scattering_amplitude = 331.2*Itotal # UBCSP2 WHI 2012 
	calc_scattering_amplitude = 71.32*Itotal  # ECSP2 WHI 2010
	
	return calc_scattering_amplitude
	
	
#**********calc the lookup table*************************

#set the maximum shell radius (note: this is a radius not a thickness)
max_shell_rad = 500 #nm
shell_step_size = 0.5 # will give 1nm steps in final diameter
core_step_size = 0.5 # will give 1nm steps in final diameter

#set the range and increment value of core radii to be used
core_rad_range = []
core_radius = 30  #60nm dia
while core_radius <= 120: #to 240nm dia
	core_rad_range.append(core_radius)
	core_radius += core_step_size


lookup_table = {}

print 'core RI: ', core_RI
print 'shell RI: ', shell_RI

for core_rad in core_rad_range:
	print 'core diameter: ',core_rad*2, ' nm'
	#for each core size create a dictionary of shell radii and associated scattering amplitudes
	shell_data = {}
	
	#start at zero coating thickness
	shell_rad = core_rad
	
	while shell_rad < max_shell_rad:    

		mie = Mie()
		mie.x = 2*math.pi*core_rad/wl
		mie.m = core_RI
		mie.y = 2*math.pi*shell_rad/wl
		mie.m2 = shell_RI

		Itot = 0
		for theta in range(4, 87):  #4, 87
			cos_angle=math.cos(math.radians(theta))
			S12 = mie.S12(cos_angle)
			I1 = S12[0].real**2 + S12[0].imag**2
			I2 = S12[1].real**2 + S12[1].imag**2
			Itot = Itot+ I1 + I2
			
		for theta in range(94, 177):  #94, 177
			cos_angle=math.cos(math.radians(theta))
			S12 = mie.S12(cos_angle)
			I1 = S12[0].real**2 + S12[0].imag**2
			I2 = S12[1].real**2 + S12[1].imag**2
			Itot = Itot+ I1 + I2
		
		
		coating_thickness = (shell_rad-core_rad)
		scattering_amplitude = scat_amp(Itot)
		if scattering_amplitude <= scat_cal_limit:
			shell_data[scattering_amplitude] = coating_thickness
		if scattering_amplitude > scat_cal_limit:
			break
		shell_rad+=shell_step_size  

	
	##add in the "negative coatings:
	i=0
	neg_radius = core_rad
	while i <= 100:
		if neg_radius <= 10:
			break
		neg_radius = neg_radius - core_step_size
		shell_radius = neg_radius
		
		mie = Mie()
		mie.x = 2*math.pi*neg_radius/wl
		mie.m = core_RI
		mie.y = 2*math.pi*shell_radius/wl
		mie.m2 = shell_RI
		
		Itot = 0
		for theta in range(4, 87):  #4, 87
			cos_angle=math.cos(math.radians(theta))
			S12 = mie.S12(cos_angle)
			I1 = S12[0].real**2 + S12[0].imag**2
			I2 = S12[1].real**2 + S12[1].imag**2
			Itot = Itot+ I1 + I2
			
		for theta in range(94, 177):  #94, 177
			cos_angle=math.cos(math.radians(theta))
			S12 = mie.S12(cos_angle)
			I1 = S12[0].real**2 + S12[0].imag**2
			I2 = S12[1].real**2 + S12[1].imag**2
			Itot = Itot+ I1 + I2
		i+=1
		
		coating_thickness = (neg_radius-core_rad)
		scattering_amplitude = scat_amp(Itot)
		shell_data[scattering_amplitude] = coating_thickness
		
	###
	core_diameter = core_rad*2+core_step_size
	lookup_table[core_diameter] = shell_data

	

file = open('coating_lookup_table_WHI_2010_ECSP2-neg_coat.lupckl', 'w')
pickle.dump(lookup_table, file)
file.close()  


