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


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

lower_alt = 600
upper_alt = 1200  #max in campaign is 6267m
min_BC_VED = 70
max_BC_VED = 220
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
cloud_droplet_conc = 0.3 #threshold droplet conc from FSSP for in-cloud conditions


flight_times = {
#'science 1'  : [datetime(2015,4,5,9,43),datetime(2015,4,5,13,48),15.6500, 78.2200, 'Longyearbyen (sc1)']	,	   #longyearbyen
##'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
##'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
#'science 2'  : [datetime(2015,4,7,16,31),datetime(2015,4,7,20,48),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
#'science 3'  : [datetime(2015,4,8,13,51),datetime(2015,4,8,16,43),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
#'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,21,22),-70.338, 82.5014,'Alert (sc2-5)']   ,   #Alert
#'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,47),-62.338, 82.0,'Alert (sc2-5)']   ,      #Alert
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
#'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,16),-90.9408, 80.5,'Eureka (sc6-7)'] ,	   #eureka
#'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,52),-95, 80.1,'Eureka (sc6-7)'] ,          #eureka
#'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,49),-133.7306, 67.1,'Inuvik (sc8-10)'],     #inuvik
#'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,36),-133.7306, 69.3617,'Inuvik (sc8-10)'] ,  #inuvik
'science 10' : [datetime(2015,4,21,16,07),datetime(2015,4,21,21,24),-131, 69.55,'Inuvik (sc8-10)'],         #inuvik
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
binned_data = {}
for bin in bins:
	binned_data[bin] = [0,0]


new_data = []
for flight in flight_times:
	UNIX_start_time = calendar.timegm(flight_times[flight][0].utctimetuple())
	UNIX_end_time = calendar.timegm(flight_times[flight][1].utctimetuple())
	print flight

	cursor.execute(('SELECT bc.rBC_mass_fg, bc.coat_thickness_nm_jancalib, bc.LF_scat_amp, bc.actual_scat_amp FROM polar6_coating_2015 bc JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id WHERE bc.UNIX_UTC_ts >= %s and bc.UNIX_UTC_ts < %s and bc.particle_type = %s and fssp.FSSPTotalConc <=%s and ftd.alt >=%s and ftd.alt < %s and bc.rBC_mass_fg IS NOT NULL'),(UNIX_start_time,UNIX_end_time,'incand',cloud_droplet_conc,lower_alt, upper_alt))
	coat_data = cursor.fetchall()

	
	for row in coat_data:
		detectable_notch = True
		mass = row[0] 
		coat = row[1]
		LEO_amp = row[2]
		actual_scat = row[3]
		VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		
		for key in binned_data:
			key_value = float(key)
			interval_end = key_value + interval_length
			if VED >= key_value and VED < interval_end:
				binned_data[key][0] = binned_data[key][0] + 1
				if LEO_amp >= 0:
					binned_data[key][1] = binned_data[key][1] + 1	
		
		if coat !=None:
			#if (VED + coat) < 100 and coat >= 0:
			#	continue
			#else:
			new_data.append([VED,coat])
cnx.close() 
		
#agd
fractions_detectable = []
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

bins = [row[0] for row in fractions_detectable]
fractions = [row[1] for row in fractions_detectable]

		
core_size = [row[0] for row in new_data]
coat_size = [row[1] for row in new_data]

#plotting
fig = plt.figure()
ax1 = fig.add_subplot(111)

ax1.hexbin(core_size, coat_size, cmap=cm.jet, gridsize = 50,mincnt=5)#, norm= norm) #bins='log', norm=norm
ax1.set_xlabel('BC_VED')
ax1.set_ylabel('LEO_coating_thickness')
ax1.set_ylim(-40,240)


ax2 = ax1.twinx()
ax2.scatter(bins, fractions, color = 'r')
ax2.set_ylabel('fraction of detectable notch positions')
ax2.set_ylim(0,1)

plt.xlim(70,220)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/')
#plt.savefig('coating vs core hexbin - with LEO fit fraction -  '+flight_times[flight][4]+' - cloud-free.png', bbox_inches='tight') 
#plt.savefig('coating vs core hexbin - with LEO fit fraction -  Longyearbyen,Alert,Eureka (sc1-7) - cloud-free.png', bbox_inches='tight') 


plt.show()     
