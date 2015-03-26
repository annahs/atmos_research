import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
from datetime import timedelta
import copy

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST


#set up dictionaries

GC_GBPS = dict.fromkeys(range(1,48))
GC_LRT = dict.fromkeys(range(1,48))
GC_NPac = dict.fromkeys(range(1,48))
GC_SPac = dict.fromkeys(range(1,48))
GC_Cont = dict.fromkeys(range(1,48))
GC_all = dict.fromkeys(range(1,48))

timezone = -8

for key in GC_GBPS:
	GC_GBPS[key] =[]
	GC_LRT [key] =[]
	GC_NPac[key] =[]
	GC_SPac[key] =[]
	GC_Cont[key] =[]
	GC_all[key]  =[]
#constants
molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

#open cluslist and read into a python list
cluslist = []
CLUSLIST_file = 'C:/hysplit4/working/WHI/CLUSLIST_10'
with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5]))+timedelta(hours = timezone)
		cluslist.append([traj_time,cluster_no])

# sort cluslist by row_datetime in place		
cluslist.sort(key=lambda clus_info: clus_info[0])  


#make a copy for sorting the GeosChem data and get rid of all early night points since we don't have GC data for the early night anyways
cluslist_GC = []
cluslist_copy = copy.copy(cluslist)

for line in cluslist_copy:
	traj_datetime = line[0]
	cluster_no = line[1]
	if traj_datetime.hour == 5:
		cluslist_GC.append([traj_datetime,cluster_no])



##GEOS-Chem data
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/sarahWhistlerData'
os.chdir(data_dir)

for file in os.listdir('.'):
        if file.endswith('N.txt'):
            print file
            first_line = True
            
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

		
					for level in range(1,48):
											
						T = float(Templine[level]) # in K
						P = float(Pressureline[level])
						BC_conc_ppb = float(BCline[level]) # in molBC/molAIR 
						#correction to STP
						volume_ambient = (R*T)/(P)
						volume_STP = volume_ambient*(P/101325)*(273/T)
						STP_correction_factor =  volume_ambient/volume_STP
						BC_conc_ngm3 = STP_correction_factor*BC_conc_ppb*molar_mass_BC*ng_per_g*GEOS_Chem_factor/(R*T/P)  #this is per /m3 ambient so for STP must mult by vol_amb/vol_stp	
               

						if date > datetime.strptime('20120531', '%Y%m%d'):
							break
                
						#pop off any cluslist times that are in the past
						cluslist_current_datetime = cluslist_GC[0][0] #in PST
						cluslist_current_date = datetime(cluslist_current_datetime.year, cluslist_current_datetime.month, cluslist_current_datetime.day)

						while date > cluslist_current_date:

							cluslist_GC.pop(0)
							if len(cluslist_GC):
								cluslist_current_datetime = cluslist_GC[0][0]
								cluslist_current_date = datetime(cluslist_current_datetime.year, cluslist_current_datetime.month, cluslist_current_datetime.day)
								continue
							else:
								break

						#get cluster no
						cluslist_current_cluster_no = cluslist_GC[0][1]

						if cluslist_current_date == date:
						
							if (fire_time1[0] <= cluslist_current_date <= fire_time1[1]) or (fire_time2[0] <= cluslist_current_date <= fire_time2[1]):
								continue
								
							if cluslist_current_cluster_no == 9:
								GC_GBPS[level].append([P,BC_conc_ngm3])
								GC_all[level].append([P,BC_conc_ngm3])
								
							if cluslist_current_cluster_no == 4:
								GC_Cont[level].append([P,BC_conc_ngm3])
								GC_all[level].append([P,BC_conc_ngm3])
								
							if cluslist_current_cluster_no in [6,8]:
								GC_SPac[level].append([P,BC_conc_ngm3])
								GC_all[level].append([P,BC_conc_ngm3])
								
							if cluslist_current_cluster_no in [2,7]:
								GC_LRT[level].append([P,BC_conc_ngm3])
								GC_all[level].append([P,BC_conc_ngm3])
								
							if cluslist_current_cluster_no in [1,3,5,10]:
								GC_NPac[level].append([P,BC_conc_ngm3])
								GC_all[level].append([P,BC_conc_ngm3])

GC_GBPS_data = []
GC_Cont_data = []
GC_SPac_data = []
GC_NPac_data = []
GC_LRT_data = []
GC_all_data = []

for key, value in GC_GBPS.iteritems():
	P =  [row[0] for row in value]
	BC = [row[1] for row in value]
	avg_p = np.mean(P)
	avg_BCconc = np.mean(BC)
	GC_GBPS_data.append([avg_p,avg_BCconc])
	
for key, value in GC_Cont.iteritems():
	P =  [row[0] for row in value]
	BC = [row[1] for row in value]
	avg_p = np.mean(P)
	avg_BCconc = np.mean(BC)
	GC_Cont_data.append([avg_p,avg_BCconc])
	
for key, value in GC_SPac.iteritems():
	P =  [row[0] for row in value]
	BC = [row[1] for row in value]
	avg_p = np.mean(P)
	avg_BCconc = np.mean(BC)
	GC_SPac_data.append([avg_p,avg_BCconc])
	
for key, value in GC_NPac.iteritems():
	P =  [row[0] for row in value]
	BC = [row[1] for row in value]
	avg_p = np.mean(P)
	avg_BCconc = np.mean(BC)
	GC_NPac_data.append([avg_p,avg_BCconc])
	
for key, value in GC_LRT.iteritems():
	P =  [row[0] for row in value]
	BC = [row[1] for row in value]
	avg_p = np.mean(P)
	avg_BCconc = np.mean(BC)
	GC_LRT_data.append([avg_p,avg_BCconc])
	
for key, value in GC_all.iteritems():
	P =  [row[0] for row in value]
	BC = [row[1] for row in value]
	avg_p = np.mean(P)
	avg_BCconc = np.mean(BC)
	GC_all_data.append([avg_p,avg_BCconc])

GC_GBPS_P = [row[0] for row in GC_GBPS_data]
GC_GBPS_BC = [row[1] for row in GC_GBPS_data]

GC_Cont_P = [row[0] for row in GC_Cont_data]
GC_Cont_BC = [row[1] for row in GC_Cont_data]

GC_SPac_P = [row[0] for row in GC_SPac_data]
GC_SPac_BC = [row[1] for row in GC_SPac_data]

GC_NPac_P = [row[0] for row in GC_NPac_data]
GC_NPac_BC = [row[1] for row in GC_NPac_data]

GC_LRT_P = [row[0] for row in GC_LRT_data]
GC_LRT_BC = [row[1] for row in GC_LRT_data]

GC_all_P =  [row[0] for row in GC_all_data]
GC_all_BC = [row[1] for row in GC_all_data]

#plotting

print 'plotting'
fig = plt.figure(figsize=(8, 8))

marker_size = 8
error_line_size = 2
cap = 5
alpha_val = 1

#GC_2009
ax1 = fig.add_subplot(111)
ax1.plot(GC_all_BC, GC_all_P,   '<k-', markerfacecolor='none', label = 'All nighttime data')
ax1.plot(GC_SPac_BC, GC_SPac_P, 'og-', markerfacecolor='none', label = 'S. Pacific')
ax1.plot(GC_NPac_BC, GC_NPac_P, '*c-', markerfacecolor='none', label = 'N. Pacific')
ax1.plot(GC_GBPS_BC, GC_GBPS_P, '^r-', markerfacecolor='none', label = 'Georgia Basin/Puget Sound')
ax1.plot(GC_LRT_BC, GC_LRT_P,   'sb-', markerfacecolor='none', label = 'W. Pacific/Asia')
ax1.plot(GC_Cont_BC, GC_Cont_P, '>m-', markerfacecolor='none', label = 'N. Canada')


#ax1.axhline(782, color= 'black', linestyle = '--')
ax1.axhspan(770,793, facecolor='grey', alpha=0.25) #95% CI for pressure at WHI
ax1.set_xlim(20,250)
ax1.set_ylim(200,900)
ax1.invert_yaxis()  
#ax1.set_xscale('log')
plt.xlabel('[BC] ng/m3 - STP')
plt.ylabel('Pressure hPa')

plt.legend(loc=1, borderpad=0.5, numpoints = 1)  

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem')
plt.savefig('GEOS-Chem BC conc vs alt by FT cluster.png',bbox_inches='tight',dpi=600)


plt.show()