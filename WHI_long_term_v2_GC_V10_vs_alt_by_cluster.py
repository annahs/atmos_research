import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
from datetime import timedelta
import calendar
import mysql.connector
from pyhdf.SD import SD, SDC, SDS



#fire times
timezone = timedelta(hours = -8)

fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time1_UNIX_UTC_start = float(calendar.timegm((fire_time1[0]-timezone).utctimetuple()))
fire_time1_UNIX_UTC_end = float(calendar.timegm((fire_time1[1]-timezone).utctimetuple()))

fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST
fire_time2_UNIX_UTC_start = float(calendar.timegm((fire_time2[0]-timezone).utctimetuple()))
fire_time2_UNIX_UTC_end = float(calendar.timegm((fire_time2[1]-timezone).utctimetuple()))

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#set up cluster dictionaries
default_data = {}
other_data = {}

scenarios = [default_data,other_data]

for scenario_dict in scenarios:

	GC_LRT  = dict.fromkeys(range(1,48))
	GC_NPac = dict.fromkeys(range(1,48))
	GC_SPac = dict.fromkeys(range(1,48))
	GC_Cont = dict.fromkeys(range(1,48))
	GC_all  = dict.fromkeys(range(1,48))

	for key in GC_LRT:
		GC_LRT [key] =[]
		GC_NPac[key] =[]
		GC_SPac[key] =[]
		GC_Cont[key] =[]
		GC_all[key]  =[]
	
	scenario_dict['NPac'] = GC_NPac
	scenario_dict['SPac'] = GC_SPac
	scenario_dict['Cont'] = GC_Cont
	scenario_dict['LRT']  = GC_LRT
	scenario_dict['all']  = GC_all


lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

start_hour = 3
end_hour = 15

#GC_runs = ['default','wet_scavenging']
GC_runs = ['default','Vancouver_emission']
#GC_runs = ['default','all_together']



for GC_run in GC_runs: 
	print GC_run
	if GC_run == 'default':
		scenario = default_data
	else:
		scenario = other_data
	
	data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/' + GC_run +'/'
	os.chdir(data_dir)
	
	for file in os.listdir(data_dir):
		if file.endswith('.hdf'): 
			
			file_year = int(file[2:6])
			file_month = int(file[6:8])
			file_day = int(file[8:10])
			file_hour = int(file[11:13])
			GC_datetime = datetime(file_year,file_month,file_day,file_hour)
			GC_UNIX_UTC_ts = calendar.timegm(GC_datetime.utctimetuple())
			
			if start_hour <= file_hour < end_hour:  #ignore any times not in the 2000-0800 window 
				
				#avoid fire times
				if (fire_time1_UNIX_UTC_start <= GC_UNIX_UTC_ts <= fire_time1_UNIX_UTC_end) or  (fire_time2_UNIX_UTC_start <= GC_UNIX_UTC_ts <= fire_time2_UNIX_UTC_end):
					continue
			
				#avoid high RH times
				cursor.execute(('SELECT RH from whi_high_rh_times_2009to2012 where high_RH_start_time <= %s and high_RH_end_time > %s'),(GC_UNIX_UTC_ts,GC_UNIX_UTC_ts))
				RH_data = cursor.fetchone()
				if RH_data != None:
					if RH_data[0] > 90:
						continue
				
				#get appropriate cluster 
				cursor.execute(('SELECT cluster_number FROM whi_ft_cluster_times_2009to2012 where cluster_start_time <= %s and cluster_end_time > %s'),(GC_UNIX_UTC_ts,GC_UNIX_UTC_ts))
				cluster_number_result = cursor.fetchone()
				if cluster_number_result == None:
					continue
				else:
					cluster_number = cluster_number_result[0]

					
						
				if 	cluster_number in [1,3,5,10]:
					cluster = 'NPac'
				if 	cluster_number in [6,8,9]:
					cluster = 'SPac'
				if 	cluster_number in [4]:
					cluster = 'Cont' 	
				if 	cluster_number in [2,7]:
					cluster = 'LRT'
				
			
				hdf_file = SD(file, SDC.READ)
				GC_CO = hdf_file.select('IJ-AVG-$::CO') #3d CO data in ppbv (molBC/molAIR)
				pressures = hdf_file.select('PEDGE-$::PSURF')
				hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
				hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')
				GC_SO4 = hdf_file.select('IJ-AVG-$::SO4')
				i=0
				
						
				for level in range(1,47):
					pressure = pressures[level,lat,lon]
					total_BC_ppbv = hydrophilic_BC[level,lat,lon] + hydrophobic_BC[level,lat,lon]
					BC_conc_ngm3 = total_BC_ppbv*molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	
					CO_ppbv = GC_CO[level,lat,lon]
					SO4_ppbv = GC_SO4[level,lat,lon]
							
					scenario[cluster][level].append([pressure,BC_conc_ngm3,GC_datetime])
					scenario['all'][level].append([pressure,BC_conc_ngm3,GC_datetime])
		
		
				hdf_file.end()
				

default_sc_means = {'all':[],'NPac':[],'SPac':[],'Cont':[],'LRT':[]}
wet_scav_sc_means = {'all':[],'NPac':[],'SPac':[],'Cont':[],'LRT':[]}


for scenario in scenarios:

	if scenario == default_data:
		mean_dict = default_sc_means
	if scenario == other_data:
		mean_dict = wet_scav_sc_means
		
	for cluster in scenario:
		for level in scenario[cluster]:
			
			FT_intervals = {}
			for row in scenario[cluster][level]:
				GC_datetime = row[2]
				pressure = row[0]
				BC_conc = row[1]
				
				if start_hour <= GC_datetime.hour < (start_hour+6):
					period_midtime = datetime(GC_datetime.year,GC_datetime.month,GC_datetime.day,7)
					
				if (start_hour+6) <= GC_datetime.hour < end_hour:	
					period_midtime = datetime(GC_datetime.year,GC_datetime.month,GC_datetime.day,13)			
				
				if period_midtime in FT_intervals:
					FT_intervals[period_midtime].append([pressure,BC_conc])
				else:
					FT_intervals[period_midtime] = [[pressure,BC_conc]]
			
			temp = []
			for period_midtime in FT_intervals:	
				mean_conc = np.mean([row[1] for row in FT_intervals[period_midtime]])
				mean_pressure = np.mean([row[0] for row in FT_intervals[period_midtime]])
				std_conc = 2*np.std([row[1] for row in FT_intervals[period_midtime]])
				std_pressure = 2*np.std([row[0] for row in FT_intervals[period_midtime]])
				temp.append([mean_pressure,mean_conc,std_pressure])
				
			average_p = np.median([row[0] for row in temp])
			average_p_err = np.mean([row[2] for row in temp])
			average_conc = np.median([row[1] for row in temp])
			average_conc_err = np.median([row[1] for row in temp])
			mean_dict[cluster].append([average_p,average_conc,average_p_err,average_conc_err])

			

#### plotting
cluster_list = ['all','NPac','SPac','Cont','LRT']
colors = ['k','b','g','r','orange']

SP2_medians = {
'all':[38.1,6.4],
'NPac':[42.7,6.7],
'SPac':[27.5,5.2],
'Cont':[62.7,10.7],
'LRT':[36.9,6.6]
}

fig, axes = plt.subplots(3,2, figsize=(8, 10), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.0)
axs = axes.ravel()	
axes[-1, -1].axis('off')

i=0
for cluster in cluster_list:	
	print cluster
	default_concs = [row[1] for row in default_sc_means[cluster]]
	default_concs_err = [row[3] for row in default_sc_means[cluster]]
	default_pressures = [row[0] for row in default_sc_means[cluster]]
	default_pressures_err = [row[2] for row in default_sc_means[cluster]]

	wet_scav_concs = [row[1] for row in wet_scav_sc_means[cluster]]
	wet_scav_pressures = [row[0] for row in wet_scav_sc_means[cluster]]
	wet_scav_pressures_err = [row[2] for row in wet_scav_sc_means[cluster]]
	
	meas_conc = SP2_medians[cluster][0]
	meas_uncertainty = SP2_medians[cluster][1]
	
	vert_plot_default = axs[i].plot(default_concs, default_pressures,color = colors[i],linewidth=2.0,marker = None)	
	vert_plot_wet_scav = axs[i].plot(wet_scav_concs, wet_scav_pressures, color = colors[i], linestyle='--',linewidth=2.0)	
	vert_plot_meas = axs[i].errorbar(meas_conc, 781.5, xerr=meas_uncertainty, fmt='o',color = colors[i],linewidth=2.0)

	axs[i].invert_yaxis()  

	axs[i].axhspan(770,793, facecolor='grey', alpha=0.25) #95% CI for pressure at WHI
	
	axs[i].set_ylim(910,510)
	axs[i].set_xlim(0,190)
	
	if i == 0:
		axs[i].text(0.25, 0.9,'All Data', transform=axs[i].transAxes)
	if i == 1:
		axs[i].text(0.25, 0.9,'N. Pacific', transform=axs[i].transAxes)
	if i == 2:
		axs[i].text(0.25, 0.9,'S. Pacific', transform=axs[i].transAxes)
		axs[i].set_ylabel('Pressure (hPa)')
	if i == 3:
		axs[i].text(0.25, 0.9,'N. Canada', transform=axs[i].transAxes)	
		axs[i].set_xlabel('[rBC mass](ng/m3 - STP)')
	if i == 4:
		axs[i].text(0.25, 0.9,'W. Pacific/Asia', transform=axs[i].transAxes)
		axs[i].set_xlabel('[rBC mass](ng/m3 - STP)')

	if i in [1,3]:
		axs[i].yaxis.set_label_position('right')
		axs[i].yaxis.tick_right()
	
	if i in [0,1,2]:
		axs[i].set_xticklabels([])
	
	i+=1

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/'
os.chdir(data_dir)
#plt.savefig('GCv10 vertical profile - medians - with SP2 90% RH filter - Van.png',bbox_inches='tight')


plt.show()


cnx.close()


