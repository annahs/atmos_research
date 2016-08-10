from pymiecoated import Mie
import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
import calendar
from scipy.optimize import curve_fit

cloud_droplet_conc = 0.5

min_coat = 0  #assumed minimum coating thickness for particles with LEO failure or outside of detection range = 0
max_coat = 100 #assumed maximum coating thickness for particles with LEO failure or outside of detection range = 100
savefig = False
show_distr_plots = False

#distr parameters
min_BC_VED = 80  
max_BC_VED = 220  
fit_bin_min = 45
fit_bin_max = 1005
bin_incr = 10


flight_times = {
#'science 1'  : [datetime(2015,4,5,9,0),  datetime(2015,4,5,14,0) ,''],	
##'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ,'UHSAS_Polar6_20150406_R1_V1.ict'],  
##'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ,'UHSAS_Polar6_20150406_R1_V2.ict'],
#'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ,'UHSAS_Polar6_20150407_R1_V1.ict'],
'science 3'  : [datetime(2015,4,8,13,0), datetime(2015,4,8,17,0) ,'UHSAS_Polar6_20150408_R1_V1.ict'],  
#'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0) ,'UHSAS_Polar6_20150408_R1_V2.ict'],
#'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0) ,'UHSAS_Polar6_20150409_R1_V1.ict'],
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),'UHSAS_Polar6_20150410_R1_V1.ict'],
#'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),'UHSAS_Polar6_20150411_R1_V1.ict'],
#'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),'UHSAS_Polar6_20150413_R1_V1.ict'],
#'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),'UHSAS_Polar6_20150420_R1_V1.ict'],
#'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0) ,'UHSAS_Polar6_20150420_R1_V2.ict'],
#'science 10': [datetime(2015,4,21,16,8),datetime(2015,4,21,16,18),'UHSAS_Polar6_20150421_R1_V1.ict'],  ###
}

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def myRound(x, base):
    return int(base * round(float(x)/base))
	
def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))

def getUHSASBins(UHSAS_file):

	os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/UHSAS-R1/')
	with open(UHSAS_file, 'r') as f:
		print UHSAS_file
		file_date = UHSAS_file[13:21]
		date = datetime.strptime(file_date, '%Y%m%d')

		##get bin limits
		i=0
		while i < 9:  #indep_var_number is always on line 10
			f.readline()
			i+=1
		indep_var_number = float(f.readline()) 
		i=0
		while i < (indep_var_number + 11): #check that 11 is right for each set of files
			f.readline()
			i+=1
		bin_LL_line = (f.readline()).split() 
		f.readline() #skip this line 
		bin_UL_line = (f.readline()).split() 
		
		
		##create bins dict
		bin_dict = {}
		i=0
		for LL_limit in bin_LL_line:
			bin_dict[i] = [float(LL_limit),float(bin_UL_line[i])]
			i+=1
		
		return bin_dict

def sampling_time_in_flight(start_time,end_time):
	cursor.execute(('''SELECT ftd.UNIX_UTC_ts
		FROM polar6_flight_track_details ftd
		JOIN polar6_fssp_cloud_data fssp on ftd.fssd_id = fssp.id 
		WHERE ftd.UNIX_UTC_ts >= %s and ftd.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s ORDER BY ftd.UNIX_UTC_ts'''),
		(start_time,end_time,cloud_droplet_conc))
	alt_data = cursor.fetchall()
	first_line = True
	temp_list = []
	interval_list = []
	for line in alt_data:
		current_ts = line[0]
		if first_line == True:
			prior_ts = current_ts
			first_line = False
		if (current_ts - prior_ts) <= 1:
			temp_list.append(current_ts)
			prior_ts = current_ts
		else: 
			time_interval = (temp_list[-1]-temp_list[0])  #in sec
			interval_list.append(time_interval)
			temp_list = []
			temp_list.append(current_ts)
			prior_ts = current_ts
			
	#add in last interval
	if len(temp_list):
		time_interval = (temp_list[-1]-temp_list[0])  #in sec
		interval_list.append(time_interval)
		total_sampling_time = np.sum(interval_list)
	else:
		total_sampling_time = 0
		
	return total_sampling_time

def assemble_bin_data(retrieved_records):
	#set up data structure
	bin_data = {
		'VED':[],
		'coat_min':[],
		'coat_max':[],
		'STP_correction_factor':[],
		'sample_flow':[],
		}

	#parse each row in results
	for row in retrieved_records:
		mass = row[0] 
		coat = row[1]
		LEO_amp = row[2]
		sample_flow = row[3]
		temperature = row[4] + 273.15 #convert to Kelvin
		pressure = row[5]
		VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		STP_correction_factor = (101325/pressure)*(temperature/273.15)
		
		#succesful LEO fitting	
		if (0 <= LEO_amp < 45000) and coat != None:  #failed LEO fits give neg LEO amps (e.g -2)
			#if coat >= 0:	
			coat_min = coat
			coat_max = coat
	
		#failed LEO fitting or neg coating, we calc a max and min case for these
		else: 
			coat_min = min_coat
			coat_max = max_coat
					
		bin_data['VED'].append(VED)
		bin_data['coat_min'].append(coat_min)
		bin_data['coat_max'].append(coat_max)
		bin_data['STP_correction_factor'].append(STP_correction_factor)
		bin_data['sample_flow'].append(sample_flow)
	
	
	return bin_data

def calc_bin_values(bin_start, binning_incr, bin_data,binned_data,UNIX_start_time,UNIX_end_time):
	
	bin_mid = bin_start + (binning_incr/2)
	mean_core_VED = np.nanmean(bin_data['VED']) #in nm
	mean_coat_min = np.nanmean(bin_data['coat_min']) #in nm
	mean_coat_max = np.nanmean(bin_data['coat_max']) #in nm
	mean_sample_flow  = np.nanmean(bin_data['sample_flow']) #in cm2/min
	mean_STP_correction_factor  = np.nanmean(bin_data['STP_correction_factor']) #no units
	total_samping_time = sampling_time_in_flight(UNIX_start_time,UNIX_end_time)
	total_vol = mean_sample_flow*total_samping_time/60 #factor of 60 to convert minutes to secs, result is in cc
	total_vol_sccm = total_vol/mean_STP_correction_factor #factor of 60 to convert minutes to secs, result is in cc
	numb_conc = len(bin_data['VED'])/total_vol_sccm #in #/cm3
	bin_numb_conc_norm = numb_conc/(math.log((bin_start+binning_incr))-math.log(bin_start)) #normalize number
	
	
	binned_data[bin_mid] = {
		'bin_mean_VED':mean_core_VED,
		'bin_mean_coat_min':mean_coat_min,
		'bin_mean_coat_max':mean_coat_max,
		'bin_number':bin_numb_conc_norm ,
		}

	return binned_data	

	
def fit_distrs(binned_data_dict,bin_increment):
	#create bin and step size for extrapolating to the full distr
	fit_bins = []
	for x in range(fit_bin_min,fit_bin_max,bin_increment):
		fit_bins.append(x)
	
	fit_concs = {}
	core_distr = []

	#fit the number binned data so we can extrapolate outside of the detection range
	for key in binned_data_dict:
		core_number  = binned_data_dict[key]['bin_number']
		core_distr.append([key,core_number])
		
	core_distr.sort()

	core_bin_midpoints  = [row[0] for row in core_distr]
	core_number_concs  = [row[1] for row in core_distr]
	
	#core
	try:
		popt, pcov = curve_fit(lognorm, np.array(core_bin_midpoints), np.array(core_number_concs))	
		for bin_val in fit_bins:
			fit_core_val = lognorm(bin_val, popt[0], popt[1], popt[2])
			fit_concs[bin_val] = [fit_core_val]
	except Exception,e: 
		for bin_val in fit_bins:
			fit_concs[bin_val]= [np.nan]
		print str(e)
		print 'number fit failure'
	
	
	fitted_data = []
	for key,val in fit_concs.iteritems():
		fitted_data.append([key, val[0]])
	fitted_data.sort()
		
	return fitted_data
	

	
def add_vals_outside_range(distr_fit_results,binned_data):
			
	for row in distr_fit_results:
		bin_mid = row[0]
		if bin_mid > max_BC_VED or bin_mid < min_BC_VED:
			bin_numb_conc_norm = row[1]
						
			binned_data[bin_mid] = {
				'bin_mean_VED':bin_mid,
				'bin_mean_coat_min':min_coat,
				'bin_mean_coat_max':max_coat,
				'bin_number':bin_numb_conc_norm ,
				}
			
	return binned_data
	
def consolidate_duplicate_bins(binned_data):
	core_distr_d = {}
	min_coat_distr_d = {}
	max_coat_distr_d = {}

	for key in binned_data:
		core_number  = binned_data[key]['bin_number']
		bin_mean_coat_min = binned_data[key]['bin_mean_coat_min']
		bin_mean_coat_max = binned_data[key]['bin_mean_coat_max']

		#round so that we can bin it and find nearest bin mid point dependng on if we rounded up or down
		core_min_coat_rounded = myRound(key+2.*bin_mean_coat_min,10) 
		if core_min_coat_rounded - (key+2.*bin_mean_coat_min) >= 0:
			core_min_coat_bin = core_min_coat_rounded - 5
		else:
			core_min_coat_bin = core_min_coat_rounded + 5
		##
		core_max_coat_rounded = myRound(key+2.*bin_mean_coat_max,10)
		if core_max_coat_rounded - (key+2.*bin_mean_coat_min) >= 0:
			core_max_coat_bin = core_max_coat_rounded - 5
		else:
			core_max_coat_bin = core_max_coat_rounded + 5

		
		#add to dict
		core_distr_d[key] = core_number
		#
		if core_min_coat_bin in min_coat_distr_d:
			min_coat_distr_d[core_min_coat_bin] = min_coat_distr_d[core_min_coat_bin] + core_number
		else:
			min_coat_distr_d[core_min_coat_bin] = core_number
		#
		if core_max_coat_bin in max_coat_distr_d:
			max_coat_distr_d[core_max_coat_bin] = max_coat_distr_d[core_max_coat_bin] + core_number
		else:
			max_coat_distr_d[core_max_coat_bin] = core_number
			

	return [core_distr_d,min_coat_distr_d,max_coat_distr_d]

def add_to_overall_dicts(core_distr_d,min_coat_distr_d,max_coat_distr_d,all_core_data,all_min_coat_data,all_max_coat_data):	
	for key in core_distr_d:
		all_core_data[key].append(core_distr_d[key])
	for key in min_coat_distr_d:
		all_min_coat_data[key].append(min_coat_distr_d[key])
	for key in max_coat_distr_d:
		all_max_coat_data[key].append(max_coat_distr_d[key])

def get_overall_averages(list_of_dicts):
	avgs_list = []
	for item in list_of_dicts:
		data_avg = {}
		for key in item:
			data_avg[key] = np.nanmean(item[key])
		avgs_list.append(data_avg)
		
	return avgs_list
		
def plot_distrs(fitted_concs,core_distr_d,min_coat_distr_d,max_coat_distr_d):
	core_distr = []
	min_coat_distr = []
	max_coat_distr = []
	
	
	for key in core_distr_d:
		core_distr.append([key,core_distr_d[key]])
	for key in min_coat_distr_d:	
		min_coat_distr.append([key,min_coat_distr_d[key]])
	for key in max_coat_distr_d:
		max_coat_distr.append([key,max_coat_distr_d[key]])
	
	core_distr.sort()
	min_coat_distr.sort()
	max_coat_distr.sort()
	
	core_bin_midpoints  = [row[0] for row in core_distr]
	core_number_concs  = [row[1] for row in core_distr]
	
	min_coat_bin_midpoints  = [row[0] for row in min_coat_distr]
	min_coat_number_concs  = [row[1] for row in min_coat_distr]
	
	max_coat_bin_midpoints  = [row[0] for row in max_coat_distr]
	max_coat_number_concs  = [row[1] for row in max_coat_distr]
	
	
	#fit results
	fitted_bin_mids = [row[0] for row in fitted_concs]
	fit_core_number_concs = [row[1] for row in fitted_concs]

	#plots
	ticks = [50,60,70,80,100,120,160,200,300,400,600,800]
	fig = plt.figure(figsize= (12,10))
	ax1 = fig.add_subplot(111)
	ax1.plot(core_bin_midpoints,core_number_concs, color = 'k',marker='o', label='rBC cores only')
	ax1.plot(min_coat_bin_midpoints,min_coat_number_concs, color = 'b',marker='o', label='rBC cores + min coating')
	ax1.plot(max_coat_bin_midpoints,max_coat_number_concs, color = 'r',marker='o', label='rBC cores + max coating')
	ax1.plot(fitted_bin_mids,fit_core_number_concs, color = 'k',marker=None, label = 'cores only fit')	
	ax1.set_xlabel('VED (nm)')
	ax1.set_ylabel('dN/dlog(VED)')
	ax1.set_xscale('log')
	ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
	#ax1.set_ylim(0,35)
	ax1.set_xlim(50,1000)
	plt.legend()
	
	plt.show()
	
	
def plot_distrs_all(core_distr_d,min_coat_distr_d,max_coat_distr_d,UHSAS_distr_d):
	core_distr = []
	min_coat_distr = []
	max_coat_distr = []
	UHSAS_distr = []

	for key in core_distr_d:
		core_distr.append([key,core_distr_d[key]])
	for key in min_coat_distr_d:	
		min_coat_distr.append([key,min_coat_distr_d[key]])
		for number in [85,95,105,125,145,165]:
			min_coat_distr.append([number,1])
	for key in max_coat_distr_d:
		max_coat_distr.append([key,max_coat_distr_d[key]])
		for number in [215]:
			max_coat_distr.append([number,1])
	for key in UHSAS_distr_d:
		UHSAS_distr.append([key,UHSAS_distr_d[key]])
	
	core_distr.sort()
	min_coat_distr.sort()
	max_coat_distr.sort()
	UHSAS_distr.sort()
	
	core_bin_midpoints  = [row[0] for row in core_distr]
	core_number_concs  = [row[1] for row in core_distr]
	
	min_coat_bin_midpoints  = np.array([row[0] for row in min_coat_distr])
	min_coat_number_concs  = np.array([row[1] for row in min_coat_distr])
	
	max_coat_bin_midpoints  = np.array([row[0] for row in max_coat_distr])
	max_coat_number_concs  = np.array([row[1] for row in max_coat_distr])
	
	max_UHSAS_bin_midpoints  = [row[0] for row in UHSAS_distr]
	max_UHSAS_number_concs  = [row[1] for row in UHSAS_distr]
	
	min_coat_mask = np.isfinite(min_coat_number_concs)
	max_coat_mask = np.isfinite(max_coat_number_concs)

	print np.nansum(min_coat_number_concs),np.nansum(max_coat_number_concs),np.nansum(core_number_concs)
	
	#plots
	ticks = [50,60,70,80,100,120,160,200,300,400,600,800]
	fig = plt.figure(figsize= (12,10))
	ax1 = fig.add_subplot(111)
	ax1.plot(core_bin_midpoints,core_number_concs, color = 'k',marker='o', label='rBC cores only')
	ax1.plot(min_coat_bin_midpoints[min_coat_mask],min_coat_number_concs[min_coat_mask], color = 'b',marker='o', label='rBC cores + min coating')
	#ax1.plot(min_coat_bin_midpoints,min_coat_number_concs, color = 'b',marker='o', label='cores + min coating')
	ax1.plot(max_coat_bin_midpoints[max_coat_mask],max_coat_number_concs[max_coat_mask], color = 'r',marker='o', label='rBC cores + max coating')
	ax1.plot(max_UHSAS_bin_midpoints,max_UHSAS_number_concs, color = 'g',marker='o', label = 'UHSAS')	
	ax1.set_xlabel('VED (nm)')
	ax1.set_ylabel('dN/dlog(VED)')
	ax1.set_xscale('log')
	ax1.set_yscale('log')
	ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
	ax1.set_ylim(1,2000)
	ax1.set_xlim(50,1000)
	plt.legend()
	
	plt.show()

######  start script  ########	
all_core_data={}
all_min_coat_data={}
all_max_coat_data={}
for bin in range(fit_bin_min,(fit_bin_max+max_BC_VED),bin_incr):
	all_core_data[bin] = []
	all_min_coat_data[bin] = []
	all_max_coat_data[bin] = []

	
for flight in flight_times:
	print flight

	binned_data = {}
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	
	
	for bin in range(min_BC_VED,max_BC_VED,bin_incr):
		#retrieve the data for this bin		
		cursor.execute(('''SELECT bc.rBC_mass_fg, bc.coat_thickness_nm_jancalib, bc.LF_scat_amp, hk.sample_flow, ftd.temperature_C, ftd.BP_Pa
			FROM polar6_coating_2015 bc 
			JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id 
			JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id 
			JOIN polar6_hk_data_2015 hk on bc.hk_data_id = hk.id 
			WHERE bc.rBC_mass_fg IS NOT NULL and bc.UNIX_UTC_ts >= %s and bc.UNIX_UTC_ts < %s and bc.particle_type = %s and fssp.FSSPTotalConc <=%s and (POW(bc.rBC_mass_fg,(1/3.0))*101.994391398)>=%s and (POW( bc.rBC_mass_fg,(1/3.0))*101.994391398) <%s and hk.sample_flow >%s and hk.sample_flow <%s ORDER BY bc.UNIX_UTC_ts'''),
			(UNIX_start_time,UNIX_end_time,'incand',cloud_droplet_conc,bin, bin+bin_incr,100,200))
		coat_data = cursor.fetchall()
		
		#assemble the data for this bin
		bin_data = assemble_bin_data(coat_data)
		
		#calc the overall properties for this bin and add them to the dictionary for this alt
		binned_data = calc_bin_values(bin,bin_incr,bin_data,binned_data,UNIX_start_time,UNIX_end_time)
	
	######
	
	file = open('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/SP2 data-'+flight+'.txt', 'w')
	test = []
	for item in binned_data:
		test.append([item, binned_data[item]['bin_mean_VED'],binned_data[item]['bin_mean_coat_min'],binned_data[item]['bin_mean_coat_max'],binned_data[item]['bin_number']])
	test.sort()

	file.write('bin_VED\tbin_mean_VED\tbin_mean_coat_min\tbin_mean_coat_max\tbin_number' + '\n')
	for row in test:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
	sys.exit()
	#####
	
	#for this flight, fit the mass and number distributions
	distr_fit_results = fit_distrs(binned_data,bin_incr)
	
	#add values from outside dectection range to the binned data
	binned_data = add_vals_outside_range(distr_fit_results,binned_data)
	
	#consildate all the duplicated bins after coatings calculated and separate into 3 dicts (core, min coat, and max coat)
	core_binned_data,min_binned_data,max_binned_data = consolidate_duplicate_bins(binned_data)
	
	if show_distr_plots == True:		
		plot_distrs(distr_fit_results,core_binned_data,min_binned_data,max_binned_data)

		
	#add this flights data to the overall dict
	add_to_overall_dicts(core_binned_data,min_binned_data,max_binned_data,all_core_data,all_min_coat_data,all_max_coat_data)
	

#get averages for each bin
all_core_data_avg,all_min_coat_data_avg,all_max_coat_data_avg = get_overall_averages([all_core_data,all_min_coat_data,all_max_coat_data])	


UHSAS_dict = {}
for flight in flight_times:
	
	UHSAS_file = flight_times[flight][2]
	if UHSAS_file == '':
		continue
	bin_dict = getUHSASBins(UHSAS_file)

	#get number concs for each bin
	for bin in bin_dict:
		bin_LL =  bin_dict[bin][0]
		bin_UL =  bin_dict[bin][1]

		bin_MP = bin_LL + (bin_UL-bin_LL)/2
		
			
		#get UHSAS #
		cursor.execute(('''SELECT avg(property_value)
							FROM polar6_uhsas_rbc_binned_data_altcalib bd
							WHERE bd.UNIX_UTC_ts >= %s 
							AND bd.UNIX_UTC_ts < %s 
							AND bd.bin_LL >= %s 
							AND bd.bin_UL <= %s 
							AND bd.binned_property = %s
							'''),
							(UNIX_start_time, UNIX_end_time,bin_LL,bin_UL,'UHSAS_#'))
		UHSAS_number = cursor.fetchall()
		UHSAS_number_mean = UHSAS_number[0][0] 
		if UHSAS_number_mean != None:
			UHSAS_number_mean_norm = UHSAS_number_mean/(math.log((bin_UL))-math.log(bin_LL))

			if bin_MP in UHSAS_dict:
				UHSAS_dict[bin_MP].append(UHSAS_number_mean_norm)
			else:
				UHSAS_dict[bin_MP] = [UHSAS_number_mean_norm]
				
UHSAS_avg_distr = get_overall_averages([UHSAS_dict])[0]	
				
##############	

plot_distrs_all(all_core_data_avg,all_min_coat_data_avg,all_max_coat_data_avg,UHSAS_avg_distr)



if savefig == True:
	#plt.savefig('altitude dependent plots - '+flight_times[flight][4]+' - cloud-free.png', bbox_inches='tight') 
	plt.savefig('altitude dependent plots Dp sig mass DpDc fracBC -  using variable coating - sc1-7 - cloud-free - neg coats incl as smaller bare cores.png', bbox_inches='tight') 

plt.show()

