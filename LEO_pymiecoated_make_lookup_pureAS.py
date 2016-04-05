from pymiecoated import Mie
import numpy as np
import matplotlib.pyplot as plt
import pickle
import math
import sys
import os
from pprint import pprint 

#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/'
lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/lookup files/'

os.chdir(lookup_dir)

#************setup********************

wl = 1064 #nm
AS_RI = complex(1.5, 0)
PSL_RI = complex(1.59,0)

scat_cal_limit = 50000

def scat_amp(Itotal):
	#calc_scattering_amplitude = (545/2.68)*Itotal  # UBCSP2 POLAR6 2015-spring - 545 from slope of PSL calib plot, 446 from 200nm PSL alone, /2.68 to scale to Alert calib scattering
	calc_scattering_amplitude = (225)*Itotal  # UBCSP2 WHI 2012
	
	return calc_scattering_amplitude
	
	
#**********calc the lookup table*************************

#set the maximum shell radius (note: this is a radius not a thickness)
max_shell_rad = 540 #this is radius of core + shell (in nm)
shell_step_size = 0.5 # will give 1nm steps in final diameter
core_step_size = 0.5 # will give 1nm steps in final diameter

#set the range of core radii to be used
core_rad_range = []
core_radius = 50  #60nm dia
while core_radius <= 180:
	core_rad_range.append(core_radius)
	core_radius += core_step_size


lookup_table = {}

#set ranges for integration of scattering
incr = 0.1
range1 = []
i=2.5
while i <=77.5:
	range1.append(i)
	i+=incr
	
range2 = []
i=102.5
while i <= 167.5:
	range2.append(i)
	i+=incr	
	
print 'RI: ', AS_RI

scat_dict = {}
for core_rad in core_rad_range:
	print 'core diameter: ',core_rad*2, ' nm'
	mie = Mie()
	mie.x = 2*math.pi*core_rad/wl
	mie.m = AS_RI

	#calc intensity
	Itot_fwd = 0
	Itot_back = 0
	for theta in range1:
		cos_angle=math.cos(math.radians(theta))
		S12 = mie.S12(cos_angle)
		I1 = S12[0].real**2 + S12[0].imag**2
		I2 = S12[1].real**2 + S12[1].imag**2
		Itot_fwd = (Itot_fwd + I1 + I2)
		
	for theta in range2:
		cos_angle=math.cos(math.radians(theta))
		S12 = mie.S12(cos_angle)
		I1 = S12[0].real**2 + S12[0].imag**2
		I2 = S12[1].real**2 + S12[1].imag**2
		Itot_back = (Itot_back + I1 + I2)
	
	Itot = np.mean([Itot_fwd*incr,Itot_back*incr])*math.pi/2
	scattering_amplitude = scat_amp(Itot)
	
	if scattering_amplitude <= scat_cal_limit:
		lookup_table[scattering_amplitude] = core_rad*2
	if scattering_amplitude > scat_cal_limit:
		break
	 

pprint(scat_dict)

file = open('Nonincand_lookup_table_WHI_2012_UBCSP2-used_factor225.lupckl', 'w')
pickle.dump(lookup_table, file)
file.close()  


