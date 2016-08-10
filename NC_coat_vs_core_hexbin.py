import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.cm as cm
from matplotlib import dates
import calendar
from copy import deepcopy


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

lower_alt = 0
upper_alt = 6267  #max in campaign is 6267m
min_BC_VED = 70
max_BC_VED = 220
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
cloud_droplet_conc = 0.3 #threshold droplet conc from FSSP for in-cloud conditions


flight_times = {
'science 1'  : [datetime(2015,4,5,9,43),datetime(2015,4,5,13,48),15.6500, 78.2200, 'Longyearbyen']	,	   #longyearbyen
##'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
##'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,31),datetime(2015,4,7,20,48),-62.338, 82.5014,'Alert']    ,  #Alert
'science 3'  : [datetime(2015,4,8,13,51),datetime(2015,4,8,16,43),-62.338, 82.5014,'Alert']    ,  #Alert
'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,21,22),-70.338, 82.5014,'Alert']   ,   #Alert
'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,47),-62.338, 82.0,'Alert']   ,      #Alert
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,16),-90.9408, 80.5,'Eureka'] ,	   #eureka
'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,52),-95, 80.1,'Eureka'] ,          #eureka
#'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,49),-133.7306, 67.1,'Inuvik (sc8-10)'],     #inuvik
#'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,36),-133.7306, 69.3617,'Inuvik (sc8-10)'] ,  #inuvik
#'science 10' : [datetime(2015,4,21,16,07),datetime(2015,4,21,21,24),-131, 69.55,'Inuvik (sc8-10)'],         #inuvik
#
}




##############initialize binning variables
bins = []
start_size = min_BC_VED #VED in nm
end_size = max_BC_VED #VED in nm
interval_length = 5 #in nm

#create list of size bins
while start_size < end_size:    
    bins.append(start_size)
    start_size += interval_length

#create dictionary with size bins as keys
Longyearbyen_binned_data = {}
for bin in bins:
	Longyearbyen_binned_data[bin] = [0,0]

Alert_binned_data = deepcopy(Longyearbyen_binned_data)
Eureka_binned_data = deepcopy(Longyearbyen_binned_data)
All_binned_data = deepcopy(Longyearbyen_binned_data)

Longyearbyen = []
Alert = []
Eureka = []
All = []

def add_leo_counts(binned_data):
	for key in binned_data:
		key_value = float(key)
		interval_end = key_value + interval_length
		if VED >= key_value and VED < interval_end:
			binned_data[key][0] = binned_data[key][0] + 1
			if LEO_amp >= 0:
				binned_data[key][1] = binned_data[key][1] + 1	

	return binned_data
	
	
def make_fractions_list(binned_data,fractions_detectable):
	for bin, counts in binned_data.iteritems():
		bin_midpoint = bin + interval_length/2.0
		total_particles = counts[0]
		detectable_notches = counts[1]
		
		try:
			fraction_detectable = detectable_notches*1.0/total_particles
		except:
			fraction_detectable=np.nan
			
		fractions_detectable.append([bin_midpoint,fraction_detectable])

	fractions_detectable.sort()

	return fractions_detectable

for flight in flight_times:
	location = flight_times[flight][4]
	UNIX_start_time = calendar.timegm(flight_times[flight][0].utctimetuple())
	UNIX_end_time = calendar.timegm(flight_times[flight][1].utctimetuple())
	print flight

	cursor.execute(('''SELECT bc.rBC_mass_fg, 
							bc.coat_thickness_nm_jancalib, 
							bc.LF_scat_amp, 
							bc.actual_scat_amp 
						FROM polar6_coating_2015 bc 
						JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id 
						JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id 
						WHERE bc.UNIX_UTC_ts >= %s and 
							bc.UNIX_UTC_ts < %s and 
							bc.particle_type = %s and 
							fssp.FSSPTotalConc <=%s and 
							ftd.alt >=%s and ftd.alt < %s and 
							bc.rBC_mass_fg IS NOT NULL'''),
						(UNIX_start_time,UNIX_end_time,'incand',cloud_droplet_conc,lower_alt, upper_alt))
	coat_data = cursor.fetchall()

	
	for row in coat_data:
		detectable_notch = True
		mass = row[0] 
		coat = row[1]
		LEO_amp = row[2]
		actual_scat = row[3]
		VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		
		if location == 'Longyearbyen':
			Longyearbyen_binned_data = add_leo_counts(Longyearbyen_binned_data)
			All_binned_data = add_leo_counts(All_binned_data)
			if coat !=None:
				Longyearbyen.append([VED,coat])
				All.append([VED,coat])
		if location == 'Alert':
			Alert_binned_data = add_leo_counts(Alert_binned_data)
			All_binned_data = add_leo_counts(All_binned_data)
			if coat !=None:
				Alert.append([VED,coat])
				All.append([VED,coat])
		if location == 'Eureka':
			Eureka_binned_data = add_leo_counts(Eureka_binned_data)
			All_binned_data = add_leo_counts(All_binned_data)
			if coat !=None:
				Eureka.append([VED,coat])
				All.append([VED,coat])
			
		
cnx.close() 
		
#agd

Longyearbyen_fractions_detectable = []
Alert_fractions_detectable = []
Eureka_fractions_detectable = []
All_fractions_detectable = []

Longyearbyen_fractions_detectable = make_fractions_list(Longyearbyen_binned_data,Longyearbyen_fractions_detectable)
Alert_fractions_detectable = make_fractions_list(Alert_binned_data,Alert_fractions_detectable)
Eureka_fractions_detectable = make_fractions_list(Eureka_binned_data,Eureka_fractions_detectable)
All_fractions_detectable = make_fractions_list(All_binned_data,All_fractions_detectable)



L_bins = [row[0] for row in Longyearbyen_fractions_detectable]
L_fractions = [row[1] for row in Longyearbyen_fractions_detectable]
L_core_size = [row[0] for row in Longyearbyen]
L_coat_size = [row[1] for row in Longyearbyen]

A_bins = [row[0] for row in Alert_fractions_detectable]
A_fractions = [row[1] for row in Alert_fractions_detectable]
A_core_size = [row[0] for row in Alert]
A_coat_size = [row[1] for row in Alert]

E_bins = [row[0] for row in Eureka_fractions_detectable]
E_fractions = [row[1] for row in Eureka_fractions_detectable]
E_core_size = [row[0] for row in Eureka]
E_coat_size = [row[1] for row in Eureka]

All_bins = [row[0] for row in All_fractions_detectable]
All_fractions = [row[1] for row in All_fractions_detectable]
All_core_size = [row[0] for row in All]
All_coat_size = [row[1] for row in All]

#plotting
m_inct = 5
color_min = m_inct
color_max = 2500
#color_map = cm.nipy_spectral
color_map = cm.gist_ncar
#color_map = cm.rainbow


fig = plt.figure(figsize=(12,8))
                     
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)					
ax4  = plt.subplot2grid((2,2), (1,1), colspan=1)					
	

			
coats1 = ax1.hexbin(L_core_size,L_coat_size, cmap=color_map, gridsize = 50,mincnt=m_inct,clim=(color_min,color_max))  
ax1.set_xlabel('BC_VED')
ax1.set_ylabel('LEO_coating_thickness')
ax1.set_ylim(-30,240)
ax1.set_xlim(70,220)
ax1a = ax1.twinx()
ax1a.scatter(L_bins, L_fractions, color = 'r')
#ax1a.set_ylabel('fraction of detectable notch positions')
ax1a.set_yticks([])
ax1a.set_ylim(0,1)
ax1a.set_xlim(70,220)
ax1.text(0.94,0.93,'A)', transform=ax1.transAxes)


coats = ax2.hexbin(A_core_size, A_coat_size, cmap=color_map, gridsize = 50,mincnt=m_inct,clim=(color_min,color_max))#, norm= norm) #bins='log', norm=norm
ax2.set_xlabel('BC_VED')
#ax2.set_ylabel('LEO_coating_thickness')
ax2.set_yticks([])
ax2.set_ylim(-30,240)
ax2.set_xlim(70,220)
ax2a = ax2.twinx()
ax2a.scatter(A_bins, A_fractions, color = 'r')
ax2a.set_ylabel('fraction of detectable notch positions')
ax2a.set_ylim(0,1)
ax2a.set_xlim(70,220)
ax2.text(0.94,0.93,'B)', transform=ax2.transAxes)


coats = ax3.hexbin(E_core_size, E_coat_size, cmap=color_map, gridsize = 50,mincnt=m_inct,clim=(color_min,color_max))#, norm= norm) #bins='log', norm=norm
ax3.set_xlabel('BC_VED')
ax3.set_ylabel('LEO_coating_thickness')
ax3.set_ylim(-30,240)
ax3.set_xlim(70,220)
ax3a = ax3.twinx()
ax3a.scatter(E_bins, E_fractions, color = 'r')
#ax3a.set_ylabel('fraction of detectable notch positions')
ax3a.set_yticks([])
ax3a.set_ylim(0,1)
ax3a.set_xlim(70,220)
ax3.text(0.94,0.93,'C)', transform=ax3.transAxes)


coats4 = ax4.hexbin(All_core_size, All_coat_size, cmap=color_map, gridsize = 50,mincnt=m_inct,clim=(color_min,color_max))#, norm= norm) #bins='log', norm=norm
ax4.set_xlabel('BC_VED')
#ax4.set_ylabel('LEO_coating_thickness')
ax4.set_yticks([])
ax4.set_ylim(-30,240)
ax4.set_xlim(70,220)
ax4a = ax4.twinx()
ax4a.scatter(All_bins, All_fractions, color = 'r')
ax4a.set_ylabel('fraction of detectable notch positions')
ax4a.set_ylim(0,1)
ax4a.set_xlim(70,220)
ax4.text(0.94,0.93,'D)', transform=ax4.transAxes)


fig.subplots_adjust(right=0.85)
cbar_ax = fig.add_axes([0.9, 0.15, 0.03, 0.7])
cb = fig.colorbar(coats4, cax=cbar_ax)
cb.set_label('counts')

fig.subplots_adjust(wspace=0.05)


os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/')
plt.savefig('coating vs core hexbin - with LEO fit fraction - cloud-free.png', bbox_inches='tight') 

plt.show()


#all locations only
fig = plt.figure(figsize=(12,8))
ax4  = plt.subplot2grid((1,1), (0,0))        
		
coats4 = ax4.hexbin(All_core_size, All_coat_size, cmap=color_map, gridsize = 50,mincnt=m_inct)#, norm= norm) #bins='log', norm=norm
ax4.set_xlabel('BC_VED')
ax4.set_ylabel('Coating Thickness (nm)')
ax4.set_ylim(-30,240)
ax4.set_xlim(70,220)
ax4a = ax4.twinx()
ax4a.scatter(All_bins, All_fractions, color = 'r')
ax4a.set_ylabel('fraction of detectable notch positions', color = 'r')
ax4a.set_ylim(0,1)
ax4a.set_xlim(70,220)

fig.subplots_adjust(right=0.82)
cbar_ax = fig.add_axes([0.9, 0.10, 0.03, 0.7])
cb = fig.colorbar(coats4, cax=cbar_ax)
cb.set_label('counts')

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/')
plt.savefig('coating vs core hexbin - with LEO fit fraction - cloud-free - sc1-7.png', bbox_inches='tight') 

plt.show()
