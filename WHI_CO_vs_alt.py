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

year_to_plot = 2009

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

GC_LRT  = dict.fromkeys(range(1,47))
GC_NPac = dict.fromkeys(range(1,47))
GC_SPac = dict.fromkeys(range(1,47))
GC_Cont = dict.fromkeys(range(1,47))
GC_all  = dict.fromkeys(range(1,47))

for key in GC_LRT:
	GC_LRT [key] =[]
	GC_NPac[key] =[]
	GC_SPac[key] =[]
	GC_Cont[key] =[]
	GC_all[key]  =[]

default_data['NPac'] = GC_NPac
default_data['SPac'] = GC_SPac
default_data['Cont'] = GC_Cont
default_data['LRT']  = GC_LRT
default_data['all']  = GC_all


lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

start_hour = 4
end_hour = 16


data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/default/'
os.chdir(data_dir)

for file in os.listdir(data_dir):
	if file.endswith('.hdf'): 
				
		file_year = int(file[2:6])
		file_month = int(file[6:8])
		file_day = int(file[8:10])
		file_hour = int(file[11:13])
		GC_datetime = datetime(file_year,file_month,file_day,file_hour)
		GC_UNIX_UTC_ts = calendar.timegm(GC_datetime.utctimetuple())
		
		if file_year not in [year_to_plot]:
			continue
		
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
			i=0
			
					
			for level in range(1,47):
				pressure = pressures[level,lat,lon]
				total_BC_ppbv = hydrophilic_BC[level,lat,lon] + hydrophobic_BC[level,lat,lon]
				BC_conc_ngm3 = total_BC_ppbv*molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	
				
				CO_ppbv = GC_CO[level,lat,lon]
				BC_CO = BC_conc_ngm3/CO_ppbv
				
				default_data[cluster][level].append([pressure,CO_ppbv,GC_datetime])
				default_data['all'][level].append([pressure,CO_ppbv,GC_datetime])
	
	
			hdf_file.end()
				


mean_dict = {'all':[],'NPac':[],'SPac':[],'Cont':[],'LRT':[]}

for cluster in default_data:
	for level in default_data[cluster]:
		
		FT_intervals = {}
		for row in default_data[cluster][level]:
			GC_datetime = row[2]
			pressure = row[0]
			CO = row[1]
			
			if start_hour <= GC_datetime.hour < (start_hour+6):
				period_midtime = datetime(GC_datetime.year,GC_datetime.month,GC_datetime.day,7)
				
			if (start_hour+6) <= GC_datetime.hour < end_hour:	
				period_midtime = datetime(GC_datetime.year,GC_datetime.month,GC_datetime.day,13)			
			
			if period_midtime in FT_intervals:
				FT_intervals[period_midtime].append([pressure,CO])
			else:
				FT_intervals[period_midtime] = [[pressure,CO]]
		
		temp = []
		#get 6-hr means  - analogous to measurements 
		for period_midtime in FT_intervals:	
			mean_conc = np.mean([row[1] for row in FT_intervals[period_midtime]])
			mean_pressure = np.mean([row[0] for row in FT_intervals[period_midtime]])
			temp.append([mean_pressure,mean_conc])

		#get medians for each level	
		average_p = np.mean([row[0] for row in temp])
		med_CO = np.median([row[1] for row in temp])
		min_err_CO = med_CO - np.percentile([row[1] for row in temp],25)
		max_err_CO = np.percentile([row[1] for row in temp],75) - med_CO
		mean_dict[cluster].append([average_p,med_CO,min_err_CO,max_err_CO])


cursor.execute(('''SELECT measCO.UNIX_UTC_start_time, mc.cluster_number, measCO.CO_ppbv
		FROM whi_gc_and_sp2_6h_mass_concs mc
		JOIN whi_co_data measCO on mc.CO_meas_id = measCO.id 
		WHERE mc.RH_threshold = 90 and measCO.CO_ppbv < 250''')
		)
data = cursor.fetchall()


CO_by_cluster = {
'all':[],
'NPac':[],
'SPac':[],
'Cont':[],
'LRT':[]
}

for row in data:
	CO_start_time = datetime.utcfromtimestamp(row[0])
	cluster_number = row[1]
	CO_conc = row[2]

	if CO_start_time.year == year_to_plot:
		CO_by_cluster['all'].append(CO_conc)
		if cluster_number in [6,8,9]:
			CO_by_cluster['SPac'].append(CO_conc)
		if cluster_number in [4]:
			CO_by_cluster['Cont'].append(CO_conc)
		if cluster_number in [2,7]:
			CO_by_cluster['LRT'].append(CO_conc)
		if cluster_number in [1,3,5,10]:
			CO_by_cluster['NPac'].append(CO_conc)
cnx.close()
		

	

#### plotting
cluster_list = ['all','NPac','SPac','Cont','LRT']
colors = ['k','c','g','m','b']


fig = plt.figure()
         
ax1  = plt.subplot2grid((1,1), (0,0), colspan=1)

default_concs = [row[1] for row in mean_dict['all']]
default_concs_min_err = [row[2] for row in mean_dict['all']]
default_concs_max_err = [row[3] for row in mean_dict['all']]
default_pressures = [row[0] for row in mean_dict['all']]

#ax1.errorbar(108, 781.5,xerr=[[13],[28]],fmt='o',color = colors[i])
#ax1.errorbar(105.6, 781.5,xerr=[[11.7],[12.6]],fmt='o',color = 'b') #2009,2010 (june-aug)
#ax1.errorbar(106.4, 781.5,xerr=[[7],[35]],fmt='o',color = 'b') #2009 (june-aug)
ax1.errorbar(103, 781.5,xerr=[[13],[13]],fmt='o',color = 'r') #2010 (june-aug)
#ax1.errorbar(141.4, 781.5,xerr=[[10],[7]],fmt='o',color = colors[i]) #2012 (apr-may)
ax1.errorbar(default_concs, default_pressures,xerr=[default_concs_min_err,default_concs_max_err],fmt='s',color = 'b',linestyle='-')
ax1.invert_yaxis()  
ax1.axhspan(770,793, facecolor='grey', alpha=0.25) #95% CI for pressure at WHI
ax1.set_ylim(910,510)
ax1.set_xlim(80,240)
#ax1.text(0.25, 0.9,'All Data', transform=ax1.transAxes)	
ax1.set_xlabel('CO ppbv')
ax1.set_ylabel('Pressure (hPa)')
plt.show()



fig, axes = plt.subplots(3,2, figsize=(8, 10), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.0)
axs = axes.ravel()	
axes[-1, -1].axis('off')

i=0
for cluster in cluster_list:	
	print cluster
	default_concs = [row[1] for row in mean_dict[cluster]]
	default_concs_min_err = [row[2] for row in mean_dict[cluster]]
	default_concs_max_err = [row[3] for row in mean_dict[cluster]]
	default_pressures = [row[0] for row in mean_dict[cluster]]
	
	meas_CO = [np.mean(CO_by_cluster[cluster])]
	meas_CO_min = [meas_CO - np.percentile(CO_by_cluster[cluster],25)]
	meas_CO_max = [np.percentile(CO_by_cluster[cluster],75) - meas_CO]

	vert_plot_GC = axs[i].errorbar(default_concs, default_pressures,xerr=[default_concs_min_err,default_concs_max_err],fmt='.',color = colors[i],linestyle='-')
	vert_plot_meas = axs[i].errorbar(meas_CO, 781.5,xerr=[meas_CO_min,meas_CO_max],fmt='o',color = colors[i])

	
	
	axs[i].invert_yaxis()  

	axs[i].axhspan(770,793, facecolor='grey', alpha=0.25) #95% CI for pressure at WHI
	
	axs[i].set_ylim(910,510)
	axs[i].set_xlim(80,240)
	
	if i == 0:
		axs[i].text(0.25, 0.9,'All Data', transform=axs[i].transAxes)
	if i == 1:
		axs[i].text(0.25, 0.9,'N. Pacific', transform=axs[i].transAxes)
	if i == 2:
		axs[i].text(0.25, 0.9,'S. Pacific', transform=axs[i].transAxes)
		axs[i].set_ylabel('Pressure (hPa)')
	if i == 3:
		axs[i].text(0.25, 0.9,'N. Canada', transform=axs[i].transAxes)	
		axs[i].set_xlabel('CO ppbv')
	if i == 4:
		axs[i].text(0.25, 0.9,'W. Pacific/Asia', transform=axs[i].transAxes)
		axs[i].set_xlabel('CO ppbv')

	if i in [1,3]:
		axs[i].yaxis.set_label_position('right')
		axs[i].yaxis.tick_right()
	
	if i in [0,1,2]:
		axs[i].set_xticklabels([])
	
	i+=1

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/CO data/'
os.chdir(data_dir)
plt.savefig('GCv10 vertical profile - CO ' + str(year_to_plot) + '.png',bbox_inches='tight')


plt.show()




