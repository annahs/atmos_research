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

save_file = False

start_date = datetime(2012,4,1)
end_date =   datetime(2012,5,1)
hour_step = 1#336#168

min_BC_VED = 80
max_BC_VED = 220
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)


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
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert Data/coating data/')

new_data = []

while start_date < end_date:
	print start_date
	period_end = start_date + timedelta(hours = hour_step)
	UNIX_start_time = calendar.timegm(start_date.utctimetuple())
	UNIX_end_time   = calendar.timegm(period_end.utctimetuple())


	cursor.execute(('''SELECT rBC_mass_fg,coat_thickness_nm_min,coat_thickness_nm_max,LF_scat_amp,UNIX_UTC_ts
						FROM alert_leo_coating_data 
						WHERE UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and HK_flag = 0 and rBC_mass_fg IS NOT NULL
						LIMIT 10000'''),
						(UNIX_start_time,UNIX_end_time))
	coat_data = cursor.fetchall()

	#hexbin plot
	for row in coat_data:
		mass = row[0] 
		min_coat = row[1]
		max_coat = row[2]
		LEO_amp = row[3]
		UNIX_UTC_ts = row[4]
		date_time = datetime.utcfromtimestamp(UNIX_UTC_ts)
		VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		
		for key in binned_data:
			key_value = float(key)
			interval_end = key_value + interval_length
			if VED >= key_value and VED < interval_end:
				binned_data[key][0] = binned_data[key][0] + 1
				if LEO_amp >= 0:
					binned_data[key][1] = binned_data[key][1] + 1	
		
		if min_coat != None and max_coat != None and LEO_amp > 100:
			if VED < min_BC_VED:
				continue
			new_data.append([VED,min_coat,max_coat])
	
	start_date = start_date + timedelta(hours = hour_step)
			
print len(new_data)
 
#fraction detectable
fractions_detectable = []
for bin, counts in binned_data.iteritems():
	bin_midpoint = bin + interval_length/2.0
	total_particles = counts[0]
	detectable_notches = counts[1]
	
	try:
		fraction_detectable = detectable_notches*1.0/total_particles
	except:
		fraction_detectable=np.nan
		
	fractions_detectable.append([bin,bin+interval_length,fraction_detectable])

fractions_detectable.sort()

bins = [row[0]+interval_length/2 for row in fractions_detectable]
fractions = [row[2] for row in fractions_detectable]
#number_max = np.max([row[3] for row in fractions_detectable])
#number_particles = [row[3]*1.0/number_max for row in fractions_detectable]

core_size = [row[0] for row in new_data]
coat_min_size = [row[1] for row in new_data]
coat_max_size = [row[2] for row in new_data]


	
	
#plotting
fig = plt.figure(figsize=(8,6))
ax1 = fig.add_subplot(111)

min = ax1.hexbin(core_size, coat_min_size, cmap=cm.jet, gridsize = 40,mincnt=1)#, norm= norm) #bins='log', norm=norm
#ax1.hist2d(core_size, coat_size, bins = 60)
ax1.set_xlabel('rBC core diameter')
ax1.set_ylabel('Coating thickness')
ax1.set_ylim(-30,220)
ax1.set_xlim(min_BC_VED,max_BC_VED)
fig.subplots_adjust(right=0.8)
cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
cbar = fig.colorbar(min, cax=cbar_ax)
cbar.ax.get_yaxis().labelpad = 10
cbar.set_label('# of particles')

ax2 = ax1.twinx()
ax2.scatter(bins, fractions, color = 'r')
#ax2.scatter(bins, number_particles, color = 'k')
ax2.set_ylabel('fraction of detectable notch positions',color='r')
ax2.set_ylim(0,1)
plt.xlim(min_BC_VED,max_BC_VED)

#ax3 = fig.add_subplot(212)
#ax3.hexbin(core_size, coat_max_size, cmap=cm.jet, gridsize = 40,mincnt=1)#, norm= norm) #bins='log', norm=norm
#ax3.set_xlabel('rBC core diameter')
#ax3.set_ylabel('Maximum coating thickness')
#ax3.set_ylim(-30,220)
#ax3.set_xlim(min_BC_VED,max_BC_VED)
#
#ax4 = ax3.twinx()
#ax4.scatter(bins, fractions, color = 'r')
##ax4.scatter(bins, number_particles, color = 'k')
#ax4.set_ylabel('fraction of detectable notch positions',color='r')
#ax4.set_ylim(0,1)
#plt.xlim(min_BC_VED,max_BC_VED)

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/seasonal coating/April 2012.png', bbox_inches='tight')
plt.show()


  

	
	
cnx.close()