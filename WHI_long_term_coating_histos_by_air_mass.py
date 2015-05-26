import sys
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt

VED_min = 155	
VED_max = 180


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('coating thicknesses by air mass for 69.76nm to 220.11nm.binpickl', 'r')
coating_data = pickle.load(file)
file.close()

coating_info = {}

for air_mass_name, air_mass_info in coating_data.iteritems():
	print air_mass_name
	coatings=[]
	for row in air_mass_info:
		rBC_VED = row[0]
		coat_th = row[1]
		Dshell_Dcore = (rBC_VED+2*coat_th)/rBC_VED
		
		
		if rBC_VED >= VED_min and rBC_VED < VED_max:
			coatings.append(Dshell_Dcore)
	
	coating_info[air_mass_name] = coatings
	
#####plotting


fig = plt.figure(figsize=(6,12))
bin_number = 20

ax1 =  plt.subplot2grid((6,1), (0,0), )
ax2 =  plt.subplot2grid((6,1), (1,0),sharex=ax1)
ax3 =  plt.subplot2grid((6,1), (2,0),sharex=ax1)
ax4 =  plt.subplot2grid((6,1), (3,0),sharex=ax1)
ax5 =  plt.subplot2grid((6,1), (4,0),sharex=ax1)
ax6 =  plt.subplot2grid((6,1), (5,0),sharex=ax1)

ax1.hist(coating_info['GBPS'], bins=bin_number,histtype='step', label = 'GBPS', normed = 1)
ax1.text(0.6, 0.8,'GBPS', transform=ax1.transAxes)
ax1.yaxis.set_visible(False)
ax1.axvline(np.median(coating_info['GBPS']), color='r', linestyle='--')
#ax1.set_xlim(-80,178)
ax1.set_xlim(0,3)
ax1.set_title(str(VED_min) + '-' + str(VED_max) + 'nm rBC cores')

ax2.hist(coating_info['Cont'], bins=bin_number,histtype='step', label = 'N Can', normed = 1)
ax2.text(0.6, 0.8,'N Can', transform=ax2.transAxes)
ax2.yaxis.set_visible(False)
ax2.axvline(np.median(coating_info['Cont']), color='r', linestyle='--')


ax3.hist(coating_info['LRT'], bins=bin_number,histtype='step', label = 'W Pac/Asia', normed = 1)
ax3.text(0.6, 0.8,'W Pac/Asia', transform=ax3.transAxes)
ax3.yaxis.set_visible(False)
ax3.axvline(np.median(coating_info['LRT']), color='r', linestyle='--')

ax4.hist(coating_info['SPac'], bins=bin_number,histtype='step', label = 'S Pac', normed = 1)
ax4.text(0.6, 0.8,'S Pac', transform=ax4.transAxes)
ax4.yaxis.set_visible(False)
ax4.axvline(np.median(coating_info['SPac']), color='r', linestyle='--')


ax5.hist(coating_info['NPac'], bins=bin_number,histtype='step', label = 'N Pac', normed = 1)
ax5.text(0.6, 0.8,'N Pac', transform=ax5.transAxes)
ax5.yaxis.set_visible(False)
ax5.axvline(np.median(coating_info['NPac']), color='r', linestyle='--')
ax5.set_xlabel('Coating Thickness (nm)')


ax6.hist(coating_info['fresh'], bins=bin_number,histtype='step', label = 'fresh rBC', normed = 1)
ax6.text(0.6, 0.8,'fresh rBC', transform=ax6.transAxes)
ax6.yaxis.set_visible(False)
ax6.axvline(np.median(coating_info['fresh']), color='r', linestyle='--')
#ax6.set_xlabel('Coating Thickness (nm)')
ax6.set_xlabel('Dshell/Dcore')

plt.subplots_adjust(hspace=0.0)
plt.subplots_adjust(wspace=0.0)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
plt.savefig('coating (Dshell_Dcore) histos by air mass' + str(VED_min) + '-' +str(VED_max) + 'nm rBC cores.png', bbox_inches='tight')

plt.show()      
