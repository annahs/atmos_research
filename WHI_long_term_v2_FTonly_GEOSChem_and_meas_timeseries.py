import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy

timezone = -8
calib_stability_uncertainty = 0.1

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
	




#6h rBC-meas avgs (FT data)
SP2_6h_NPac = [] 
SP2_6h_SPac = [] 
SP2_6h_Cont = [] 
SP2_6h_LRT  = [] 
SP2_6h_GBPS = [] 
SP2_6h_BB = []
all_6h_SP2_data = []

#6h avgd data	
for date, mass_data in rBC_FT_data_cluster_NPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_abs_err = np.mean(mass_concs_abs_err)
	SP2_6h_NPac.append([date,date_mean,date_mean_abs_err])
	all_6h_SP2_data.append([date,date_mean,date_mean_abs_err])
	
for date, mass_data in rBC_FT_data_cluster_SPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_abs_err = np.mean(mass_concs_abs_err)	
	SP2_6h_SPac.append([date,date_mean,date_mean_abs_err])
	all_6h_SP2_data.append([date,date_mean,date_mean_abs_err])
	
for date, mass_data in rBC_FT_data_cluster_Cont.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_abs_err = np.mean(mass_concs_abs_err)
	SP2_6h_Cont.append([date,date_mean,date_mean_abs_err])
	all_6h_SP2_data.append([date,date_mean,date_mean_abs_err])

for date, mass_data in rBC_FT_data_cluster_LRT.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_abs_err = np.mean(mass_concs_abs_err)
	SP2_6h_LRT.append([date,date_mean,date_mean_abs_err])
	all_6h_SP2_data.append([date,date_mean,date_mean_abs_err])

for date, mass_data in rBC_FT_data_cluster_GBPS.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_abs_err = np.mean(mass_concs_abs_err)
	SP2_6h_GBPS.append([date,date_mean,date_mean_abs_err])	
	all_6h_SP2_data.append([date,date_mean,date_mean_abs_err])	
	
for date, mass_data in rBC_FT_data_cluster_BB.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_abs_err = np.mean(mass_concs_abs_err)
	SP2_6h_BB.append([date,date_mean,date_mean_abs_err])	

##save data to file
sorted_6h_SP2_data = sorted(all_6h_SP2_data)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
file = open('WHI_SP2_6h_rBC_mass_concs.txt', 'w')
file.write('midpoint_date_and_time(PST)' + '\t' +  'rBC_mass_conc_ng/m3(STP)' + '\t' + 'mass_conc_absolute_err' + '\n')
for row in sorted_6h_SP2_data:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
file.close()


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


GC2009_BC_concs_d = {} 
GC2010_BC_concs_d = {} 
GC2012_BC_concs_d = {} 
	
GC2009_BC_concs = [] 
GC2010_BC_concs = [] 
GC2012_BC_concs = [] 
					

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

			
				#if in a BB time, #do not go on to put this data into a dictionary
				if (fire_time1[0] <= date <= fire_time1[1]) or (fire_time2[0] <= date <= fire_time2[1]):
					continue 
				
				if date > datetime.strptime('20120531', '%Y%m%d'):
					break
                
				if date >= datetime.strptime('20090628', '%Y%m%d') and date <= datetime.strptime('20090816', '%Y%m%d'):					
					GC2009_BC_concs_d[date] = [BC_conc_ngm3,neg_y_err,pos_y_err]
				if date >= datetime.strptime('20100610', '%Y%m%d') and date <= datetime.strptime('20100727', '%Y%m%d'):
					GC2010_BC_concs_d[date] = [BC_conc_ngm3,neg_y_err,pos_y_err]
				if date >= datetime.strptime('20120405', '%Y%m%d') and date <= datetime.strptime('20120531', '%Y%m%d'):
					GC2012_BC_concs_d[date] = [BC_conc_ngm3,neg_y_err,pos_y_err]


#fill in blanks days for GC with nans		
working_date = datetime.strptime('20090628', '%Y%m%d')
end_date = datetime.strptime('20090816', '%Y%m%d')
while working_date <= end_date:
	if working_date not in GC2009_BC_concs_d:
		GC2009_BC_concs_d[working_date] =  [np.nan,np.nan,np.nan]
	working_date = working_date + timedelta(days=1)


working_date = datetime.strptime('20100610', '%Y%m%d')
end_date = datetime.strptime('20100726', '%Y%m%d')
while working_date <= end_date:
	if working_date not in GC2010_BC_concs_d:
		GC2010_BC_concs_d[working_date] =  [np.nan,np.nan,np.nan]
	working_date = working_date + timedelta(days=1)


working_date = datetime.strptime('20120405', '%Y%m%d')
end_date = datetime.strptime('20120531', '%Y%m%d')
while working_date <= end_date:
	if working_date not in GC2012_BC_concs_d:
		GC2012_BC_concs_d[working_date] =  [np.nan,np.nan,np.nan]
	working_date = working_date + timedelta(days=1)
	

GC2009_BC_concs = [] 
GC2010_BC_concs = [] 
GC2012_BC_concs = [] 

for date, mass_data in GC2009_BC_concs_d.iteritems():
	mass_conc = mass_data[0]
	neg_yerr = mass_data[1]
	pos_yerr = mass_data[2]
	GC_datetime = datetime(date.year,date.month, date.day, 5)
	GC2009_BC_concs.append([GC_datetime,mass_conc, neg_yerr,pos_yerr])
for date, mass_data in GC2010_BC_concs_d.iteritems():
	mass_conc = mass_data[0]
	neg_yerr = mass_data[1]
	pos_yerr = mass_data[2]
	GC_datetime = datetime(date.year,date.month, date.day, 5)
	GC2010_BC_concs.append([GC_datetime,mass_conc, neg_yerr,pos_yerr])
for date, mass_data in GC2012_BC_concs_d.iteritems():
	mass_conc = mass_data[0]
	neg_yerr = mass_data[1]
	pos_yerr = mass_data[2]
	GC_datetime = datetime(date.year,date.month, date.day, 5)
	GC2012_BC_concs.append([GC_datetime,mass_conc, neg_yerr,pos_yerr])
	
GC2009_BC_concs.sort()
GC2010_BC_concs.sort()			
GC2012_BC_concs.sort()



#get ratios for meas/GC

ratios_cluster_NPac = []
ratios_cluster_SPac = []
ratios_cluster_Cont = []
ratios_cluster_LRT = [] 
ratios_cluster_GBPS = []
ratios_cluster_BB = []


for row in SP2_6h_SPac:
	row_datetime = row[0]
	if row_datetime.hour  == 5:
		date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		line_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day,row_datetime.hour)
		mean_mass_conc = row[1]
		mean_abs_err = row[2]
		mean_rel_err = mean_abs_err/mean_mass_conc
		
		if date in GC2009_BC_concs_d:
			GC_mass_conc = GC2009_BC_concs_d[date][0]
			neg_yerr = GC2009_BC_concs_d[date][1]
			pos_yerr = GC2009_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_SPac.append(newline)

		if date in GC2010_BC_concs_d:
			GC_mass_conc = GC2010_BC_concs_d[date][0]
			neg_yerr = GC2010_BC_concs_d[date][1]
			pos_yerr = GC2010_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_SPac.append(newline)
			
		if date in GC2012_BC_concs_d:
			GC_mass_conc = GC2012_BC_concs_d[date][0]
			neg_yerr = GC2012_BC_concs_d[date][1]
			pos_yerr = GC2012_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_SPac.append(newline)

for row in SP2_6h_NPac:
	row_datetime = row[0]
	if row_datetime.hour   == 5:
		date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		line_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day,row_datetime.hour)
		mean_mass_conc = row[1]
		mean_abs_err = row[2]
		mean_rel_err = mean_abs_err/mean_mass_conc
		
		if date in GC2009_BC_concs_d:
			GC_mass_conc = GC2009_BC_concs_d[date][0]
			neg_yerr = GC2009_BC_concs_d[date][1]
			pos_yerr = GC2009_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_NPac.append(newline)

		if date in GC2010_BC_concs_d:
			GC_mass_conc = GC2010_BC_concs_d[date][0]
			neg_yerr = GC2010_BC_concs_d[date][1]
			pos_yerr = GC2010_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_NPac.append(newline)
			
		if date in GC2012_BC_concs_d:
			GC_mass_conc = GC2012_BC_concs_d[date][0]
			neg_yerr = GC2012_BC_concs_d[date][1]
			pos_yerr = GC2012_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_NPac.append(newline)
			
for row in SP2_6h_Cont:
	row_datetime = row[0]
	if row_datetime.hour   == 5:
		date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		line_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day,row_datetime.hour)
		mean_mass_conc = row[1]
		mean_abs_err = row[2]
		mean_rel_err = mean_abs_err/mean_mass_conc
		
		if date in GC2009_BC_concs_d:
			GC_mass_conc = GC2009_BC_concs_d[date][0]
			neg_yerr = GC2009_BC_concs_d[date][1]
			pos_yerr = GC2009_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_Cont.append(newline)

		if date in GC2010_BC_concs_d:
			GC_mass_conc = GC2010_BC_concs_d[date][0]
			neg_yerr = GC2010_BC_concs_d[date][1]
			pos_yerr = GC2010_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_Cont.append(newline)
			
		if date in GC2012_BC_concs_d:
			GC_mass_conc = GC2012_BC_concs_d[date][0]
			neg_yerr = GC2012_BC_concs_d[date][1]
			pos_yerr = GC2012_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_Cont.append(newline)
		
for row in SP2_6h_GBPS:
	row_datetime = row[0]
	if row_datetime.hour   == 5:
		date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		line_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day,row_datetime.hour)
		mean_mass_conc = row[1]
		mean_abs_err = row[2]
		mean_rel_err = mean_abs_err/mean_mass_conc
		
		if date in GC2009_BC_concs_d:
			GC_mass_conc = GC2009_BC_concs_d[date][0]
			neg_yerr = GC2009_BC_concs_d[date][1]
			pos_yerr = GC2009_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_GBPS.append(newline)

		if date in GC2010_BC_concs_d:
			GC_mass_conc = GC2010_BC_concs_d[date][0]
			neg_yerr = GC2010_BC_concs_d[date][1]
			pos_yerr = GC2010_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_GBPS.append(newline)
			
		if date in GC2012_BC_concs_d:
			GC_mass_conc = GC2012_BC_concs_d[date][0]
			neg_yerr = GC2012_BC_concs_d[date][1]
			pos_yerr = GC2012_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_GBPS.append(newline)
		
for row in SP2_6h_LRT:
	row_datetime = row[0]
	if row_datetime.hour  == 5:
		date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		line_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day,row_datetime.hour)
		mean_mass_conc = row[1]
		mean_abs_err = row[2]
		mean_rel_err = mean_abs_err/mean_mass_conc
		
		if date in GC2009_BC_concs_d:
			GC_mass_conc = GC2009_BC_concs_d[date][0]
			neg_yerr = GC2009_BC_concs_d[date][1]
			pos_yerr = GC2009_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_LRT.append(newline)

		if date in GC2010_BC_concs_d:
			GC_mass_conc = GC2010_BC_concs_d[date][0]
			neg_yerr = GC2010_BC_concs_d[date][1]
			pos_yerr = GC2010_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_LRT.append(newline)
			
		if date in GC2012_BC_concs_d:
			GC_mass_conc = GC2012_BC_concs_d[date][0]
			neg_yerr = GC2012_BC_concs_d[date][1]
			pos_yerr = GC2012_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_LRT.append(newline)
		
		
for row in SP2_6h_BB:
	row_datetime = row[0]
	if row_datetime.hour  == 5:
		date = datetime(row_datetime.year, row_datetime.month, row_datetime.day)
		line_date = datetime(row_datetime.year, row_datetime.month, row_datetime.day,5)
		mean_mass_conc = row[1]
		mean_abs_err = row[2]
		mean_rel_err = mean_abs_err/mean_mass_conc
		
		if date in GC2009_BC_concs_d:
			GC_mass_conc = GC2009_BC_concs_d[date][0]
			neg_yerr = GC2009_BC_concs_d[date][1]
			pos_yerr = GC2009_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_BB.append(newline)

		if date in GC2010_BC_concs_d:
			GC_mass_conc = GC2010_BC_concs_d[date][0]
			neg_yerr = GC2010_BC_concs_d[date][1]
			pos_yerr = GC2010_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_BB.append(newline)
			
		if date in GC2012_BC_concs_d:
			GC_mass_conc = GC2012_BC_concs_d[date][0]
			neg_yerr = GC2012_BC_concs_d[date][1]
			pos_yerr = GC2012_BC_concs_d[date][2]
			GC_rel_err = (pos_yerr+neg_yerr/2)/GC_mass_conc
			ratio = GC_mass_conc/mean_mass_conc
			newline = [line_date, ratio, ratio*(mean_rel_err+GC_rel_err)]
			ratios_cluster_BB.append(newline)
		
		

			
			
###################plotting

SP2_6h_NPac_date = [dates.date2num(row[0]) for row in SP2_6h_NPac] 
SP2_6h_NPac_mass_conc = [row[1] for row in SP2_6h_NPac]
SP2_6h_NPac_abs_err = [row[2] for row in SP2_6h_NPac]

SP2_6h_SPac_date = [dates.date2num(row[0]) for row in SP2_6h_SPac]
SP2_6h_SPac_mass_conc = [row[1] for row in SP2_6h_SPac]
SP2_6h_SPac_abs_err = [row[2] for row in SP2_6h_SPac]

SP2_6h_Cont_date = [dates.date2num(row[0]) for row in SP2_6h_Cont]
SP2_6h_Cont_mass_conc = [row[1] for row in SP2_6h_Cont]
SP2_6h_Cont_abs_err = [row[2] for row in SP2_6h_Cont]

SP2_6h_LRT_date =  [dates.date2num(row[0]) for row in SP2_6h_LRT]
SP2_6h_LRT_mass_conc = [row[1] for row in SP2_6h_LRT]
SP2_6h_LRT_abs_err = [row[2] for row in SP2_6h_LRT]

SP2_6h_GBPS_date = [dates.date2num(row[0]) for row in SP2_6h_GBPS]
SP2_6h_GBPS_mass_conc = [row[1] for row in SP2_6h_GBPS]
SP2_6h_GBPS_abs_err = [row[2] for row in SP2_6h_GBPS]

SP2_6h_BB_date = [dates.date2num(row[0]) for row in SP2_6h_BB]
SP2_6h_BB_mass_conc = [row[1] for row in SP2_6h_BB]
SP2_6h_BB_abs_err = [row[2] for row in SP2_6h_BB]

GC_6h_2009_date = [dates.date2num(row[0]) for row in GC2009_BC_concs] 
GC_6h_2009_mass_conc = [row[1] for row in GC2009_BC_concs]
GC_6h_2009_neg_err = [row[2] for row in GC2009_BC_concs]
GC_6h_2009_pos_err = [row[3] for row in GC2009_BC_concs]

GC_6h_2010_date = [dates.date2num(row[0]) for row in GC2010_BC_concs] 
GC_6h_2010_mass_conc = [row[1] for row in GC2010_BC_concs]
GC_6h_2010_neg_err = [row[2] for row in GC2010_BC_concs]
GC_6h_2010_pos_err = [row[3] for row in GC2010_BC_concs]

GC_6h_2012_date = [dates.date2num(row[0]) for row in GC2012_BC_concs] 
GC_6h_2012_mass_conc = [row[1] for row in GC2012_BC_concs]
GC_6h_2012_neg_err = [row[2] for row in GC2012_BC_concs]
GC_6h_2012_pos_err = [row[3] for row in GC2012_BC_concs]	

	
ratio_dates_SPac = [dates.date2num(row[0]) for row in ratios_cluster_SPac]
ratio_mass_conc_SPac = [row[1] for row in ratios_cluster_SPac] 
ratio_err_SPac = [row[2] for row in ratios_cluster_SPac]

ratio_dates_NPac = [dates.date2num(row[0]) for row in ratios_cluster_NPac]
ratio_mass_conc_NPac = [row[1] for row in ratios_cluster_NPac] 
ratio_err_NPac = [row[2] for row in ratios_cluster_NPac]

ratio_dates_Cont = [dates.date2num(row[0]) for row in ratios_cluster_Cont]
ratio_mass_conc_Cont = [row[1] for row in ratios_cluster_Cont] 
ratio_err_Cont = [row[2] for row in ratios_cluster_Cont]

ratio_dates_LRT = [dates.date2num(row[0]) for row in ratios_cluster_LRT]
ratio_mass_conc_LRT = [row[1] for row in ratios_cluster_LRT] 
ratio_err_LRT = [row[2] for row in ratios_cluster_LRT]

ratio_dates_GBPS = [dates.date2num(row[0]) for row in ratios_cluster_GBPS]
ratio_mass_conc_GBPS = [row[1] for row in ratios_cluster_GBPS] 
ratio_err_GBPS = [row[2] for row in ratios_cluster_GBPS]

ratio_dates_BB = [dates.date2num(row[0]) for row in ratios_cluster_BB]
ratio_mass_conc_BB = [row[1] for row in ratios_cluster_BB] 
ratio_err_BB = [row[2] for row in ratios_cluster_BB]
		
#fire times for plotting shaded areas
fire_span2_09s=datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span2_09f=datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span1_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')


fire_alpha = 0.25
fire_color = '#990000'			

			
###################plotting#####################


fig = plt.figure(figsize=(11.5,7.5))

hfmt = dates.DateFormatter('%b')
#hfmt = dates.DateFormatter('%m-%d')

display_month_interval = 1
max_display_conc = 340

startdate_2009 = '2009/06/25'
enddate_2009 = '2009/08/20'

startdate_2010 = '2010/05/31'
enddate_2010 = '2010/08/04'

startdate_2012 = '2012/03/29'
enddate_2012 = '2012/06/05'


ax7 =  plt.subplot2grid((4,3), (0,0), colspan=1,rowspan = 2)
ax8 =  plt.subplot2grid((4,3), (0,1), colspan=1,rowspan = 2)
ax9 =  plt.subplot2grid((4,3), (0,2), colspan=1,rowspan = 2, sharey=ax8)
										
ax10 = plt.subplot2grid((4,3), (2,0), colspan=1,rowspan = 2)
ax11 = plt.subplot2grid((4,3), (2,1), colspan=1,rowspan = 2, sharey=ax10)
ax12 = plt.subplot2grid((4,3), (2,2), colspan=1,rowspan = 2, sharey=ax10)
											
#combo

ax7.errorbar(SP2_6h_NPac_date,SP2_6h_NPac_mass_conc,yerr = SP2_6h_NPac_abs_err, color='cyan', alpha = 1, fmt = '*')
ax7.errorbar(SP2_6h_SPac_date,SP2_6h_SPac_mass_conc,yerr = SP2_6h_SPac_abs_err, color='green', alpha = 1, fmt = 'o')
ax7.errorbar(SP2_6h_Cont_date,SP2_6h_Cont_mass_conc,yerr = SP2_6h_Cont_abs_err, color='magenta', alpha = 1, fmt = '>')
ax7.errorbar(SP2_6h_LRT_date,SP2_6h_LRT_mass_conc,yerr = SP2_6h_LRT_abs_err, color='blue', alpha = 1, fmt = 's')
ax7.errorbar(SP2_6h_GBPS_date,SP2_6h_GBPS_mass_conc,yerr = SP2_6h_GBPS_abs_err, color='red', alpha = 1, fmt = '^')
#ax7.errorbar(SP2_6h_BB_date,SP2_6h_BB_mass_conc,yerr = SP2_6h_BB_abs_err, color='grey', alpha = 1, fmt = '<')
ax7.errorbar(GC_6h_2009_date,GC_6h_2009_mass_conc,yerr=[GC_6h_2009_neg_err,GC_6h_2009_pos_err], color = 'k', alpha = 1, marker = '+')
ax7.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax7.xaxis.set_visible(False)
ax7.yaxis.set_visible(True)
ax7.set_ylabel('rBC mass concentration (ng/m3 - STP)')
ax7.set_ylim(0, max_display_conc)
ax7.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax7.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)
ax7.text(0.1, 0.9,'2009', transform=ax7.transAxes)


ax8.errorbar(SP2_6h_NPac_date,SP2_6h_NPac_mass_conc,yerr = SP2_6h_NPac_abs_err, color='cyan', alpha = 1, fmt = '*', label = 'N. Pacific')
ax8.errorbar(SP2_6h_SPac_date,SP2_6h_SPac_mass_conc,yerr = SP2_6h_SPac_abs_err, color='green', alpha = 1, fmt = 'o', label = 'S. Pacific')
ax8.errorbar(SP2_6h_Cont_date,SP2_6h_Cont_mass_conc,yerr = SP2_6h_Cont_abs_err, color='magenta', alpha = 1, fmt = '>', label = 'N. Canada')
ax8.errorbar(SP2_6h_LRT_date,SP2_6h_LRT_mass_conc,yerr = SP2_6h_LRT_abs_err, color='blue', alpha = 1, fmt = 's', label = 'W. Pacific/Asia')
ax8.errorbar(SP2_6h_GBPS_date,SP2_6h_GBPS_mass_conc,yerr = SP2_6h_GBPS_abs_err, color='red', alpha = 1, fmt = '^', label = 'Georgia Basin/Puget Sound')
#ax8.errorbar(SP2_6h_BB_date,SP2_6h_BB_mass_conc,yerr = SP2_6h_BB_abs_err, color='grey', alpha = 1, fmt = '<', label = 'Biomass Burning')
ax8.errorbar(GC_6h_2010_date,GC_6h_2010_mass_conc,yerr=[GC_6h_2010_neg_err,GC_6h_2010_pos_err], color = 'k', alpha = 1, marker = '+')
ax8.xaxis.set_major_formatter(hfmt)
ax8.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax8.xaxis.set_visible(False)
ax8.yaxis.set_visible(False)
ax8.set_xlabel('month')
ax8.set_ylim(0, max_display_conc)
ax8.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax8.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax8.text(0.1, 0.9,'2010', transform=ax8.transAxes)


ax9.errorbar(SP2_6h_NPac_date,SP2_6h_NPac_mass_conc,yerr = SP2_6h_NPac_abs_err, color='cyan', alpha = 1, fmt = '*', label = 'NPac')
ax9.errorbar(SP2_6h_SPac_date,SP2_6h_SPac_mass_conc,yerr = SP2_6h_SPac_abs_err, color='green', alpha = 1, fmt = 'o', label = 'SPac')
ax9.errorbar(SP2_6h_Cont_date,SP2_6h_Cont_mass_conc,yerr = SP2_6h_Cont_abs_err, color='magenta', alpha = 1, fmt = '>', label = 'Cont')
ax9.errorbar(SP2_6h_LRT_date,SP2_6h_LRT_mass_conc,yerr = SP2_6h_LRT_abs_err, color='blue', alpha = 1, fmt = 's', label = 'LRT')
ax9.errorbar(SP2_6h_GBPS_date,SP2_6h_GBPS_mass_conc,yerr = SP2_6h_GBPS_abs_err, color='red', alpha = 1, fmt = '^', label = 'GBPS')
#ax9.errorbar(SP2_6h_BB_date,SP2_6h_BB_mass_conc,yerr = SP2_6h_BB_abs_err, color='grey', alpha = 1, fmt = '<', label = 'BB')
ax9.errorbar(GC_6h_2012_date,GC_6h_2012_mass_conc,yerr=[GC_6h_2012_neg_err,GC_6h_2012_pos_err], color = 'k', alpha = 1, marker = '+')
ax9.xaxis.set_major_formatter(hfmt)
ax9.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax9.xaxis.set_visible(False)
ax9.yaxis.set_visible(True)
ax9.yaxis.tick_right()
ax9.set_ylim(0, max_display_conc)
ax9.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax9.text(0.1, 0.9,'2012', transform=ax9.transAxes)

legend = ax8.legend(loc='upper center', bbox_to_anchor=(0.5, 1.275), ncol=3, numpoints=1)


#ratios

ax10.errorbar(ratio_dates_SPac,ratio_mass_conc_SPac,yerr = ratio_err_SPac, color='green', alpha = 1, fmt = 'o')
ax10.errorbar(ratio_dates_NPac,ratio_mass_conc_NPac,yerr = ratio_err_NPac, color='cyan', alpha = 1, fmt = '*')
ax10.errorbar(ratio_dates_Cont,ratio_mass_conc_Cont,yerr = ratio_err_Cont, color='magenta', alpha = 1, fmt = '>')
ax10.errorbar(ratio_dates_LRT,ratio_mass_conc_LRT,yerr = ratio_err_LRT, color='blue', alpha = 1, fmt = 's')
ax10.errorbar(ratio_dates_GBPS,ratio_mass_conc_GBPS,yerr = ratio_err_GBPS, color='red', alpha = 1, fmt = '^')
#ax10.errorbar(ratio_dates_BB,ratio_mass_conc_BB,yerr = ratio_err_BB, color='grey', alpha = 1, fmt = '<')
ax10.xaxis.set_major_formatter(hfmt)
ax10.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax10.xaxis.set_minor_locator(dates.DayLocator(interval = 2))
ax10.xaxis.set_visible(True)
ax10.yaxis.set_visible(True)
ax10.set_ylabel('GEOS-Chem/Measurements')
#ax10.set_ylim(0, 70)
ax10.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax10.axhline(y=1,color = 'grey', linestyle = '--')
ax10.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)
ax10.set_yscale('log')


ax11.errorbar(ratio_dates_SPac,ratio_mass_conc_SPac,yerr = ratio_err_SPac, color='green', alpha = 1, fmt = 'o')
ax11.errorbar(ratio_dates_NPac,ratio_mass_conc_NPac,yerr = ratio_err_NPac, color='cyan', alpha = 1, fmt = '*')
ax11.errorbar(ratio_dates_Cont,ratio_mass_conc_Cont,yerr = ratio_err_Cont, color='magenta', alpha = 1, fmt = '>')
ax11.errorbar(ratio_dates_LRT,ratio_mass_conc_LRT,yerr = ratio_err_LRT, color='blue', alpha = 1, fmt = 's')
ax11.errorbar(ratio_dates_GBPS,ratio_mass_conc_GBPS,yerr = ratio_err_GBPS, color='red', alpha = 1, fmt = '^')
#ax11.errorbar(ratio_dates_BB,ratio_mass_conc_BB,yerr = ratio_err_BB, color='grey', alpha = 1, fmt = '<')
ax11.xaxis.set_major_formatter(hfmt)
ax11.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax11.xaxis.set_minor_locator(dates.DayLocator(interval = 2))
ax11.xaxis.set_visible(True)
ax11.yaxis.set_visible(False)
ax11.set_xlabel('month')
ax11.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax11.axhline(y=1,color = 'grey', linestyle = '--')
ax11.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax11.set_yscale('log')

ax12.errorbar(ratio_dates_SPac,ratio_mass_conc_SPac,yerr = ratio_err_SPac, color='green', alpha = 1, fmt = 'o')
ax12.errorbar(ratio_dates_NPac,ratio_mass_conc_NPac,yerr = ratio_err_NPac, color='cyan', alpha = 1, fmt = '*')
ax12.errorbar(ratio_dates_Cont,ratio_mass_conc_Cont,yerr = ratio_err_Cont, color='magenta', alpha = 1, fmt = '>')
ax12.errorbar(ratio_dates_LRT,ratio_mass_conc_LRT,yerr = ratio_err_LRT, color='blue', alpha = 1, fmt = 's')
ax12.errorbar(ratio_dates_GBPS,ratio_mass_conc_GBPS,yerr = ratio_err_GBPS, color='red', alpha = 1, fmt = '^')
#ax12.errorbar(ratio_dates_BB,ratio_mass_conc_BB,yerr = ratio_err_BB, color='grey', alpha = 1, fmt = '<')
ax12.xaxis.set_major_formatter(hfmt)
ax12.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax12.xaxis.set_minor_locator(dates.DayLocator(interval = 2))
ax12.xaxis.set_visible(True)
ax12.yaxis.set_visible(True)
ax12.yaxis.tick_right()
#ax12.spines['top'].set_visible(False)
#ax12.xaxis.tick_bottom()
ax12.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax12.axhline(y=1,color = 'grey', linestyle = '--')
ax12.set_yscale('log')

#legend = ax12.legend(loc='upper right', shadow=False)

plt.subplots_adjust(hspace=0.08)
plt.subplots_adjust(wspace=0.05)


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
plt.savefig('timeseries - FT only GEOS-Chem v measurements.png', bbox_extra_artists=(legend,), bbox_inches='tight',dpi=600)




plt.show()