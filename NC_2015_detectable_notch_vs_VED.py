import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from pprint import pprint
import sqlite3
import calendar
from datetime import datetime
from datetime import timedelta
import math
import copy


timezone = -8

#set parameters
instrument_locn = 'POLAR6'
type_particle = 'incand'
start_date = datetime(2015,4,21)
end_date  =  datetime(2015,4,22)
rBC_density = 1.8 
incand_sat = 3750
LF_max = 45000 #above this is unreasonable

min_rBC_mass = 0.25#100-#0.94#1.63-#120 2.6-#140 3.86-#160nm 0.25-#65
min_BC_VED = (((min_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7
max_rBC_mass = 10.05#140 3.86-160 5.5-#180nm 7.55-#200 10.05-#220
max_BC_VED = (((max_rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7

begin_data = calendar.timegm(start_date.timetuple())
end_data = calendar.timegm(end_date.timetuple())


##############initialize binning variables
bins = []
start_size = 65 #VED in nm
end_size = 220 #VED in nm
interval_length = 5 #in nm

#create list of size bins
while start_size < end_size:    
    bins.append(start_size)
    start_size += interval_length

#create dictionary with size bins as keys
binned_data = {}
for bin in bins:
	binned_data[bin] = [0,0]

LOG_EVERY_N = 10000
particles =0 
fit_failure=0
not_enough_data=0
LF_high=0
flat_fit = 0
#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

for row in c.execute('''SELECT rBC_mass_fg, LF_scat_amp, sp2b_file, actual_scat_amp
FROM SP2_coating_analysis 
WHERE instr_locn=? and particle_type=? and rBC_mass_fg>=? and  rBC_mass_fg<? and unix_ts_utc>=? and unix_ts_utc<?
ORDER BY unix_ts_utc''', 
(instrument_locn,type_particle, min_rBC_mass, max_rBC_mass, begin_data,end_data)):	
	particles+=1
	detectable_notch = True
	
	rBC_mass = row[0]
	LEO_amp = row[1]
	file = row[2]
	actual_scat = row[3]
	rBC_VED = (((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm

	
	#parse if notch detectable
	if LEO_amp == -2:  #early evap
		detectable_notch = False	
	if LEO_amp == -1:
		fit_failure +=1	
		detectable_notch = False
	if LEO_amp == -3:
		not_enough_data +=1
		detectable_notch = False
	if LEO_amp > LF_max:
		LF_high +=1
		detectable_notch = False
	if LEO_amp <= 1 and actual_scat > 100:
		flat_fit+=1
		detectable_notch = False
		
	for key in binned_data:
		key_value = float(key)
		interval_end = key_value + interval_length
		if rBC_VED >= key_value and rBC_VED < interval_end:
			binned_data[key][0] = binned_data[key][0] + 1
			if detectable_notch == True:		
				binned_data[key][1] = binned_data[key][1] + 1

				
	
	if (particles % LOG_EVERY_N) == 0:
		print 'record: ', particles
		
conn.close()
	
print 'fit_failure', fit_failure
print 'not_enough_data', not_enough_data
print 'LF_high', LF_high
print 'flat_fit', flat_fit

#agd
fractions_detectable = []
for bin, counts in binned_data.iteritems():
	bin_midpoint = bin + interval_length/2.0
	total_particles = counts[0]
	detectable_notches = counts[1]*100
	
	try:
		fraction_detectable = detectable_notches*1.0/total_particles
	except:
		fraction_detectable=np.nan
		
	fractions_detectable.append([bin_midpoint,fraction_detectable])

fractions_detectable.sort()

#save data
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/')
file = open('fraction of detectable notch positions by BC core size for ' +  str(start_date.year) + str(start_date.month).zfill(2) + str(start_date.day).zfill(2) + '.pickl', 'w')
pickle.dump(fractions_detectable, file)
file.close()


##plotting

bins = [row[0] for row in fractions_detectable]
fractions = [row[1] for row in fractions_detectable]

#####plotting

fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(bins, fractions)
ax.set_ylabel('frctaion of detectable notch positions')
ax.set_xlabel('rBC core VED')
plt.ylim(0,100)
plt.xlim(60,220)

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/fraction of detectable split detector notches AND sufficient data pts for fitting vs core size for ' +  str(start_date.year) + str(start_date.month).zfill(2) + str(start_date.day).zfill(2)+'.png')

plt.show()      

