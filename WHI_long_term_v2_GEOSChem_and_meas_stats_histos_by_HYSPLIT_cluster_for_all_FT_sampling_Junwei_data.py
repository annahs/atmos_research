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
import collections

filter_by_RH = False
timezone = -8
calib_stability_uncertainty = 0.1

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST

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
		
#high RH times
high_RH_times_file = open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/high RH times.pkl', 'r')
high_RH_times_list = pickle.load(high_RH_times_file)
high_RH_times_list_v2 = copy.deepcopy(high_RH_times_list)
high_RH_times_file.close()

		

#open cluslist and read into a python list
cluslist = []
CLUSLIST_file = 'C:/hysplit4/working/WHI/CLUSLIST_10'
CLUSLIST_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/HYSPLIT/clustering/CLUSLIST_10'

with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5]))+timedelta(hours = timezone)
		cluslist.append([traj_time,cluster_no])

# sort cluslist by row_datetime in place		
cluslist.sort(key=lambda clus_info: clus_info[0])  

#make a copy for sorting the GeosChem data 
cluslist_GC = copy.deepcopy(cluslist)

############Meaurements
#get full rBC record (in PST and 10 min binned intervals) and put in dictionaries keyed by date 
rBC_24h_data = {} #does not include BB data
rBC_BB_24h_data = {}
rBC_FT_data_cluster_NPac = {}
rBC_FT_data_cluster_SPac = {}
rBC_FT_data_cluster_Cont = {}
rBC_FT_data_cluster_LRT = {}
rBC_FT_data_cluster_GBPS = {}
rBC_FT_data_cluster_BB = {}


with open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI_rBC_record_2009to2013-spikes_removed.rbcpckl', 'r') as f:  #this has only the data of interest, it has been truncated at May 31, 2012 also these row_datetimes are in PST
	full_rBC_record = pickle.load(f)

	for row in full_rBC_record:
		row_datetime = row[0] #in PST
		row_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		row_rBC_mass_conc = row[2]
		row_rBC_mass_conc_LL = row[3]
		row_rBC_mass_conc_UL = row[4]
		
		
		###filter by RH
		if filter_by_RH == True:
			highRH_datetime = high_RH_times_list[0]
			while row_datetime > (highRH_datetime+timedelta(minutes = 30)):
				high_RH_times_list.pop(0)
				if len(high_RH_times_list):
					highRH_datetime = high_RH_times_list[0]
					continue
				else:
					break
			
			if (highRH_datetime-timedelta(minutes=30)) < row_datetime < (highRH_datetime+timedelta(minutes=30)):
				continue
			
		
		#####
		if np.isnan(row_rBC_mass_conc_LL):
			row_abs_err = np.nan
		else:
			row_abs_err = (row_rBC_mass_conc-row_rBC_mass_conc_LL)
		
		#get all 24hr data  (could make it less BB times if we this after the BB data extraction code
		correction_factor_for_massdistr = 1./0.4767
		mass_distr_correction_error = 0.016  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
		corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
		row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]
		if row_date in rBC_24h_data:
			rBC_24h_data[row_date].append(row_data)
		else:
			rBC_24h_data[row_date] = [row_data]
	
			
		#if in a BB time, put this data in 24h BB dict
		if (fire_time1[0] <= row_datetime <= fire_time1[1]) or (fire_time2[0] <= row_datetime <= fire_time2[1]):
			correction_factor_for_massdistr = 1./0.4153
			mass_distr_correction_error = 0.018  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]
			if row_date in rBC_BB_24h_data:
				rBC_BB_24h_data[row_date].append(row_data)
			else:
				rBC_BB_24h_data[row_date] = [row_data]

		
		#pop off any cluslist times that are in the past
		cluslist_current_datetime = cluslist[0][0] #in PST
		while row_datetime > (cluslist_current_datetime + timedelta(hours=3)):
			cluslist.pop(0)
			if len(cluslist):
				cluslist_current_datetime = cluslist[0][0]
				continue
			else:
				break
				
		#get cluster no
		cluslist_current_cluster_no = cluslist[0][1]
		
		#add data to list in cluster dictionaries (1 list per cluster time early night/late night)
		if ((cluslist_current_datetime-timedelta(hours=3)) <= row_datetime <= (cluslist_current_datetime+timedelta(hours=3))):
		
			#if in a BB time,
			if (fire_time1[0] <= row_datetime <= fire_time1[1]) or (fire_time2[0] <= row_datetime <= fire_time2[1]):
				correction_factor_for_massdistr = 1./0.415
				mass_distr_correction_error = 0.018  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
				corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
				row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]
				if cluslist_current_datetime in rBC_FT_data_cluster_BB:
					rBC_FT_data_cluster_BB[cluslist_current_datetime].append(row_data)
				else:
					rBC_FT_data_cluster_BB[cluslist_current_datetime] = [row_data] 
				continue #do not go on to put this data into a cluster dictionary, since it's BB data
		

			if cluslist_current_cluster_no == 9:
				correction_factor_for_massdistr = 1./0.5411
				mass_distr_correction_error = 0.015  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
				corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
				row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]
				if cluslist_current_datetime in rBC_FT_data_cluster_GBPS:
					rBC_FT_data_cluster_GBPS[cluslist_current_datetime].append(row_data)
				else:
					rBC_FT_data_cluster_GBPS[cluslist_current_datetime] = [row_data] 
				
			if cluslist_current_cluster_no == 4:
				correction_factor_for_massdistr = 1./0.4028
				mass_distr_correction_error = 0.028  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
				corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
				row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
				if cluslist_current_datetime in rBC_FT_data_cluster_Cont:
					rBC_FT_data_cluster_Cont[cluslist_current_datetime].append(row_data)
				else:
					rBC_FT_data_cluster_Cont[cluslist_current_datetime] = [row_data]
					
			if cluslist_current_cluster_no in [6,8]:
				correction_factor_for_massdistr = 1./0.4626
				mass_distr_correction_error = 0.032  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
				corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
				row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
				if cluslist_current_datetime in rBC_FT_data_cluster_SPac:
					rBC_FT_data_cluster_SPac[cluslist_current_datetime].append(row_data)
				else:
					rBC_FT_data_cluster_SPac[cluslist_current_datetime] = [row_data]
					
			if cluslist_current_cluster_no in [2,7]:
				correction_factor_for_massdistr = 1./0.5280
				mass_distr_correction_error = 0.019  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
				corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
				row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
				if cluslist_current_datetime in rBC_FT_data_cluster_LRT:
					rBC_FT_data_cluster_LRT[cluslist_current_datetime].append(row_data)
				else:
					rBC_FT_data_cluster_LRT[cluslist_current_datetime] = [row_data]
					
			if cluslist_current_cluster_no in [1,3,5,10]:
				correction_factor_for_massdistr = 1./0.3525
				mass_distr_correction_error = 0.015  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
				corrected_mass_conc = row_rBC_mass_conc*correction_factor_for_massdistr
				row_data = [corrected_mass_conc, row_abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
				if cluslist_current_datetime in rBC_FT_data_cluster_NPac:
					rBC_FT_data_cluster_NPac[cluslist_current_datetime].append(row_data)
				else:
					rBC_FT_data_cluster_NPac[cluslist_current_datetime] = [row_data]

print len(rBC_FT_data_cluster_SPac), len(rBC_FT_data_cluster_NPac), len(rBC_FT_data_cluster_GBPS), len(rBC_FT_data_cluster_LRT), len(rBC_FT_data_cluster_Cont)
	
#24h rBC-meas avgs
SP2_24h_FR = [] 
SP2_24h_BB = []


#6h rBC-meas avgs (FT data)
SP2_6h_NPac = [] 
SP2_6h_SPac = [] 
SP2_6h_Cont = [] 
SP2_6h_LRT  = [] 
SP2_6h_GBPS = [] 
SP2_6h_BB = [] 
SP2_6h_all_non_BB = []
		
#24h avgd data 
for date, mass_data in rBC_24h_data.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean
	
	SP2_24h_FR.append([date_mean,date_mean_err])

	
for date, mass_data in rBC_BB_24h_data.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean
	
	SP2_24h_BB.append([date_mean,date_mean_err])


#6h avgd data	
for date, mass_data in rBC_FT_data_cluster_NPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_NPac.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
for date, mass_data in rBC_FT_data_cluster_SPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_SPac.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
for date, mass_data in rBC_FT_data_cluster_Cont.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_Cont.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])

for date, mass_data in rBC_FT_data_cluster_LRT.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_LRT.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])

for date, mass_data in rBC_FT_data_cluster_GBPS.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_GBPS.append([date_mean,date_mean_err])	
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
for date, mass_data in rBC_FT_data_cluster_BB.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_BB.append([date_mean,date_mean_err])	
	
	
SP2_6h_NPac_m = [row[0] for row in SP2_6h_NPac] 
SP2_6h_SPac_m = [row[0] for row in SP2_6h_SPac] 
SP2_6h_Cont_m = [row[0] for row in SP2_6h_Cont] 
SP2_6h_LRT_m =  [row[0] for row in SP2_6h_LRT]  
SP2_6h_GBPS_m = [row[0] for row in SP2_6h_GBPS] 
#SP2_6h_BB_m = [row[0] for row in SP2_6h_BB]
SP2_6h_all_non_BB_m = [row[0] for row in SP2_6h_all_non_BB]

	
#########print out percentile data and uncertainties for SP2
stats_SP2 = collections.OrderedDict([
('SP2_6h_all_non_BB',[SP2_6h_all_non_BB]),
('SP2_6h_NPac',[SP2_6h_NPac]),
('SP2_6h_SPac',[SP2_6h_SPac]),
('SP2_6h_Cont',[SP2_6h_Cont]),
('SP2_6h_GBPS',[SP2_6h_GBPS]),
('SP2_6h_LRT',[SP2_6h_LRT]),
])
file_list=[]
print 'SP2'
for key, value in stats_SP2.iteritems():
	mass_concs = [row[0] for row in value[0]]
	mass_concs_rel_errs = [row[1] for row in value[0]]
	print key,'no. of samples: ', len(mass_concs)
	print key,'mass concs', np.percentile(mass_concs, 10),np.percentile(mass_concs, 50), np.percentile(mass_concs, 90), np.mean(mass_concs) 
	print key,'errs', np.mean(mass_concs_rel_errs)	
	file_list.append([key,np.percentile(mass_concs, 10),np.percentile(mass_concs, 50), np.percentile(mass_concs, 90), np.mean(mass_concs),np.mean(mass_concs_rel_errs)])
	
#save stats to file 
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
file = open('WHI_long_term_SP2_stats_by_cluster.txt', 'w')
file.write('mass conc stats in ng/m3 - stp' +'\n')
file.write('cluster' + '\t' +  '10th percentile' + '\t' + '50th percentile' + '\t' + '90th percentile' + '\t' + 'mean' + '\t' +'mean rel err' +'\n')
for row in file_list:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()	
#######
	
###################GEOS-Chem

GC_data = {}

GC_runs = ['default','Vancouver_emission','wet_scavenging','no_biomass','All_together']

lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg
level = 9 #1-47 #9 is closest to WHI avg P (WHI 95% CI = 770-793)

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

start_hour = 4
end_hour = 16
i=0
for GC_run in GC_runs: #the runs are 'default','Vancouver_emission','wet_scavenging','no_biomass','All_together'
	print GC_run
	data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/' + GC_run +'/'
	os.chdir(data_dir)
	pressure = []
	for file in os.listdir(data_dir):
		if file.endswith('.hdf'): 
			
			file_year = int(file[2:6])
			file_month = int(file[6:8])
			file_day = int(file[8:10])
			file_hour = int(file[11:13])
			GC_datetime = datetime(file_year,file_month,file_day,file_hour)
			
			###filter by RH
			if filter_by_RH == True:
				highRH_datetime = high_RH_times_list_v2[0]
				while GC_datetime-timedelta(hours=8) > (highRH_datetime):
					high_RH_times_list_v2.pop(0)
					if len(high_RH_times_list_v2):
						highRH_datetime = high_RH_times_list_v2[0]
						continue
					else:
						break
				
				if (GC_datetime-timedelta(hours=8)) == highRH_datetime:
					continue
				
			############
			
			if start_hour <= file_hour < end_hour:  #ignore any times not in the 2000-0800 PST window (0400-1600 UTC)
				hdf_file = SD(file, SDC.READ)
				#pprint(hdf_file.datasets())
				
				#pressures = hdf_file.select('PEDGE-$::PSURF')
				#pressure.append(pressures[level,lat,lon])
				#lats = hdf_file.select('LAT')
				#lons = hdf_file.select('LON')
				##print lats[lat], lons[lon]
				
				if start_hour <= file_hour < (start_hour+6):
					period_midtime = datetime(file_year,file_month,file_day,23) - timedelta(days=1) #this is the early night period of 2000-0200 PST (mid time is 2300 of the previous day when converting from UTC to PST)
					
				if (start_hour+6) <= file_hour < end_hour:	
					period_midtime = datetime(file_year,file_month,file_day,05) #this is the late night period of 0200-0800 PST 

				hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
				hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')

				total_BC_ppbv = hydrophilic_BC[level,lat,lon] + hydrophobic_BC[level,lat,lon]
				BC_conc_ngm3 = total_BC_ppbv*molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	
				
				if period_midtime in sampling_times:  #this excludes BB times already
					if period_midtime in GC_data:
						GC_data[period_midtime][i].append(BC_conc_ngm3)
					else:
						GC_data[period_midtime] = [[],[],[],[],[],'']
						GC_data[period_midtime][i].append(BC_conc_ngm3)
				
				hdf_file.end()	
	i+=1
	
#print np.mean(pressure)

#assign clusters
for line in cluslist_GC:
	
	cluster_datetime = line[0]
	cluster_no = line[1]
	
	if cluster_datetime in sampling_times:
		if cluster_no == 4:
			cluster = 'Cont'	
		
		if cluster_no == 9:
			cluster = 'GBPS'
			
		if cluster_no in [6,8]:
			cluster = 'SPac'
		
		if cluster_no in [2,7]:
			cluster = 'LRT'

		if cluster_no in [1,3,5,10]:
			cluster = 'NPac'
		
		if (fire_time1[0] <= cluster_datetime <= fire_time1[1]) or (fire_time2[0] <= cluster_datetime <= fire_time2[1]):
			cluster = 'BB'

		for period_midtime in GC_data:
			if period_midtime == cluster_datetime:
				GC_data[period_midtime][5] = cluster



all_data =  {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
NPac_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
SPac_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
Cont_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
GBPS_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
LRT_data =  {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}



for period_midtime in GC_data:
	
	default_data = GC_data[period_midtime][0]
	Vancouver_data = GC_data[period_midtime][1]
	wet_scav_data = GC_data[period_midtime][2]
	no_biomass_data = GC_data[period_midtime][3]
	all_together_data = GC_data[period_midtime][4]
	GC_cluster = GC_data[period_midtime][5]
	
	#get the default GC data for all air masses combined
	for key, data in {'default':default_data,'Van':Vancouver_data,'wet_scav':wet_scav_data,'no_bb':no_biomass_data,'all_together':all_together_data}.iteritems():
		mean = np.nanmean(data) 
		rel_err = np.std(data)/mean  
		all_data[key].append([mean,rel_err])
	
	for cluster, data_set in  {'NPac':NPac_data,'SPac':SPac_data,'Cont':Cont_data,'GBPS':GBPS_data,'LRT':LRT_data}.iteritems():
		if GC_cluster == cluster:
			for key, data in {'default':default_data,'Van':Vancouver_data,'wet_scav':wet_scav_data,'no_bb':no_biomass_data,'all_together':all_together_data}.iteritems():
				mean = np.nanmean(data) 
				rel_err = np.std(data)/mean  
				data_set[key].append([mean,rel_err])


#*******PLOTTING*************

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')


#############    histograms   #########

###all 6h data SP2 and default GC run
fig = plt.figure(figsize=(6,8))
bin_number_all_FT = 40
UL_all_FT = 300
bin_range_all_FT = (0,UL_all_FT)

ax1 = plt.subplot2grid((2,1), (0,0), colspan=1)				
ax2 = plt.subplot2grid((2,1), (1,0), colspan=1)

#SP2
ax1.hist(SP2_6h_all_non_BB_m,bins = bin_number_all_FT, range = bin_range_all_FT)
ax1.xaxis.set_visible(True)
ax1.yaxis.set_visible(True)
ax1.set_ylabel('frequency - Measurements')
ax1.xaxis.tick_top()
ax1.xaxis.set_label_position('top') 
ax1.xaxis.set_ticks(np.arange(0, UL_all_FT, 50))
ax1.axvline(np.nanmedian(SP2_6h_all_non_BB_m), color= 'black', linestyle = '--')

#GC
all_default_concs = [row[0] for row in all_data['default']]
print len(all_default_concs), '**'
ax2.hist(all_default_concs,bins = bin_number_all_FT, range = bin_range_all_FT, color = 'green')
ax2.xaxis.set_visible(True)
ax2.yaxis.set_visible(True)
ax2.set_ylabel('frequency - GEOS-Chem')
ax2.xaxis.set_ticks(np.arange(0, UL_all_FT, 50))
ax2.axvline(np.nanmedian(all_default_concs), color= 'black', linestyle = '--')
ax2.set_xlabel('6h rBC mass concentration (ng/m3 - STP)')

plt.subplots_adjust(hspace=0.07)
plt.subplots_adjust(wspace=0.07)

#plt.savefig('histograms - GEOS-Chem and measurements - all non-BB FT - 6h - JW_data.png',bbox_inches='tight')

plt.show()





###histos by air mass for all SP2 and default GC
data_to_plot = [SP2_6h_all_non_BB_m,SP2_6h_NPac_m,SP2_6h_SPac_m,SP2_6h_Cont_m,SP2_6h_GBPS_m,SP2_6h_LRT_m]

for dataset in [all_data,NPac_data,SPac_data,Cont_data,GBPS_data,LRT_data]:
	default_case = dataset['default']
	default_concs = [row[0] for row in default_case]
	print len(default_concs), '**'
	data_to_plot.append(default_concs)
	
bin_number = 22
FT_UL = 280
bin_range = (0,FT_UL)
y_lim = 60

#SP2 vs GC	
fig, axes = plt.subplots(2,6, figsize=(14, 6), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.0)
axs = axes.ravel()	
i=0

for dataset in data_to_plot:	

	if i in [0,1,2,3,4,5]:
		histo = axs[i].hist(dataset, bins = bin_number, range = bin_range, color = 'b')	
		axs[i].xaxis.set_visible(False)
		axs[i].set_ylim(0,y_lim)
	if i in [6,7,8,9,10,11]:
		histo = axs[i].hist(dataset, bins = bin_number, range = bin_range, color = 'g')	
		axs[i].set_ylim(0,y_lim)
	
	axs[i].axvline(np.nanmedian(dataset), color= 'black', linestyle = '--')
	axs[i].set_xlim(0,FT_UL)
	
	if i == 0:
		axs[i].text(0.25, 0.9,'All Data', transform=axs[i].transAxes)
		axs[i].set_ylabel('SP2 data')
	if i == 1:
		axs[i].text(0.25, 0.9,'N. Pacific', transform=axs[i].transAxes)
		
	if i == 2:
		axs[i].text(0.25, 0.9,'S. Pacific', transform=axs[i].transAxes)
		
	if i == 3:
		axs[i].text(0.25, 0.9,'N. Canada', transform=axs[i].transAxes)
		
	if i == 4:
		axs[i].text(0.2, 0.9,'Georgia Basin/Puget Sound', transform=axs[i].transAxes)
	
	if i == 5:
		axs[i].text(0.25, 0.9,'W. Pacific/Asia', transform=axs[i].transAxes)
		
	if i ==6:
		axs[i].set_ylabel('GEOS-Chem data')
	if i ==8:
		axs[i].set_xlabel('6h rBC mass concentration (ng/m3 - STP)')
	if i in [1,2,3,4,7,8,9,10]:
		axs[i].yaxis.set_visible(False)
	if i in [5,11]:
		axs[i].yaxis.set_label_position('right')
		axs[i].yaxis.tick_right()
	
	i+=1
	
plt.savefig('histograms -clustered GEOS-Chem and measurements - 6h FT - v10.png',bbox_inches='tight')

plt.show()

########

#hitos for test-runs and SP2

data_to_plot = [SP2_6h_all_non_BB_m,SP2_6h_NPac_m,SP2_6h_SPac_m,SP2_6h_Cont_m,SP2_6h_GBPS_m,SP2_6h_LRT_m]

save_list = []

labels = ['all data', 'NPac_data','SPac_data','Cont_data','GBPS_data','LRT_data']
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,GBPS_data,LRT_data]:
	case_data = dataset['default']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	save_list.append(['default',labels[i],np.percentile(concs, 10), np.percentile(concs, 50),         np.percentile(concs, 90),         np.mean(concs),rel_err])
	data_to_plot.append(concs)
	i+=1
	
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,GBPS_data,LRT_data]:
	case_data = dataset['Van']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	save_list.append(['Van',labels[i],np.percentile(concs, 10), np.percentile(concs, 50),         np.percentile(concs, 90),         np.mean(concs),rel_err])
	data_to_plot.append(concs)
	i+=1
	
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,GBPS_data,LRT_data]:
	case_data = dataset['wet_scav']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	save_list.append(['wet_scav',labels[i],np.percentile(concs, 10), np.percentile(concs, 50),         np.percentile(concs, 90),         np.mean(concs),rel_err])
	data_to_plot.append(concs)
	i+=1
	
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,GBPS_data,LRT_data]:
	case_data = dataset['no_bb']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	save_list.append(['no_bb',labels[i],np.percentile(concs, 10), np.percentile(concs, 50),         np.percentile(concs, 90),         np.mean(concs),rel_err])
	data_to_plot.append(concs)
	i+=1
	
i=0	
for dataset in [all_data,NPac_data,SPac_data,Cont_data,GBPS_data,LRT_data]:
	case_data = dataset['all_together']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	save_list.append(['all_together',labels[i],np.percentile(concs, 10), np.percentile(concs, 50),         np.percentile(concs, 90),         np.mean(concs),rel_err])
	data_to_plot.append(concs)
	i+=1

#write final list of interval data to file
file = open('GC_stats.txt', 'w')
for row in save_list:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()
	
fig, axes = plt.subplots(6,6, figsize=(14, 14), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.0)
axs = axes.ravel()	
i=0

for dataset in data_to_plot:	

	if i in [0,1,2,3,4,5]:
		histo = axs[i].hist(dataset, bins = bin_number, range = bin_range, color = 'b')	
		axs[i].xaxis.set_visible(False)
		axs[i].set_ylim(0,y_lim)
	else:
		histo = axs[i].hist(dataset, bins = bin_number, range = bin_range, color = 'g')	
		axs[i].set_ylim(0,y_lim)
	
	axs[i].axvline(np.nanmedian(dataset), color= 'black', linestyle = '--')
	axs[i].set_xlim(0,FT_UL)
	
	if i == 0:
		axs[i].text(0.25, 0.9,'All Data', transform=axs[i].transAxes)
		axs[i].set_ylabel('SP2 data')
	if i == 1:
		axs[i].text(0.25, 0.9,'N. Pacific', transform=axs[i].transAxes)		
	if i == 2:
		axs[i].text(0.25, 0.9,'S. Pacific', transform=axs[i].transAxes)		
	if i == 3:
		axs[i].text(0.25, 0.9,'N. Canada', transform=axs[i].transAxes)
	if i == 4:
		axs[i].text(0.2, 0.8,'Georgia Basin/\nPuget Sound', transform=axs[i].transAxes)
	if i == 5:
		axs[i].text(0.25, 0.9,'W. Pacific/Asia', transform=axs[i].transAxes)
	
	if i == 6:
		axs[i].set_ylabel('default GC')
	if i == 12:
		axs[i].set_ylabel('No Vancouver\n emissions')
	if i == 18:
		axs[i].set_ylabel('enhanced\n wet scavenging')
	if i == 24:
		axs[i].set_ylabel('no biomass\n burning')
	if i == 30:
		axs[i].set_ylabel('all changes\n together')
		
	if i in [1,2,3,4, 7,8,9,10, 13,14,15,16, 19,20,21,22, 25,26,27,28, 31,32,33,34]:
		axs[i].yaxis.set_visible(False)
	if i in [5,11,17,23,29,35]:
		axs[i].yaxis.set_label_position('right')
		axs[i].yaxis.tick_right()
	if i == 32:
		axs[i].set_xlabel('6h rBC mass concentration (ng/m3 - STP)')
	
	i+=1
	
plt.savefig('histograms -clustered GEOS-Chem and measurements - 6h FT - v10-tests.png',bbox_inches='tight')

plt.show()



