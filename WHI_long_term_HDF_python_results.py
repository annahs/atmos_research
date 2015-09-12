import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
from pyhdf.SD import SD, SDC, SDS
from operator import add

##sampling times
sampling_times_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/WHI_SP2_6h_rBC_mass_concs.txt'
sampling_times = []
with open(sampling_times_file,'r') as f:
	f.readline()
	for line in f:
		newline = line.split()
		sampling_date = newline[0]
		sampling_time = newline[1]
		sampling_datetime = datetime(int(sampling_date[0:4]),int(sampling_date[5:7]),int(sampling_date[8:10]),int(sampling_time[0:2]))
		sampling_times.append(sampling_datetime)
		
	
#GC data

GC_data = {}

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/no_biomass/'  # ['default','Vancouver_emission','wet_scavenging','no_biomass','All_together']



lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg
level = 9 #1-47 #9 is closest to WHI avg P (WHI 95% CI = 770-793)

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9
i=0
pressure = []

start_hour = 4
end_hour = 16


os.chdir(data_dir)
for file in os.listdir(data_dir):
	if file.endswith('.hdf'): 

		file_year = int(file[2:6])
		file_month = int(file[6:8])
		file_day = int(file[8:10])
		file_hour = int(file[11:13])
		file_datetime = datetime(file_year,file_month,file_day,file_hour)
		
		#if (file_year == 2009 and file_month in [7,8]) or  (file_year == 2010 and file_month in [6,7]) or  (file_year == 2012 and file_month in [4,5]):
		
		if start_hour <= file_hour < end_hour:  #ignore any times not in the 2000-0800 PST window (0400-1600 UTC)
			hdf_file = SD(file, SDC.READ)
			
			
			#pprint(hdf_file.datasets())
			
			#pressures = hdf_file.select('PEDGE-$::PSURF')
			#pressure.append(pressures[level,lat,lon])
			#lats = hdf_file.select('LAT')
			#lons = hdf_file.select('LON')
			#print lats[lat], lons[lon]
			
			if start_hour <= file_hour < (start_hour+6):
				period_midtime = datetime(file_year,file_month,file_day,23) - timedelta(days=1) #this is the early night period of 2000-0200 PST (mid time is 2300 of the previous day when converting from UTC to PST)
				
			if (start_hour+6) <= file_hour < end_hour:	
				period_midtime = datetime(file_year,file_month,file_day,05) #this is the late night period of 0200-0800 PST 
		   
			
			#period_midtime = datetime(file_year,file_month,file_day) #this is the late night period of 0200-0800 PST 
		   
		   
			hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
			hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')
		
			total_BC_ppbv = (hydrophilic_BC[level,lat,lon]) + (hydrophobic_BC[level,lat,lon])
			
			#hydrophilic_BC.__del__()
			#hydrophobic_BC.__del__()
			
			#print total_BC_ppbv
			#if i>2:
			#	sys.exit()
			Factor =  (1000 * 1e2 * 1e6 * 1e-9) / (8.31 * 273)

			BC_conc_ngm3 = total_BC_ppbv*(molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273)))  #101325/(R*273) corrects to STP 	
			temp_BC = total_BC_ppbv * Factor * 12 *1000

			
			if period_midtime in sampling_times:  #this excludes BB times already
				if period_midtime in GC_data:
					GC_data[period_midtime].append(BC_conc_ngm3)
				else:
					GC_data[period_midtime] = [BC_conc_ngm3]
			
			
			hdf_file.end()	
			i+=1
			
##save stats to file 
#os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
#file = open('WHI_long_term_GC_JW_stats_Vancouver_emission.txt', 'w')
#file.write('datetime' + '\t' +  'mean_bc_conc_ug/m3' +'\n')
#temp = []
#for period_midtime in GC_data:
#	mean_BC_conc = np.nanmean(GC_data[period_midtime])
#	row = [datetime(period_midtime.year,period_midtime.month,period_midtime.day), period_midtime.hour, mean_BC_conc]
#	temp.append(row)
#	
#temp.sort()
#	
#for row in temp:
#	line = '\t'.join(str(x) for x in row)
#	file.write(line + '\n')
#
#file.close()	
				
				
				
#print np.mean(pressure)

GC_6h_all_non_BB = []			

for period_midtime in GC_data:
	
	mean_BC_conc = np.nanmean(GC_data[period_midtime])
	GC_6h_all_non_BB.append(mean_BC_conc)

print np.percentile(GC_6h_all_non_BB, 10),np.percentile(GC_6h_all_non_BB, 50), np.percentile(GC_6h_all_non_BB, 90), np.mean(GC_6h_all_non_BB) 




## full grid calcs

#for file in os.listdir(data_dir):
#	if file.endswith('.hdf'): 
#		#print file
#		file_year = int(file[2:6])
#		file_month = int(file[6:8])
#		file_day = int(file[8:10])
#		file_hour = int(file[11:13])
#		
#		if 3 <= file_hour < 15:  #ignore any times not in the 2000-0800 PST window (0400-1600 UTC)
#			hdf_file = SD(file, SDC.READ)
#			#pprint(hdf_file.datasets())
#			
#			#pressures = hdf_file.select('PEDGE-$::PSURF')
#			#pressure.append(pressures[level,lat,lon])
#			#lats = hdf_file.select('LAT')
#			#lons = hdf_file.select('LON')
#			#print lats[lat], lons[lon]
#			
#			if file_hour < 9:
#				period_midtime = datetime(file_year,file_month,file_day,23) - timedelta(days=1) #this is the early night period of 2000-0200 PST (mid time is 2300 of the previous day when converting from UTC to PST)
#				
#			if 9 <= file_hour < 15:	
#				period_midtime = datetime(file_year,file_month,file_day,05) #this is the late night period of 0200-0800 PST 
#			
#			#skip BB times
#			if (fire_time1[0] <= period_midtime <= fire_time1[1]) or (fire_time2[0] <= period_midtime <= fire_time2[1]):
#				hdf_file.end()	
#				continue
#			
#		
#
#			hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
#			hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')
#		
#			#total_BC_ppbv = np.matrix(hydrophilic_BC[level,lat,lon]) + np.matrix(hydrophobic_BC[level,lat,lon])
#			total_BC_ppbv = map(add, hydrophilic_BC[level,:,:], hydrophobic_BC[level,:,:])
#			
#			#hydrophilic_BC.__del__()
#			#hydrophobic_BC.__del__()
#			
#			#print total_BC_ppbv
#			#if i>2:
#			#	sys.exit()
#			
#			Factor =  (1000 * 1e2 * 1e6 * 1e-9) / (8.31 * 273)
#			BC_conc_ngm3 = total_BC_ppbv#*(molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273)))  #101325/(R*273) corrects to STP 	
#			#temp_BC = total_BC_ppbv * Factor * 12 *1000
#				
#			#if period_midtime not in GC_data:
#			#	GC_data[period_midtime] = []
#			#	
#			##if period_midtime in sampling_times:
#			#GC_data[period_midtime].append(BC_conc_ngm3)
#            
#
#			if period_midtime in sampling_times:
#				if period_midtime in GC_data:
#					GC_data[period_midtime].append(BC_conc_ngm3)
#				else:
#					GC_data[period_midtime] = [BC_conc_ngm3]
#				
#			
#			hdf_file.end()	
#			i+=1
##print np.mean(pressure)
#
#GC_6h_all_non_BB = []			
#
#for period_midtime in GC_data:
#	
#	mean_BC_conc = np.mean(GC_data[period_midtime], axis=0)
#	test_val = mean_BC_conc[lat,lon]*(molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273)))  #101325/(R*273)
#	GC_6h_all_non_BB.append(test_val)
#
#print np.percentile(GC_6h_all_non_BB, 10),np.percentile(GC_6h_all_non_BB, 50), np.percentile(GC_6h_all_non_BB, 90), np.mean(GC_6h_all_non_BB) 




