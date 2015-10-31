import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
import calendar
import mysql.connector


timezone = -8
calib_stability_uncertainty = 0.1

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST

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


#make a copy for sorting the GeosChem data and get rid of all early night points since we don't have GC data for the early night anyways
cluslist_GC = []
cluslist_copy = copy.copy(cluslist)

for line in cluslist_copy:
	traj_datetime = line[0]
	cluster_no = line[1]
	if traj_datetime.hour == 5:
		cluslist_GC.append([traj_datetime,cluster_no])
 
 
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
	
			
		#if in a BB time, put this data in BB dict
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
	
###################GEOS-Chem

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/sarahWhistlerData'
os.chdir(data_dir)

level = 10 #1-47 #10 is closest to WHI avg P (WHI 95% CI = 770-793)
level_up = level+1
level_dn = level-1

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

GC_24h_FR = []
GC_24h_BB = []

for file in os.listdir('.'):
	if file.endswith('24h.txt'):
		
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
				
				###get data for levels above and below curent
				T_up = float(Templine[level_up]) # in K
				P_up = float(Pressureline[level_up])*100 #original data in hPa, this converts to Pa
				BC_conc_ppb_up = float(BCline[level_up]) # in molBC/molAIR 
				volume_ambient_up = (R*T_up)/(P_up)
				volume_STP_up = volume_ambient_up*(P_up/101325)*(273/T_up)
				STP_correction_factor_up =  volume_ambient_up/volume_STP_up
				BC_conc_ngm3_up = STP_correction_factor_up*BC_conc_ppb_up*molar_mass_BC*ng_per_g*GEOS_Chem_factor/(R*T_up/P_up)  #this is per /m3 ambient so for STP must mult by vol_amb/vol_stp
				
				T_dn = float(Templine[level_dn]) # in K
				P_dn = float(Pressureline[level_dn])*100 #original data in hPa, this converts to Pa
				BC_conc_ppb_dn = float(BCline[level_dn]) # in molBC/molAIR 		
				volume_ambient_dn = (R*T_dn)/(P_dn)
				volume_STP_dn = volume_ambient_dn*(P_dn/101325)*(273/T_dn)
				STP_correction_factor_dn =  volume_ambient_dn/volume_STP_dn
				BC_conc_ngm3_dn = STP_correction_factor_dn*BC_conc_ppb_dn*molar_mass_BC*ng_per_g*GEOS_Chem_factor/(R*T_dn/P_dn)  #this is per /m3 ambient so for STP must mult by vol_amb/vol_stp
				
				BC_conc_ngm3_lower_limit = min(BC_conc_ngm3_up,BC_conc_ngm3_dn,BC_conc_ngm3)
				BC_conc_ngm3_upper_limit = max(BC_conc_ngm3_up,BC_conc_ngm3_dn,BC_conc_ngm3)
				pos_y_err = BC_conc_ngm3_upper_limit - BC_conc_ngm3
				neg_y_err = BC_conc_ngm3 - BC_conc_ngm3_lower_limit
				mean_rel_err = ((pos_y_err+neg_y_err)/2)/BC_conc_ngm3
				
				#FR data
				if date >= datetime.strptime('20090628', '%Y%m%d') and date <= datetime.strptime('20090816', '%Y%m%d'):
					GC_24h_FR.append([BC_conc_ngm3,mean_rel_err])
				if date >= datetime.strptime('20100610', '%Y%m%d') and date <= datetime.strptime('20100727', '%Y%m%d'):
					GC_24h_FR.append([BC_conc_ngm3,mean_rel_err])
				if date >= datetime.strptime('20120405', '%Y%m%d') and date <= datetime.strptime('20120531', '%Y%m%d'):
					GC_24h_FR.append([BC_conc_ngm3,mean_rel_err])
					
				#BB data
				if (date >= datetime.strptime('2009/07/27', '%Y/%m/%d') and date < datetime.strptime('2009/08/08', '%Y/%m/%d')) or date == datetime.strptime('2010/07/26', '%Y/%m/%d') or date == datetime.strptime('2010/07/27', '%Y/%m/%d'):
					GC_24h_BB.append([BC_conc_ngm3,mean_rel_err])


GC_6h_NPac = [] 
GC_6h_SPac = [] 
GC_6h_Cont = [] 
GC_6h_LRT  = [] 
GC_6h_GBPS = [] 	
GC_6h_BB = []	
GC_6h_all_non_BB = []			


#query to add 6h GC mass ocnc data
add_6h_data = ('INSERT INTO whi_gc_v9_6h_mass_concs'
              '(UNIX_UTC_6h_midtime,6h_midtime_string,cluster,GC_v9_default_mass_conc,GC_v9_default_rel_err)'
              'VALUES (%(UNIX_ts)s,%(string_ts)s,%(cluster)s,%(GC_mass_conc)s,%(GC_rel_err)s)'
			  )



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
			
				###get data for levels above and below curent
				T_up = float(Templine[level_up]) # in K
				P_up = float(Pressureline[level_up])*100 #original data in hPa, this converts to Pa
				BC_conc_ppb_up = float(BCline[level_up]) # in molBC/molAIR 
				volume_ambient_up = (R*T_up)/(P_up)
				volume_STP_up = volume_ambient_up*(P_up/101325)*(273/T_up)
				STP_correction_factor_up =  volume_ambient_up/volume_STP_up
				BC_conc_ngm3_up = STP_correction_factor_up*BC_conc_ppb_up*molar_mass_BC*ng_per_g*GEOS_Chem_factor/(R*T_up/P_up)  #this is per /m3 ambient so for STP must mult by vol_amb/vol_stp
				
				T_dn = float(Templine[level_dn]) # in K
				P_dn = float(Pressureline[level_dn])*100 #original data in hPa, this converts to Pa
				BC_conc_ppb_dn = float(BCline[level_dn]) # in molBC/molAIR 		
				volume_ambient_dn = (R*T_dn)/(P_dn)
				volume_STP_dn = volume_ambient_dn*(P_dn/101325)*(273/T_dn)
				STP_correction_factor_dn =  volume_ambient_dn/volume_STP_dn
				BC_conc_ngm3_dn = STP_correction_factor_dn*BC_conc_ppb_dn*molar_mass_BC*ng_per_g*GEOS_Chem_factor/(R*T_dn/P_dn)  #this is per /m3 ambient so for STP must mult by vol_amb/vol_stp
				
				BC_conc_ngm3_lower_limit = min(BC_conc_ngm3_up,BC_conc_ngm3_dn,BC_conc_ngm3)
				BC_conc_ngm3_upper_limit = max(BC_conc_ngm3_up,BC_conc_ngm3_dn,BC_conc_ngm3)
				pos_y_err = BC_conc_ngm3_upper_limit - BC_conc_ngm3
				neg_y_err = BC_conc_ngm3 - BC_conc_ngm3_lower_limit
				mean_rel_err = ((pos_y_err+neg_y_err)/2)/BC_conc_ngm3
			
							
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
						GC_6h_BB.append([BC_conc_ngm3,mean_rel_err])
						continue
						
					if cluslist_current_cluster_no == 9:
						GC_6h_GBPS.append([BC_conc_ngm3,mean_rel_err])
						GC_6h_all_non_BB.append([BC_conc_ngm3,mean_rel_err])
						GC_cluster = 'GBPS'
							
					if cluslist_current_cluster_no == 4:
						GC_6h_Cont.append([BC_conc_ngm3,mean_rel_err])
						GC_6h_all_non_BB.append([BC_conc_ngm3,mean_rel_err])
						GC_cluster = 'Cont'
						
					if cluslist_current_cluster_no in [6,8]:
						GC_6h_SPac.append([BC_conc_ngm3,mean_rel_err])
						GC_6h_all_non_BB.append([BC_conc_ngm3,mean_rel_err])
						GC_cluster = 'SPac'
						
					if cluslist_current_cluster_no in [2,7]:
						GC_6h_LRT.append([BC_conc_ngm3,mean_rel_err])
						GC_6h_all_non_BB.append([BC_conc_ngm3,mean_rel_err])
						GC_cluster = 'LRT'
						
					if cluslist_current_cluster_no in [1,3,5,10]:
						GC_6h_NPac.append([BC_conc_ngm3,mean_rel_err])
						GC_6h_all_non_BB.append([BC_conc_ngm3,mean_rel_err])
						GC_cluster = 'NPac'
					
					period_midtime = datetime(date.year, date.month, date.day, 13, 0, 0)
					
					
					BC_6h_data = {
					'UNIX_ts':float(calendar.timegm(period_midtime.utctimetuple())),
					'string_ts':datetime.strftime(period_midtime,'%Y%m%d %H:%M:%S'),
					'cluster':GC_cluster,
					'GC_mass_conc':BC_conc_ngm3,
					'GC_rel_err': mean_rel_err,
					}
					
					cursor.execute('DELETE FROM whi_gc_v9_6h_mass_concs WHERE UNIX_UTC_6h_midtime = %s and 6h_midtime_string = %s',(BC_6h_data['UNIX_ts'],BC_6h_data['string_ts']))
					cnx.commit()
					cursor.execute(add_6h_data, BC_6h_data)
						
						
				
			
#print out percentile data and uncertainties
stats_SP2 = {
'SP2_24h_FR':[SP2_24h_FR],
'SP2_24h_BB':[SP2_24h_BB],
'SP2_6h_NPac':[SP2_6h_NPac],
'SP2_6h_SPac':[SP2_6h_SPac],
'SP2_6h_Cont':[SP2_6h_Cont],
'SP2_6h_LRT':[SP2_6h_LRT],
'SP2_6h_GBPS':[SP2_6h_GBPS],
'SP2_6h_BB':[SP2_6h_BB],
'SP2_6h_all_non_BB':[SP2_6h_all_non_BB],
}

file_list = []

print 'SP2'
for key, value in stats_SP2.iteritems():
	mass_concs = [row[0] for row in value[0]]
	mass_concs_rel_errs = [row[1] for row in value[0]]
	print key,'no. of samples: ', len(mass_concs)
	print key,'mass concs', np.percentile(mass_concs, 10),np.percentile(mass_concs, 50), np.percentile(mass_concs, 90), np.mean(mass_concs) 
	print key,'errs',np.percentile(mass_concs_rel_errs, 50), np.mean(mass_concs_rel_errs)	
	stats_SP2[key].append(np.percentile(mass_concs, 50))
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

stats_GC = {
'GC_24h_FR':[GC_24h_FR],
'GC_24h_BB':[GC_24h_BB],
'GC_6h_NPac':[GC_6h_NPac],
'GC_6h_SPac':[GC_6h_SPac],
'GC_6h_Cont':[GC_6h_Cont],
'GC_6h_LRT':[GC_6h_LRT],
'GC_6h_GBPS':[GC_6h_GBPS],
'GC_6h_BB':[GC_6h_BB],
'GC_6h_all_non_BB':[GC_6h_all_non_BB],
}
	
	
print 'GC'
for key, value in stats_GC.iteritems():
	mass_concs = [row[0] for row in value[0]]
	mass_concs_rel_errs = [row[1] for row in value[0]]
	print key,'mass concs', np.percentile(mass_concs, 10),np.percentile(mass_concs, 50), np.percentile(mass_concs, 90), np.mean(mass_concs) 
	print key,'rel err', np.mean(mass_concs_rel_errs)	
	stats_GC[key].append(np.percentile(mass_concs, 50))




###################plotting
SP2_6h_NPac_m = [row[0] for row in SP2_6h_NPac]
SP2_6h_SPac_m = [row[0] for row in SP2_6h_SPac]
SP2_6h_Cont_m = [row[0] for row in SP2_6h_Cont]
SP2_6h_LRT_m =  [row[0] for row in SP2_6h_LRT]
SP2_6h_GBPS_m = [row[0] for row in SP2_6h_GBPS]
SP2_6h_BB_m = [row[0] for row in SP2_6h_BB]
SP2_6h_all_non_BB_m = [row[0] for row in SP2_6h_all_non_BB]

SP2_24h_FR_m = [row[0] for row in SP2_24h_FR]
SP2_24h_BB_m = [row[0] for row in SP2_24h_BB]

GC_6h_NPac_m = [row[0] for row in GC_6h_NPac]
GC_6h_SPac_m = [row[0] for row in GC_6h_SPac]
GC_6h_Cont_m = [row[0] for row in GC_6h_Cont]
GC_6h_LRT_m =  [row[0] for row in GC_6h_LRT]
GC_6h_GBPS_m = [row[0] for row in GC_6h_GBPS]
GC_6h_BB_m = [row[0] for row in GC_6h_BB]
GC_6h_all_non_BB_m = [row[0] for row in GC_6h_all_non_BB]

GC_24h_FR_m = [row[0] for row in GC_24h_FR]
GC_24h_BB_m = [row[0] for row in GC_24h_BB]

fig = plt.figure(figsize=(14, 6))

bin_number = 22
FT_UL = 280
bin_range = (0,FT_UL)
incr = 100

ax11 = plt.subplot2grid((2,6), (0,0), colspan=1,)
ax1 =  plt.subplot2grid((2,6), (0,1), colspan=1, sharey=ax11)
ax2 =  plt.subplot2grid((2,6), (0,2), colspan=1, sharey=ax11)
ax3 =  plt.subplot2grid((2,6), (0,3), colspan=1, sharey=ax11)
ax4 =  plt.subplot2grid((2,6), (0,4), colspan=1, sharey=ax11)
ax5 =  plt.subplot2grid((2,6), (0,5), colspan=1, sharey=ax11)
                           
ax12 = plt.subplot2grid((2,6), (1,0), colspan=1, )
ax6 =  plt.subplot2grid((2,6), (1,1), colspan=1, sharey=ax12)
ax7 =  plt.subplot2grid((2,6), (1,2), colspan=1, sharey=ax12)
ax8 =  plt.subplot2grid((2,6), (1,3), colspan=1, sharey=ax12)
ax9 =  plt.subplot2grid((2,6), (1,4), colspan=1, sharey=ax12)
ax10 = plt.subplot2grid((2,6), (1,5), colspan=1, sharey=ax12)

#SP2
ax1.hist(SP2_6h_NPac_m,bins = bin_number, range = bin_range)
ax1.xaxis.set_visible(True)
ax1.yaxis.set_visible(False)
ax1.text(0.25, 0.9,'N. Pacific', transform=ax1.transAxes)
#ax1.set_ylim(0,40)
ax1.xaxis.tick_top()
ax1.xaxis.set_label_position('top') 
ax1.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax1.axvline(stats_SP2['SP2_6h_NPac'][1], color= 'black', linestyle = '--')


ax2.hist(SP2_6h_SPac_m,bins = bin_number, range = bin_range)
ax2.xaxis.set_visible(True)
ax2.yaxis.set_visible(False)
ax2.text(0.25, 0.9,'S. Pacific', transform=ax2.transAxes)
ax2.xaxis.tick_top()
ax2.xaxis.set_label_position('top') 
ax2.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax2.axvline(stats_SP2['SP2_6h_SPac'][1], color= 'black', linestyle = '--')


ax3.hist(SP2_6h_GBPS_m,bins = bin_number, range = bin_range)
ax3.xaxis.set_visible(True)
ax3.yaxis.set_visible(False)
ax3.text(0.2, 0.82,'Georgia Basin/\nPuget Sound', transform=ax3.transAxes)
ax3.xaxis.tick_top()
ax3.xaxis.set_label_position('top') 
ax3.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax3.axvline(stats_SP2['SP2_6h_GBPS'][1], color= 'black', linestyle = '--')

ax4.hist(SP2_6h_LRT_m,bins = bin_number, range = bin_range)
ax4.xaxis.set_visible(True)
ax4.yaxis.set_visible(False)
ax4.text(0.2, 0.9,'W. Pacific/Asia', transform=ax4.transAxes)
ax4.xaxis.tick_top()
ax4.xaxis.set_label_position('top') 
ax4.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax4.axvline(stats_SP2['SP2_6h_LRT'][1], color= 'black', linestyle = '--')


ax5.hist(SP2_6h_Cont_m,bins = bin_number, range = bin_range)
ax5.xaxis.set_visible(True)
ax5.yaxis.set_visible(False)
ax5.text(0.25, 0.9,'N. Canada', transform=ax5.transAxes)
ax5.xaxis.tick_top()
ax5.xaxis.set_label_position('top')
ax5.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax5.axvline(stats_SP2['SP2_6h_Cont'][1], color= 'black', linestyle = '--')

ax11.hist(SP2_6h_all_non_BB_m,bins = bin_number, range = bin_range)
ax11.xaxis.set_visible(True)
ax11.yaxis.set_visible(True)
ax11.set_ylabel('frequency - Measurements')
ax11.text(0.4, 0.9,'All Data', transform=ax11.transAxes)
ax11.xaxis.tick_top()
ax11.xaxis.set_label_position('top')
ax11.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax11.axvline(stats_SP2['SP2_6h_Cont'][1], color= 'black', linestyle = '--')

#GC
ax6.hist(GC_6h_NPac_m,bins = bin_number, range = bin_range, color = 'green')
ax6.xaxis.set_visible(True)
ax6.yaxis.set_visible(False)
ax6.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax6.axvline(stats_GC['GC_6h_NPac'][1], color= 'black', linestyle = '--')

ax7.hist(GC_6h_SPac_m,bins = bin_number, range = bin_range, color = 'green')
ax7.xaxis.set_visible(True)
ax7.yaxis.set_visible(False)
ax7.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax7.axvline(stats_GC['GC_6h_SPac'][1], color= 'black', linestyle = '--')

ax8.hist(GC_6h_GBPS_m,bins = bin_number, range = bin_range, color = 'green')
ax8.xaxis.set_visible(True)
ax8.yaxis.set_visible(False)
ax8.set_xlabel('6h rBC mass concentration (ng/m3 - STP)')
ax8.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax8.axvline(stats_GC['GC_6h_GBPS'][1], color= 'black', linestyle = '--')

ax9.hist(GC_6h_LRT_m,bins = bin_number, range = bin_range, color = 'green')
ax9.xaxis.set_visible(True)
ax9.yaxis.set_visible(False)
ax9.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax9.axvline(stats_GC['GC_6h_LRT'][1], color= 'black', linestyle = '--')

ax10.hist(GC_6h_Cont_m,bins = bin_number, range = bin_range, color = 'green')
ax10.xaxis.set_visible(True)
ax10.yaxis.set_visible(False)
ax10.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax10.axvline(stats_GC['GC_6h_Cont'][1], color= 'black', linestyle = '--')

ax12.hist(GC_6h_all_non_BB_m,bins = bin_number, range = bin_range, color = 'green')
ax12.xaxis.set_visible(True)
ax12.yaxis.set_visible(True)
ax12.set_ylabel('frequency - GEOS-Chem')
ax12.xaxis.set_ticks(np.arange(0, FT_UL, incr))
ax12.axvline(stats_GC['GC_6h_BB'][1], color= 'black', linestyle = '--')

plt.subplots_adjust(hspace=0.0)
plt.subplots_adjust(wspace=0.0)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
plt.savefig('histograms -clustered GEOS-Chem and measurements - 6h FT.png',bbox_inches='tight')

plt.show()
sys.exit()
	
###################plotting 2
fig = plt.figure(figsize=(10,8))

bin_number_FR = 30
UL_FR = 360
bin_range_FR = (0,UL_FR)

bin_number_BB = 26
UL_BB = 610
bin_range_BB = (0,UL_BB)

ax1 = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2 = plt.subplot2grid((2,2), (0,1), colspan=1, sharey=ax1)

						
ax6 = plt.subplot2grid((2,2), (1,0), colspan=1)
ax7 = plt.subplot2grid((2,2), (1,1), colspan=1, sharey=ax6)



#SP2
ax1.hist(SP2_24h_FR_m,bins = bin_number_FR, range = bin_range_FR)
ax1.xaxis.set_visible(True)
ax1.yaxis.set_visible(True)
ax1.set_ylabel('frequency - Measurements')
ax1.text(0.25, 0.80,'Full Record \n(not including BB periods)', transform=ax1.transAxes)
#ax1.set_ylim(0,40)
ax1.xaxis.tick_top()
ax1.xaxis.set_label_position('top') 
ax1.xaxis.set_ticks(np.arange(0, UL_FR, 100))
ax1.axvline(stats_SP2['SP2_24h_FR'][1], color= 'black', linestyle = '--')



ax2.hist(SP2_24h_BB_m,bins = bin_number_BB, range = bin_range_BB)
ax2.xaxis.set_visible(True)
ax2.yaxis.set_visible(False)
ax2.text(0.25, 0.88,'Biomass Burning Periods', transform=ax2.transAxes)
ax2.xaxis.tick_top()
ax2.xaxis.set_label_position('top') 
ax2.xaxis.set_ticks(np.arange(0, UL_BB, 100))
ax2.axvline(stats_SP2['SP2_24h_BB'][1], color= 'black', linestyle = '--')

#GC
ax6.hist(GC_24h_FR_m,bins = bin_number_FR, range = bin_range_FR, color = 'green')
ax6.xaxis.set_visible(True)
ax6.yaxis.set_visible(True)
ax6.set_ylabel('frequency - GEOS-Chem')
ax6.xaxis.set_ticks(np.arange(0, UL_FR, 100))
ax6.axvline(stats_GC['GC_24h_FR'][1], color= 'black', linestyle = '--')


ax7.hist(GC_24h_BB_m,bins = bin_number_BB, range = bin_range_BB, color = 'green')
ax7.xaxis.set_visible(True)
ax7.yaxis.set_visible(False)
ax7.xaxis.set_ticks(np.arange(0, UL_BB, 100))
ax7.axvline(stats_GC['GC_24h_BB'][1], color= 'black', linestyle = '--')

plt.figtext(0.35,0.06, '24h rBC mass concentration (ng/m3 - STP)')

plt.subplots_adjust(hspace=0.07)
plt.subplots_adjust(wspace=0.07)

plt.savefig('histograms - GEOS-Chem and measurements - BB and FR(lessBB) - 24h.png')#,bbox_inches='tight')

plt.show()

###################plotting 3
fig = plt.figure(figsize=(6,8))

bin_number_all_FT = 30
UL_all_FT = 300
bin_range_all_FT = (0,UL_all_FT)

ax1 = plt.subplot2grid((2,1), (0,0), colspan=1)				
ax2 = plt.subplot2grid((2,1), (1,0), colspan=1)




#SP2
ax1.hist(SP2_6h_all_non_BB_m,bins = bin_number_all_FT, range = bin_range_all_FT)
ax1.xaxis.set_visible(True)
ax1.yaxis.set_visible(True)
ax1.set_ylabel('frequency - Measurements')
#ax1.text(0.25, 0.80,'All nighttime measurements \n(not including biomass burning periods)', transform=ax1.transAxes)
#ax1.set_ylim(0,40)
ax1.xaxis.tick_top()
ax1.xaxis.set_label_position('top') 
ax1.xaxis.set_ticks(np.arange(0, UL_all_FT, 50))
ax1.axvline(stats_SP2['SP2_6h_all_non_BB'][1], color= 'black', linestyle = '--')


#GC
ax2.hist(GC_6h_all_non_BB_m,bins = bin_number_all_FT, range = bin_range_all_FT, color = 'green')
ax2.xaxis.set_visible(True)
ax2.yaxis.set_visible(True)
ax2.set_ylabel('frequency - GEOS-Chem')
ax2.xaxis.set_ticks(np.arange(0, UL_FR, 50))
ax2.axvline(stats_GC['GC_6h_all_non_BB'][1], color= 'black', linestyle = '--')
ax2.set_xlabel('6h rBC mass concentration (ng/m3 - STP)')

#plt.figtext(0.35,0.06, '6h rBC mass concentration (ng/m3 - STP)')

plt.subplots_adjust(hspace=0.07)
plt.subplots_adjust(wspace=0.07)

plt.savefig('histograms - GEOS-Chem and measurements - all non-BB FT - 6h.png',bbox_inches='tight')

plt.show()


cnx.close()
