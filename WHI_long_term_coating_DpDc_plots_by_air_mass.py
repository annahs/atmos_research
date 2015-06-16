import sys
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt

VED_min = 155
VED_max = 180

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating thicknesses by air mass for 69.76nm to 220.11nm-spikes_fixed.binpickl', 'r')
coating_data = pickle.load(file)
file.close()

DpDc_vals = []
DpDc_names=[]

for air_mass_name, air_mass_info in coating_data.iteritems():
	print air_mass_name
	Dc_vals= []
	Dp_vals= []
		
	for row in air_mass_info:
		rBC_VED = row[0]
		coat_th = row[1]
		Dp = 2*coat_th+rBC_VED
		
		if rBC_VED >= VED_min and rBC_VED < VED_max:
			Dc_vals.append(rBC_VED)
			Dp_vals.append(Dp)
	
	
	#get dp/dc for traj
	sum_of_Dp_cubes = 0
	for Dp in Dp_vals:
		sum_of_Dp_cubes = sum_of_Dp_cubes + Dp**3	
		
	sum_of_Dc_cubes = 0
	for Dc in Dc_vals:
		sum_of_Dc_cubes = sum_of_Dc_cubes + Dc**3

	try:
		DpDc = math.pow((sum_of_Dp_cubes/sum_of_Dc_cubes),(1./3.))
	except:
		DpDc = np.nan
		print 'Dp/Dc', sum_of_Dp_cubes, sum_of_Dc_cubes
	print DpDc
	
	if air_mass_name == 'Cont':
		air_mass_name = 'N Can'
	if air_mass_name == 'LRT':
		air_mass_name = 'W Pac/Asia'
	
	DpDc_names.append(air_mass_name)
	DpDc_vals.append(DpDc)
	
print DpDc_names
print DpDc_vals

#####plotting

fig = plt.figure()
N=len(DpDc_vals)
ax = fig.add_subplot(111)

ind = np.arange(N)  # the x locations for the groups
width = 0.6       # the width of the bars

rects1 = ax.bar(ind, DpDc_vals, width, color='b')

# add some text for labels, title and axes ticks
ax.set_ylabel('Dp/Dc')
ax.set_title(str(VED_min) + '-' + str(VED_max) + 'nm rBC cores')
ax.set_xticks(ind+width/2)
ax.set_xticklabels( DpDc_names )
ax.axhline(1, color='r', linestyle='--')
ax.set_ylim(0,2.2)
#os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
#plt.savefig('DpDc by air mass ' + str(VED_min) + '-' +str(VED_max) + 'nm rBC cores.png', bbox_inches='tight')

plt.show()      
