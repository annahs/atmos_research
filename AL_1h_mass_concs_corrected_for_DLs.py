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
import calendar
from scipy.optimize import curve_fit


start = datetime(2011,3,5,0)
end = datetime(2014,1,1,0)

current_date = start	
while current_date < end:
	print 
	print current_date
	#get fraction within detection range and associated uncertainty from the day's distribution file
	
	file_list = []
	
	distr_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/mass and number distributions/'
	os.chdir(distr_dir)
	for file in os.listdir('.'):
			
		if file.startswith('rBC distributions for'):
			file_date = datetime.strptime(file[22:32],'%Y-%m-%d')

			if file_date == current_date:
				print 'distrs ',file_date
				with open(file, 'r') as f:
					first_line = f.readline()
					fraction_line = first_line[89:].split()
					fraction = float(fraction_line[0])
					frac_err = float(fraction_line[2].strip('%'))
					
					
		
	#get 1h mass concs from files
	data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013 - Alert rBC mass concentrations/2011-2013 - mass concentrations'
	os.chdir(data_dir)
	for file in os.listdir('.'):
			
		if file.endswith('concentration.txt'):
			mass_file_date = datetime.strptime(file[0:8],'%Y%m%d')

			if mass_file_date == current_date:
				print 'masses ',mass_file_date
				with open(file, 'r') as f:
					head1 = f.readline()
					sp2 = head1[38:40]
					head2 = f.readline()
					head3 = f.readline()
					for line in f:
						newline = line.split()
						int_start = newline[0] + '-' + newline[1]
						int_end = newline[2] + '-' + newline[3]
						mass_conc = float(newline[4])
						mass_err = float(newline[5])
						sampled_vol = newline[7]
						rel_mass_err = mass_err/mass_conc
						rel_frac_err = frac_err/fraction
						total_rel_err = rel_mass_err+rel_frac_err
						
						corrected_mass_conc = mass_conc/fraction
						corrected_mass_err  = corrected_mass_conc*total_rel_err
						
						file_list.append([int_start,int_end,mass_conc,mass_err,corrected_mass_conc,corrected_mass_err,sampled_vol])
						
						
	
	file = open('C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013 - Alert rBC mass concentrations/2011-2013 - corrected mass concentrations/'+str(datetime.date(current_date))+' hourly mass concentrations - corrected.txt', 'w')
	file.write('Corrected hourly mass concentration for SP2#' + sp2 + ' at Alert' + '\n') 
	file.write(head2)
	file.write('All mass concentrations have been corrected to account for the fraction of the mass outside the SP2 detection limits.')
	file.write(' This was done by finding the 24hour mass distribution, fitting it with a single lognormal, and calculating the ratio of the area under the measured distribution realtive to the area under the fit distribution.  This daily ratio was used to correct the hourly mass concentrations.' + '\n')
	file.write('interval_start(UTC)\tinterval_end(UTC)\tuncorrected_rBC_mass_concentration(ng/m3)\tuncorrected_rBC_mass_concentration_uncertainty(ng/m3)\tcorrected_rBC_mass_concentration(ng/m3)\tcorrected_rBC_mass_concentration_uncertainty(ng/m3)\tsampling_volume(cc)' + '\n')
	for row in file_list:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
	current_date += timedelta(hours=24)

