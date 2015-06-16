import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle


data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/sarahWhistlerData'
os.chdir(data_dir)

level = 10 #1-47 #10 is closest to WHI avg P (WHI 95% CI = 770-793)
level_up = level+1
level_dn = level-1

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST

GC_data = []

for file in os.listdir('.'):
	if file.endswith('N.txt'):  #these are the night files (2-4 and 5-7 PST)

		with open(file, 'r') as f:
			
			while True:
				BCline_all = f.readline()
				Templine_all = f.readline()
				Pressureline_all = f.readline()
				boxheightline_all = f.readline()
				
				if not (BCline_all and Templine_all and Pressureline_all and boxheightline_all):
					break

				BCline = BCline_all.split(',')
				Templine = Templine_all.split(',')
				Pressureline = Pressureline_all.split(',')
				
				date = datetime.strptime(BCline[0], '%Y%m%d')
				
				T = float(Templine[level]) # in K
				P = float(Pressureline[level])*100 #original data in hPa, this converts to Pa
				BC_conc_ppb = float(BCline[level]) # in molBC/molAIR 
				#correction to STP
				volume_ambient = (R*T)/(P)
				volume_STP = volume_ambient*(P/101325)*(273/T)
				STP_correction_factor =  volume_ambient/volume_STP
				BC_conc_ngm3 = STP_correction_factor*BC_conc_ppb*molar_mass_BC*ng_per_g*GEOS_Chem_factor/(R*T/P)  #this is per /m3 ambient so for STP must mult by vol_amb/vol_stp	
			
				#if in a BB time, #do not go on to put this data into a dictionary
				if (fire_time1[0] <= date <= fire_time1[1]) or (fire_time2[0] <= date <= fire_time2[1]):
					continue 
			
				GC_data.append(BC_conc_ngm3)
				
print np.percentile(GC_data, 10), np.median(GC_data),np.percentile(GC_data, 90), np.mean(GC_data)