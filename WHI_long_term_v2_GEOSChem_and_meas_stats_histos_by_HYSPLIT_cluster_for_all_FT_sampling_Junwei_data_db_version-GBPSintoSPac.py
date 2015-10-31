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
import calendar
import mysql.connector


#database tables

###
filter_by_RH = True
high_RH_limit = 90

if filter_by_RH == False:
	high_RH_limit = 101
####

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

calib_stability_uncertainty = 0.1

#fire times
timezone = timedelta(hours = -8)

fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time1_UNIX_UTC_start = float(calendar.timegm((fire_time1[0]-timezone).utctimetuple()))
fire_time1_UNIX_UTC_end = float(calendar.timegm((fire_time1[1]-timezone).utctimetuple()))

fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST
fire_time2_UNIX_UTC_start = float(calendar.timegm((fire_time2[0]-timezone).utctimetuple()))
fire_time2_UNIX_UTC_end = float(calendar.timegm((fire_time2[1]-timezone).utctimetuple()))


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


##
#select data (spikes already rmoved) and exclude fire times 
SP2_data_query = ('SELECT * FROM whi_sp2_rbc_record_2009to2012_spikes_removed WHERE UNIX_GMT_ts NOT BETWEEN %(fire_time1_start)s AND %(fire_time1_end)s AND UNIX_GMT_ts NOT BETWEEN %(fire_time2_start)s AND %(fire_time2_end)s')
			

query_terms ={
'fire_time1_start':fire_time1_UNIX_UTC_start,
'fire_time1_end':fire_time1_UNIX_UTC_end,
'fire_time2_start':fire_time2_UNIX_UTC_start,
'fire_time2_end':fire_time2_UNIX_UTC_end
}		

cursor.execute(SP2_data_query,query_terms)
SP2_data = cursor.fetchall()

start_hour = 4 #PST 20000
end_hour = 16 #PST 0800

for row in SP2_data:	
	UNIX_UTC_ts = row[8]
	date_time_UTC = datetime.utcfromtimestamp(UNIX_UTC_ts)
	BC_mass_conc = row[3]
	BC_mass_conc_LL = row[4] 
	BC_mass_conc_UL = row[5] 

	#avoid high RH times
	if filter_by_RH == True:
		cursor.execute(('SELECT RH from whi_high_rh_times_2009to2012 where high_RH_start_time <= %s and high_RH_end_time > %s'),(UNIX_UTC_ts,UNIX_UTC_ts))
		RH_data = cursor.fetchall()
		if len(RH_data):
			if RH_data[0] > high_RH_limit:
				continue
		
	#use night only data
	if start_hour <= date_time_UTC.hour < end_hour:
		cursor.execute(('SELECT * from whi_ft_cluster_times_2009to2012 where cluster_start_time <= %s and cluster_end_time >= %s'),(UNIX_UTC_ts,UNIX_UTC_ts))
		cluster_data = cursor.fetchall()
		#we have a few samples from teh first day of 2009 and 2012 that are before our first cluster, so this ignores those . . 
		if len(cluster_data) == 0:
			continue
			
		cluster_midtime = datetime.strptime(cluster_data[0][4], '%Y-%m-%d %H:%M:%S')
		cluster_number = cluster_data[0][3]

		#####get abs err
		if np.isnan(BC_mass_conc_LL):
			abs_err = np.nan
		else:
			abs_err = (BC_mass_conc-BC_mass_conc_LL)
		
				
		#add data to list in cluster dictionaries (1 list per cluster time early night/late night)
		if cluster_number == 9:
			correction_factor_for_massdistr = 1./0.5411
			mass_distr_correction_error = 0.015  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]
			if cluster_midtime in rBC_FT_data_cluster_SPac:
				rBC_FT_data_cluster_SPac[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_SPac[cluster_midtime] = [row_data] 
			
		if cluster_number == 4:
			correction_factor_for_massdistr = 1./0.4028
			mass_distr_correction_error = 0.028  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_Cont:
				rBC_FT_data_cluster_Cont[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_Cont[cluster_midtime] = [row_data]
				
		if cluster_number in [6,8]:
			correction_factor_for_massdistr = 1./0.4626
			mass_distr_correction_error = 0.032  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_SPac:
				rBC_FT_data_cluster_SPac[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_SPac[cluster_midtime] = [row_data]
				
		if cluster_number in [2,7]:
			correction_factor_for_massdistr = 1./0.5280
			mass_distr_correction_error = 0.019  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_LRT:
				rBC_FT_data_cluster_LRT[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_LRT[cluster_midtime] = [row_data]
				
		if cluster_number in [1,3,5,10]:
			correction_factor_for_massdistr = 1./0.3525
			mass_distr_correction_error = 0.015  #this is the uncertainty in the firt of the mass distribution for this period. from WHI_long_term_v2_size_distr_fitting_and_plotting.py
			corrected_mass_conc = BC_mass_conc*correction_factor_for_massdistr
			row_data = [corrected_mass_conc, abs_err+(corrected_mass_conc*(mass_distr_correction_error+calib_stability_uncertainty)) ]				
			if cluster_midtime in rBC_FT_data_cluster_NPac:
				rBC_FT_data_cluster_NPac[cluster_midtime].append(row_data)
			else:
				rBC_FT_data_cluster_NPac[cluster_midtime] = [row_data]


##print data set lengths
#for cluster in [rBC_FT_data_cluster_NPac,rBC_FT_data_cluster_SPac,rBC_FT_data_cluster_Cont,rBC_FT_data_cluster_GBPS,rBC_FT_data_cluster_LRT]:				
#	print len(cluster)
#	data_pts = 0
#	for midtime in cluster:
#		data_pts = data_pts + len(cluster[midtime])
#	print data_pts
#	print '\n'
#sys.exit()

#6h rBC-meas avgs (FT data)
SP2_6h_NPac = [] 
SP2_6h_SPac = [] 
SP2_6h_Cont = [] 
SP2_6h_LRT  = [] 
SP2_6h_BB = [] 
SP2_6h_all_non_BB = []

all_dict = {}

#6h means 	
for date, mass_data in rBC_FT_data_cluster_NPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_NPac.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]
		
for date, mass_data in rBC_FT_data_cluster_SPac.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_SPac.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]
	
for date, mass_data in rBC_FT_data_cluster_Cont.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_Cont.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])

	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]
	
for date, mass_data in rBC_FT_data_cluster_LRT.iteritems():
	mass_concs = [row[0] for row in mass_data]
	mass_concs_abs_err = [row[1] for row in mass_data]
	
	date_mean = np.mean(mass_concs)
	date_mean_err = np.mean(mass_concs_abs_err)/date_mean	
	SP2_6h_LRT.append([date_mean,date_mean_err])
	SP2_6h_all_non_BB.append([date_mean,date_mean_err])
	
	if date in all_dict:
		print 'alert!',date
	else:
		all_dict[date] = [date_mean,date_mean_err]


	
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
SP2_6h_all_non_BB_m = [row[0] for row in SP2_6h_all_non_BB]
	
	
	
#########print out percentile data and uncertainties for SP2 and save to db
stats_SP2 = collections.OrderedDict([
('all',[SP2_6h_all_non_BB]),
('NPac',[SP2_6h_NPac]),
('SPac',[SP2_6h_SPac]),
('Cont',[SP2_6h_Cont]),
('LRT',[SP2_6h_LRT]),
])

add_stats = ('INSERT INTO whi_gc_and_sp2_stats_on_6h_clustered_ft_data'
              '(data_source,cluster,RH_threshold,test_scenario,10th_percentile_mass_conc,50th_percentile_mass_conc,90th_percentile_mass_conc,mean_mass_conc,rel_err)'
              'VALUES (%(source)s,%(cluster_name)s,%(RH_thresh)s,%(scenario)s,%(10)s,%(50)s,%(90)s,%(mean)s,%(rel_err)s)')


print 'SP2'
for key, value in stats_SP2.iteritems():
	mass_concs = [row[0] for row in value[0]]
	mass_concs_rel_errs = [row[1] for row in value[0]]
	print key,'no. of samples: ', len(mass_concs)
	print key,'mass concs', np.percentile(mass_concs, 10),np.percentile(mass_concs, 50), np.percentile(mass_concs, 90), np.mean(mass_concs) 
	print key,'errs', np.mean(mass_concs_rel_errs)	
	
	stats = {
	'source': 'SP2',
	'cluster_name': key,
	'RH_thresh':high_RH_limit,
	'scenario':'default',
	'10':float(np.percentile(mass_concs, 10)),
	'50':float(np.percentile(mass_concs, 50)),
	'90':float(np.percentile(mass_concs, 90)),
	'mean':float(np.mean(mass_concs)),
	'rel_err':float(np.mean(mass_concs_rel_errs))
	}
	
	cursor.execute('DELETE FROM whi_gc_and_sp2_stats_on_6h_clustered_ft_data WHERE data_source = %s and cluster = %s and RH_threshold = %s',(stats['source'],stats['cluster_name'],stats['RH_thresh']))
	cnx.commit()
	cursor.execute(add_stats, stats)
	cnx.commit()
			  
	



	
###################GEOS-Chem


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
		sampling_times.append(sampling_datetime+timedelta(hours=8))  #get into UTC




GC_data = {}

GC_runs = ['default','Vancouver_emission','wet_scavenging','no_biomass','All_together']

lat = 20 #20 corresponds to 50deg 
lon = 7 #7 corresponds to -122.5deg
level = 9 #1-47 #9 is closest to WHI avg P (WHI 95% CI = 770-793)

molar_mass_BC = 12.0107 #in g/mol
ng_per_g = 10**9
R = 8.3144621 # in m3*Pa/(K*mol)
GEOS_Chem_factor = 10**-9

i=0
#start_hour = 3
#end_hour = 15
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
			GC_UNIX_UTC_ts = calendar.timegm(GC_datetime.utctimetuple())
			
			
			#avoid high RH times
			if filter_by_RH == True:
				cursor.execute(('SELECT RH from whi_high_rh_times_2009to2012 where high_RH_start_time <= %s and high_RH_end_time > %s'),(GC_UNIX_UTC_ts,GC_UNIX_UTC_ts))
				RH_data = cursor.fetchone()
				if RH_data != None:
					if RH_data[0] > high_RH_limit:
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
					period_midtime = datetime(file_year,file_month,file_day,7)
					
				if (start_hour+6) <= file_hour < end_hour:	
					period_midtime = datetime(file_year,file_month,file_day,13)  
				
				hydrophilic_BC = hdf_file.select('IJ-AVG-$::BCPI') #3d conc data in ppbv (molBC/molAIR)
				hydrophobic_BC = hdf_file.select('IJ-AVG-$::BCPO')

				total_BC_ppbv = hydrophilic_BC[level,lat,lon] + hydrophobic_BC[level,lat,lon]
				BC_conc_ngm3 = total_BC_ppbv*molar_mass_BC*ng_per_g*GEOS_Chem_factor*(101325/(R*273))  #101325/(R*273) corrects to STP 	
				
				if period_midtime in all_dict:  #this excludes BB times already
					if period_midtime in GC_data:
						GC_data[period_midtime][i].append(BC_conc_ngm3)
					else:
						GC_data[period_midtime] = [[],[],[],[],[],'']
						GC_data[period_midtime][i].append(BC_conc_ngm3)
					
					

				hdf_file.end()
	i+=1
	
	
#assign clusters to GC data
for period_midtime in GC_data:
	period_midtime_UNIX_ts = calendar.timegm(period_midtime.utctimetuple())
	cursor.execute(('SELECT * from whi_ft_cluster_times_2009to2012 where cluster_start_time <= %s and cluster_end_time > %s'),(period_midtime_UNIX_ts,period_midtime_UNIX_ts)) #UTC
	cluster_data = cursor.fetchall()
	cluster_midtime = datetime.strptime(cluster_data[0][4], '%Y-%m-%d %H:%M:%S')
	cluster_no = cluster_data[0][3]

	if cluster_no == 4:
		cluster = 'Cont'	
		
	if cluster_no in [6,8,9]:
		cluster = 'SPac'

	if cluster_no in [2,7]:
		cluster = 'LRT'

	if cluster_no in [1,3,5,10]:
		cluster = 'NPac'
		
	if (datetime.utcfromtimestamp(fire_time1_UNIX_UTC_start) <= cluster_midtime <= datetime.utcfromtimestamp(fire_time1_UNIX_UTC_end)) or (datetime.utcfromtimestamp(fire_time2_UNIX_UTC_start) <= cluster_midtime <= datetime.utcfromtimestamp(fire_time2_UNIX_UTC_end)):
		cluster = 'BB'
	
	GC_data[period_midtime][5] = cluster		


all_data =  {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
NPac_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
SPac_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
Cont_data = {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}
LRT_data =  {'default':[],'Van':[],'wet_scav':[],'no_bb':[],'all_together':[]}

#query to add 6h mass ocnc data
add_6h_data = ('INSERT INTO whi_gc_and_sp2_6h_mass_concs'
              '(UNIX_UTC_6h_midtime,6h_midtime_string,cluster,meas_mean_mass_conc,GC_v10_default,GC_v10_Van,GC_v10_wet_scav,GC_v10_no_bb,GC_v10_all_together,RH_threshold,meas_rel_err,GC_default_rel_err,GC_Van_rel_err,GC_wet_scav_rel_err,GC_no_bb_rel_err, GC_all_together_rel_err)'
              'VALUES (%(UNIX_ts)s,%(string_ts)s,%(cluster)s,%(meas_mass_conc)s,%(GC_def)s,%(GC_Van)s,%(GC_ws)s,%(GC_nobb)s,%(GC_allch)s,%(RH_thresh)s,%(meas_err)s,%(GC_def_err)s,%(GC_Van_err)s,%(GC_ws_err)s,%(GC_nobb_err)s,%(GC_allch_err)s)'
			  )

			  
#get the means for each 6-h period
for period_midtime in GC_data:
	
	default_data = GC_data[period_midtime][0]
	Vancouver_data = GC_data[period_midtime][1]
	wet_scav_data = GC_data[period_midtime][2]
	no_biomass_data = GC_data[period_midtime][3]
	all_together_data = GC_data[period_midtime][4]
	GC_cluster = GC_data[period_midtime][5]
	
	data_6hrly = {}
	#get the default GC data for all air masses combined
	for key, data in {'default':default_data,'Van':Vancouver_data,'wet_scav':wet_scav_data,'no_bb':no_biomass_data,'all_together':all_together_data}.iteritems():
		mean = np.nanmean(data) 
		rel_err = np.std(data)/mean  
		all_data[key].append([mean,rel_err])
		data_6hrly[key] = [float(mean),float(rel_err)]
		
	
	
	if period_midtime in all_dict:
			
		BC_6h_data = {
		'UNIX_ts':float(calendar.timegm(period_midtime.utctimetuple())),
		'string_ts':datetime.strftime(period_midtime,'%Y%m%d %H:%M:%S'),
		'cluster':GC_cluster,
		'meas_mass_conc':float(all_dict[period_midtime][0]),
		'GC_def': data_6hrly['default'][0],
		'GC_Van':data_6hrly['Van'][0],
		'GC_ws':data_6hrly['wet_scav'][0],
		'GC_nobb':data_6hrly['no_bb'][0],
		'GC_allch':data_6hrly['all_together'][0],
		'RH_thresh':high_RH_limit,
		'meas_err':float(all_dict[period_midtime][1]),
		'GC_def_err':data_6hrly['default'][1],
		'GC_Van_err':data_6hrly['Van'][1],
		'GC_ws_err':data_6hrly['wet_scav'][1],
		'GC_nobb_err':data_6hrly['no_bb'][1],
		'GC_allch_err':data_6hrly['all_together'][1],
		}
		
		pprint(BC_6h_data)
		cursor.execute('DELETE FROM whi_gc_and_sp2_6h_mass_concs WHERE UNIX_UTC_6h_midtime = %s and RH_threshold = %s',(BC_6h_data['UNIX_ts'],BC_6h_data['RH_thresh']))
		cnx.commit()
		cursor.execute(add_6h_data, BC_6h_data)
			
			
	
	for cluster, data_set in  {'NPac':NPac_data,'SPac':SPac_data,'Cont':Cont_data,'LRT':LRT_data}.iteritems():
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
data_to_plot = [SP2_6h_all_non_BB_m,SP2_6h_NPac_m,SP2_6h_SPac_m,SP2_6h_Cont_m,SP2_6h_LRT_m]

for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	default_case = dataset['default']
	default_concs = [row[0] for row in default_case]
	print len(default_concs), '**'
	data_to_plot.append(default_concs)
	
for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	case_data = dataset['wet_scav']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	data_to_plot.append(concs)
	
bin_number = 22
FT_UL = 280
bin_range = (0,FT_UL)
y_lim = 60

#SP2 vs GC	
fig, axes = plt.subplots(3,5, figsize=(14, 9), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.0)
axs = axes.ravel()	
i=0

for dataset in data_to_plot:	

	if i in [0,1,2,3,4]:
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
		axs[i].text(0.25, 0.9,'W. Pacific/Asia', transform=axs[i].transAxes)
		
	if i ==5:
		axs[i].set_ylabel('GEOS-Chem data\ndefault scenario')	
	if i ==10:
		axs[i].set_ylabel('GEOS-Chem data\nimproved wet scavenging')
	if i ==12:
		axs[i].set_xlabel('6h rBC mass concentration (ng/m3 - STP)')
	if i in [1,2,3,6,7,8,11,12,13]:
		axs[i].yaxis.set_visible(False)
	if i in [4,9,14]:
		axs[i].yaxis.set_label_position('right')
		axs[i].yaxis.tick_right()
	
	i+=1
	
plt.savefig('histograms -clustered GEOS-Chem and measurements - 6h FT - v10 - RH ' + str(high_RH_limit) +'%limit-GBPSintoSPac.png',bbox_inches='tight')

plt.show()

########

#hitos for test-runs and SP2


data_to_plot = [SP2_6h_all_non_BB_m,SP2_6h_NPac_m,SP2_6h_SPac_m,SP2_6h_Cont_m,SP2_6h_LRT_m]


labels = ['all', 'NPac','SPac','Cont','LRT']
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	case_data = dataset['default']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	data_to_plot.append(concs)

	stats = {
	'source': 'GEOS-Chem',
	'cluster_name': labels[i],
	'RH_thresh':high_RH_limit,
	'scenario':'default',
	'10':float(np.percentile(concs, 10)),
	'50':float(np.percentile(concs, 50)),
	'90':float(np.percentile(concs, 90)),
	'mean':float(np.mean(concs)),
	'rel_err':float(np.mean(rel_err))
	}
	
	cursor.execute('DELETE FROM whi_gc_and_sp2_stats_on_6h_clustered_ft_data WHERE data_source = %s and cluster = %s and test_scenario = %s and RH_threshold = %s',(stats['source'],stats['cluster_name'],stats['scenario'], stats['RH_thresh']))
	cnx.commit()
	cursor.execute(add_stats, stats)
	cnx.commit()
	
	i+=1
	
	

i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	case_data = dataset['wet_scav']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	data_to_plot.append(concs)
	
	stats = {
	'source': 'GEOS-Chem',
	'cluster_name': labels[i],
	'RH_thresh':high_RH_limit,
	'scenario':'wet_scav',
	'10':float(np.percentile(concs, 10)),
	'50':float(np.percentile(concs, 50)),
	'90':float(np.percentile(concs, 90)),
	'mean':float(np.mean(concs)),
	'rel_err':float(np.mean(rel_err))
	}
	
	cursor.execute('DELETE FROM whi_gc_and_sp2_stats_on_6h_clustered_ft_data WHERE data_source = %s and cluster = %s and test_scenario = %s and RH_threshold = %s',(stats['source'],stats['cluster_name'],stats['scenario'], stats['RH_thresh']))
	cnx.commit()
	cursor.execute(add_stats, stats)
	cnx.commit()
	
	
	i+=1
	
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	case_data = dataset['Van']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	data_to_plot.append(concs)
	
	stats = {
	'source': 'GEOS-Chem',
	'cluster_name': labels[i],
	'RH_thresh':high_RH_limit,
	'scenario':'Van',
	'10':float(np.percentile(concs, 10)),
	'50':float(np.percentile(concs, 50)),
	'90':float(np.percentile(concs, 90)),
	'mean':float(np.mean(concs)),
	'rel_err':float(np.mean(rel_err))
	}
	
	cursor.execute('DELETE FROM whi_gc_and_sp2_stats_on_6h_clustered_ft_data WHERE data_source = %s and cluster = %s and test_scenario = %s and RH_threshold = %s',(stats['source'],stats['cluster_name'],stats['scenario'], stats['RH_thresh']))
	cnx.commit()
	cursor.execute(add_stats, stats)
	cnx.commit()
	
	i+=1	

	
i=0
for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	case_data = dataset['no_bb']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	data_to_plot.append(concs)
	
	stats = {
	'source': 'GEOS-Chem',
	'cluster_name': labels[i],
	'RH_thresh':high_RH_limit,
	'scenario':'no_bb',
	'10':float(np.percentile(concs, 10)),
	'50':float(np.percentile(concs, 50)),
	'90':float(np.percentile(concs, 90)),
	'mean':float(np.mean(concs)),
	'rel_err':float(np.mean(rel_err))
	}
	
	cursor.execute('DELETE FROM whi_gc_and_sp2_stats_on_6h_clustered_ft_data WHERE data_source = %s and cluster = %s and test_scenario = %s and RH_threshold = %s',(stats['source'],stats['cluster_name'],stats['scenario'], stats['RH_thresh']))
	cnx.commit()
	cursor.execute(add_stats, stats)
	cnx.commit()
	
	
	i+=1
	
i=0	
for dataset in [all_data,NPac_data,SPac_data,Cont_data,LRT_data]:
	case_data = dataset['all_together']
	concs = [row[0] for row in case_data]
	errs = [row[1] for row in case_data]
	rel_err = np.mean(errs)
	data_to_plot.append(concs)
	
	stats = {
	'source': 'GEOS-Chem',
	'cluster_name': labels[i],
	'RH_thresh':high_RH_limit,
	'scenario':'all_together',
	'10':float(np.percentile(concs, 10)),
	'50':float(np.percentile(concs, 50)),
	'90':float(np.percentile(concs, 90)),
	'mean':float(np.mean(concs)),
	'rel_err':float(np.mean(rel_err))
	}
	
	cursor.execute('DELETE FROM whi_gc_and_sp2_stats_on_6h_clustered_ft_data WHERE data_source = %s and cluster = %s and test_scenario = %s and RH_threshold = %s',(stats['source'],stats['cluster_name'],stats['scenario'], stats['RH_thresh']))
	cnx.commit()
	cursor.execute(add_stats, stats)
	cnx.commit()
	
	
	i+=1


	
fig, axes = plt.subplots(6,5, figsize=(14, 14), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.0)
axs = axes.ravel()	
i=0

for dataset in data_to_plot:	

	if i in [0,1,2,3,4]:
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
		axs[i].text(0.25, 0.9,'W. Pacific/Asia', transform=axs[i].transAxes)
	
	if i == 5:
		axs[i].set_ylabel('default GC')
	if i == 10:
		axs[i].set_ylabel('enhanced\n wet scavenging')
	if i == 15:
		axs[i].set_ylabel('No Vancouver\n emissions')
	if i == 20:
		axs[i].set_ylabel('no biomass\n burning')
	if i == 25:
		axs[i].set_ylabel('all changes\n together')

	if i in [1,2,3, 6,7,8, 11,12,13, 16,17,18 ,21,22,23, 26,27,28, ]:
		axs[i].yaxis.set_visible(False)
	if i in [4,9,14,19,14,24,29]:
		axs[i].yaxis.set_label_position('right')
		axs[i].yaxis.tick_right()
	if i == 27:
		axs[i].set_xlabel('6h rBC mass concentration (ng/m3 - STP)')
	
	i+=1
	
plt.savefig('histograms -clustered GEOS-Chem and measurements - 6h FT - v10-tests - RH ' + str(high_RH_limit) +'%limit-GBPSintoSPac.png',bbox_inches='tight')

plt.show()


cnx.close()



