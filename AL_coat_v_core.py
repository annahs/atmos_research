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

start_date = datetime(2013,10,1)
end_date =   datetime(2013,11,1)
hour_step = 168#336#168

min_BC_VED = 80
max_BC_VED = 220
interval = 5
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)


##############initialize binning variables

def createBinDict(min_VED,max_VED,interval_length):
	bins = []
	start_size = min_VED #VED in nm
	end_size = max_VED #VED in nm
	 #in nm

	#create list of size bins
	while start_size < end_size:    
		bins.append(start_size)
		start_size += interval_length

	#create dictionary with size bins as keys
	bin_data = {}
	for bin in bins:
		bin_data[bin] = [0,0]
	
	return bin_data
	

binned_data_min = createBinDict(min_BC_VED,max_BC_VED,interval)	
binned_data_max = createBinDict(min_BC_VED,max_BC_VED,interval)	
fraction_successful = createBinDict(min_BC_VED,max_BC_VED,interval)	
	
for key in binned_data_min:
	binned_data_min[key] = []
	binned_data_max[key] = []
	
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert Data/coating data/')
while start_date < end_date:
	print start_date
	period_end = start_date + timedelta(hours = hour_step)
	UNIX_start_time = calendar.timegm(start_date.utctimetuple())
	UNIX_end_time   = calendar.timegm(period_end.utctimetuple())


	cursor.execute(('''SELECT rBC_mass_fg,coat_thickness_nm_min,coat_thickness_nm_max,LF_scat_amp,UNIX_UTC_ts
						FROM alert_leo_coating_data 
						WHERE UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and HK_flag = 0 and coat_thickness_nm_min >= %s and rBC_mass_fg  IS NOT NULL'''),
						(UNIX_start_time,UNIX_end_time,0))
	coat_data = cursor.fetchall()

	#hexbin plot
	new_data = []
	file_data = []
	for row in coat_data:
		mass = row[0] 
		min_coat = row[1]
		max_coat = row[2]
		LEO_amp = row[3]
		UNIX_UTC_ts = row[4]
		date_time = datetime.utcfromtimestamp(UNIX_UTC_ts)
		VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		
		for key in fraction_successful:
			key_value = float(key)
			interval_end = key_value + interval
			if VED >= key_value and VED < interval_end:
				fraction_successful[key][0] = fraction_successful[key][0] + 1
				if LEO_amp >= 0:
					fraction_successful[key][1] = fraction_successful[key][1] + 1	
					if min_coat != None:
						binned_data_min[key].append(min_coat)
					if max_coat != None:
						binned_data_max[key].append(max_coat)

	#fraction detectable
	fractions_detectable = []
	for bin, counts in fraction_successful.iteritems():
		bin_midpoint = bin + interval/2.0
		total_particles = counts[0]
		detectable_notches = counts[1]
		
		try:
			fraction_detectable = detectable_notches*1.0/total_particles
		except:
			fraction_detectable=np.nan
			
		fractions_detectable.append([bin_midpoint,fraction_detectable])

	fractions_detectable.sort()
	
	#coats for cores
	min_coats = []
	max_coats = []
	for bin, counts in binned_data_min.iteritems():
		bin_midpoint = bin + interval/2.0
		min_avg_coat = np.mean(binned_data_min[bin])
		min_coats.append([bin_midpoint,min_avg_coat])
	min_coats.sort()
	
	for bin, counts in binned_data_max.iteritems():
		bin_midpoint = bin + interval/2.0
		max_avg_coat = np.mean(binned_data_max[bin])
		max_coats.append([bin_midpoint,max_avg_coat])
	max_coats.sort()
	
	
	#make lists
	bins = [row[0] for row in fractions_detectable]
	fractions = [row[1] for row in fractions_detectable]

	
	core_size_min = [row[0] for row in min_coats]
	coat_min_size = [row[1] for row in min_coats]
	core_size_max = [row[0] for row in max_coats]
	coat_max_size = [row[1] for row in max_coats]

	
	
	
	#plotting
	fig = plt.figure(figsize=(8,6))
	ax1 = fig.add_subplot(111)

	min = ax1.fill_between(core_size_min, coat_min_size, coat_max_size,label = 'coating min', alpha = 0.5)#, norm= norm) #bins='log', norm=norm
	ax1.scatter(core_size_min, coat_min_size, label = 'coating max',color='k')#, norm= norm) #bins='log', norm=norm
	ax1.scatter(core_size_max, coat_max_size, label = 'coating max',color='r')#, norm= norm) #bins='log', norm=norm
	ax1.set_xlabel('rBC core diameter')
	ax1.set_ylabel('range of coating thickness')
	ax1.set_ylim(0,220)
	ax1.set_xlim(min_BC_VED,max_BC_VED)
	fig.subplots_adjust(right=0.8)
	
	ax2 = ax1.twinx()
	ax2.scatter(bins, fractions, color = 'g', marker = 's')
	ax2.set_ylabel('fraction of detectable notch positions',color='g')
	ax2.set_ylim(0,1)
	plt.xlim(min_BC_VED,max_BC_VED)
	
	#ax3 = fig.add_subplot(212)
	#ax3.scatter(core_size_max, coat_max_size)#, norm= norm) #bins='log', norm=norm
	#ax3.set_xlabel('rBC core diameter')
	#ax3.set_ylabel('Maximum coating thickness')
	#ax3.set_ylim(-30,220)
	#ax3.set_xlim(min_BC_VED,max_BC_VED)
    #
	#ax4 = ax3.twinx()
	#ax4.scatter(bins, fractions, color = 'r')
	#ax4.set_ylabel('fraction of detectable notch positions',color='r')
	#ax4.set_ylim(0,1)
	#plt.xlim(min_BC_VED,max_BC_VED)
	#plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/coating data/' + file_name + '.png', bbox_inches='tight')
	plt.legend()
	plt.show()
	
	#start_date = start_date + timedelta(hours = hour_step)
	#continue

	#  

	start_date = start_date + timedelta(hours = hour_step)
	
cnx.close()