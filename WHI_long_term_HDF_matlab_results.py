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


	
timezone = timedelta(hours=-8)
		
#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST

	
#GC data

GC_data = {}

files = [
'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/matlab_output/Vancouver_output_PST.txt', #wet_scavening_output_PST.txt, default_output_PST, Vancouver_output_PST
]




start_hour = 4
end_hour = 16


for file in files:
	with open(file,'r') as f: 
		f.readline()
		for line in f:
			newline = line.split()
			file_year = int(newline[0][0:4])
			file_month = int(newline[0][4:6])
			file_day = int(newline[0][6:8])
			file_hour = int(newline[1])
			file_datetime = datetime(file_year,file_month,file_day,file_hour)
			bc_conc_ngm3 = float(newline[2])*1000
			
			#if (file_year == 2009 and file_month in [7,8]) or  (file_year == 2010 and file_month in [6,7]) or  (file_year == 2012 and file_month in [4,5]):
							  
							  
			##skip BB times
			#if (fire_time1[0] <= file_datetime <= fire_time1[1]) or (fire_time2[0] <= file_datetime <= fire_time2[1]):
			#	#print 'fire!', period_midtime	
			#	continue
		  

			#if file_datetime in sampling_times:
			if file_datetime in GC_data:
				GC_data[file_datetime].append(bc_conc_ngm3)
			else:
				GC_data[file_datetime] = [bc_conc_ngm3]
				
					
#print np.mean(pressure)

GC_6h_all_non_BB = []			

for period_midtime in GC_data:
	
	mean_BC_conc = np.nanmean(GC_data[period_midtime])
	GC_6h_all_non_BB.append(mean_BC_conc)

print np.percentile(GC_6h_all_non_BB, 10, interpolation='midpoint'),np.percentile(GC_6h_all_non_BB, 50, interpolation='midpoint'), np.percentile(GC_6h_all_non_BB, 90, interpolation='midpoint'), np.mean(GC_6h_all_non_BB) 


