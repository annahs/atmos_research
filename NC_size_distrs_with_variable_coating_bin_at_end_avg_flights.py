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


#distr parameters
min_BC_VED = 85  
max_BC_VED = 220  
min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
fit_bin_min = 50
fit_bin_max = 1000
bin_incr = 10
master_bin_file = 'UHSAS_Polar6_20150408_R1_V2.ict'
#master_bin_file = 'UHSAS_Polar6_20150413_R1_V1.ict'

flight_times = {
#'science 1'  : [datetime(2015,4,5,9,0),  datetime(2015,4,5,14,0) ,''],	
#'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ,'UHSAS_Polar6_20150406_R1_V1.ict'],  
#'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ,'UHSAS_Polar6_20150406_R1_V2.ict'],
'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ,'UHSAS_Polar6_20150407_R1_V1.ict'],
'science 3'  : [datetime(2015,4,8,13,0), datetime(2015,4,8,17,0) ,'UHSAS_Polar6_20150408_R1_V1.ict'],  
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0) ,'UHSAS_Polar6_20150408_R1_V2.ict'],
#'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0) ,'UHSAS_Polar6_20150409_R1_V1.ict'],
#'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),'UHSAS_Polar6_20150410_R1_V1.ict'],
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),'UHSAS_Polar6_20150411_R1_V1.ict'],
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),'UHSAS_Polar6_20150413_R1_V1.ict'],
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
	#UHSAS_file = 'UHSAS_Polar6_20150413_R1_V1.ict'
	os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/UHSAS-R1/')
	with open(UHSAS_file, 'r') as f:
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
			bin_dict[i] = [float(LL_limit),float(bin_UL_line[i]),[]]
			i+=1
		
		return bin_dict

def make_bin_dict():
	new_dict = {}
	print fit_bin_min,fit_bin_max,bin_incr
	for bin in range(fit_bin_min,fit_bin_max,bin_incr):
		new_dict[bin] = [bin,(bin+bin_incr),[]]
		
	return new_dict

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

def assemble_bin_data(retrieved_records, flight_data):
	
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
					
		flight_data['core_dia'].append(VED)
		flight_data['min_coated_dia'].append(VED+2*coat_min)
		flight_data['max_coated_dia'].append(VED+2*coat_max)
		flight_data['STP_correction_factor'].append(STP_correction_factor)
		flight_data['sample_flow'].append(sample_flow)
	
	
	return flight_data


	
def make_binned_list(raw_dia_list, bin_dict,total_vol_sccm):
	for dia in raw_dia_list:	
		for point in bin_dict:
			LL_bin = bin_dict[point][0]
			UL_bin = bin_dict[point][1]
			if (LL_bin <= dia < UL_bin):
				bin_dict[point][2].append(dia)
	
	dia_list = []
	area = 0
	for point in bin_dict:
		bin_ll = bin_dict[point][0]
		bin_ul = bin_dict[point][1]
		bin_mid = bin_ll + (bin_ul-bin_ll)/2
		number = len(bin_dict[point][2])
		number_conc = number/total_vol_sccm #in #/cm3
		norm_number_conc = number_conc/(math.log((bin_ul))-math.log(bin_ll))
		area = area+norm_number_conc
		dia_list.append([bin_ll,bin_ul,bin_mid,number,number_conc,norm_number_conc])
	dia_list.sort()
	print 'area',area
	return dia_list
	
def fit_distr(core_dia_list, instr):
	
	#don't fit to bins with no data, this messes with the fit
	if instr == 'SP2':
		core_bin_midpoints  = []
		core_number_conc_norm  = []
		for row in core_dia_list:
			if min_BC_VED <= row[2] < max_BC_VED:
				core_bin_midpoints.append(row[2])
				core_number_conc_norm.append(row[5])
	
	if instr == 'UHSAS':
		core_bin_midpoints  = []
		core_number_conc_norm  = []
		for row in core_dia_list:
			if 70 <= row[2] < 700:
				core_bin_midpoints.append(row[2])
				core_number_conc_norm.append(row[5])

	#core
	try:
		popt, pcov = curve_fit(lognorm, np.array(core_bin_midpoints), np.array(core_number_conc_norm), p0=(2000,0.6,110))	

	except Exception,e: 
		popt = np.nan
		print str(e)
		print 'number fit failure'
		
	return popt

def calc_bin_values(flight_data,UNIX_start_time,UNIX_end_time,UHSAS_file):
	mean_sample_flow  = np.nanmean(flight_data['sample_flow']) #in cm2/min
	mean_STP_correction_factor  = np.nanmean(flight_data['STP_correction_factor']) #no units
	total_samping_time = 0
	for flight in flight_times:
		print flight
		start_time = flight_times[flight][0]
		end_time = flight_times[flight][1]
		UHSAS_file = flight_times[flight][2]
		UNIX_start_time = calendar.timegm(start_time.utctimetuple())
		UNIX_end_time = calendar.timegm(end_time.utctimetuple())
		total_samping_time = total_samping_time + sampling_time_in_flight(UNIX_start_time,UNIX_end_time)
	total_vol = mean_sample_flow*total_samping_time/60 #factor of 60 to convert minutes to secs, result is in cc
	total_vol_sccm = total_vol/mean_STP_correction_factor #factor of 60 to convert minutes to secs, result is in cc

	print 'stp',mean_STP_correction_factor
	print total_vol,  total_vol_sccm
	#cores
	binned_core_dias = getUHSASBins(master_bin_file)
	#binned_core_dias = make_bin_dict()
	core_diameter_list = make_binned_list(flight_data['core_dia'],binned_core_dias,total_vol_sccm)
	core_dia_fit_func =  fit_distr(core_diameter_list,'SP2')

	area = 0
	fit_core_dias_list = []
	for point in binned_core_dias:
		bin_ll = binned_core_dias[point][0]
		bin_ul = binned_core_dias[point][1]
		bin_mid = bin_ll + (bin_ul-bin_ll)/2
		fit_core_number_conc_norm  = lognorm(bin_mid, core_dia_fit_func[0], core_dia_fit_func[1], core_dia_fit_func[2])
		fit_core_number_conc = fit_core_number_conc_norm*(math.log((bin_ul))-math.log(bin_ll))
		fit_core_number = fit_core_number_conc*total_vol_sccm
		fit_core_dias_list.append([bin_ll,bin_ul,bin_mid,fit_core_number,fit_core_number_conc,fit_core_number_conc_norm])
		area+= fit_core_number_conc_norm
		if (bin_ul < min_BC_VED) or (max_BC_VED < bin_ll):
			i=0
			while i < fit_core_number:
				flight_data['min_coated_dia'].append(bin_mid)
				flight_data['max_coated_dia'].append(bin_mid+2*max_coat)
				i+=1
	print 'fit area',area
	fit_core_dias_list.sort()
	#min coats
	binned_min_coat_dias = getUHSASBins(master_bin_file)
	#binned_min_coat_dias = make_bin_dict()
	min_coated_dia_list = make_binned_list(flight_data['min_coated_dia'],binned_min_coat_dias,total_vol_sccm)

	#max coats
	binned_max_coat_dias = getUHSASBins(master_bin_file)
	#binned_max_coat_dias = make_bin_dict()
	max_coated_dia_list = make_binned_list(flight_data['max_coated_dia'],binned_max_coat_dias,total_vol_sccm)

	return [core_diameter_list,min_coated_dia_list,max_coated_dia_list,fit_core_dias_list]	

def plot_distrs(binned_data,UHSAS_list,UHSAS_fitted_list):
	
	core_bin_mids = [row[2] for row in binned_data[0]]
	core_norm_conc = [row[5] for row in binned_data[0]]
	
	min_coat_bin_mids = [row[2] for row in binned_data[1]]
	min_coat_norm_conc = [row[5] for row in binned_data[1]]
	
	max_coat_bin_mids = [row[2] for row in binned_data[2]]
	max_coat_norm_conc = [row[5] for row in binned_data[2]]
	
	core_fit_bin_mids = [row[2] for row in binned_data[3]]
	core_fit_norm_conc = [row[5] for row in binned_data[3]]
	
	uhsas_bin_mids = [row[0] for row in UHSAS_list]
	uhsas_norm_conc = [row[1] for row in UHSAS_list]
	
	uhsas_fitted_bin_mids = [row[2] for row in UHSAS_fitted_list]
	uhsas_fitted_norm_conc = [row[5] for row in UHSAS_fitted_list]
	
	print sum(core_fit_norm_conc)
	print sum(uhsas_fitted_norm_conc)
	
	i=0
	min_ratios = []
	max_ratios = []
	for conc in min_coat_norm_conc:
		min_ratio = conc/uhsas_norm_conc[i]
		max_ratio = max_coat_norm_conc[i]/uhsas_norm_conc[i]
		min_ratios.append(min_ratio)
		max_ratios.append(max_ratio)
		i+=1
	print np.nanmean(min_ratios)
	print np.nanmean(max_ratios)
	#plots
	ticks = [50,60,70,80,100,120,160,200,300,400,600,800]
	fig = plt.figure(figsize= (12,10))
	ax1 = fig.add_subplot(111)
	ax1.plot(uhsas_bin_mids,uhsas_norm_conc, color = 'g',marker='s', label = 'total particles (UHSAS)')
	ax1.scatter(core_bin_mids,core_norm_conc, color = 'k',marker='o', label='rBC cores only')
	ax1.plot(core_fit_bin_mids,core_fit_norm_conc, color = 'grey',marker='',linestyle = '--', label = 'rBC core fit')	
	ax1.plot(min_coat_bin_mids,min_coat_norm_conc, color = 'b',marker='<', label='rBC cores + min coating')
	ax1.plot(max_coat_bin_mids,max_coat_norm_conc, color = 'r',marker='>', label='rBC cores + max coating')	
	#ax1.plot(uhsas_fitted_bin_mids,uhsas_fitted_norm_conc, color = 'g',marker='',linestyle = '--', label = 'UHSAS fit')	
	#ax1.plot(uhsas_bin_mids,min_ratios, color = 'c',marker='o', label = 'min/UHSAS')	
	#ax1.plot(uhsas_bin_mids,max_ratios, color = 'orange',marker='o', label = 'max/UHSAS')	
	ax1.set_xlabel('VED (nm)')
	ax1.set_ylabel('dN/dlog(VED)')
	ax1.set_xscale('log')
	ax1.set_yscale('log')
	ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
	ax1.set_ylim(1,3500)
	ax1.set_xlim(50,1000)
	plt.legend()
	
	plt.show()
	
	ticks = [50,60,70,80,100,120,160,200,300,400,600,800]
	fig = plt.figure(figsize= (12,10))
	ax2 = fig.add_subplot(111)
	ax2.plot(uhsas_bin_mids,min_ratios, color = 'b',marker='o',linestyle = '-', label = 'rBC cores with min coating/UHSAS')	
	ax2.plot(uhsas_bin_mids,max_ratios, color = 'r',marker='s',linestyle = '-', label = 'rBC cores with max coating/UHSAS')	
	ax2.set_xlabel('VED (nm)')
	ax2.set_ylabel('fraction of total particles containing rBC')
	ax2.set_xscale('log')
	#ax2.set_yscale('log')
	ax2.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	ax2.xaxis.set_major_locator(plt.FixedLocator(ticks))
	ax2.set_ylim(0,1)
	ax2.set_xlim(50,1000)
	plt.legend()
	
	plt.show()
	
def write_files(binned_data):
	#cores
	file = open('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/SP2 core data-'+flight+'.txt', 'w')
	file.write('bin_LL\tbin_UL\tbin_mid\tbin_number\tbin_number_conc\tbin_number_conc_norm' + '\n')
	for row in binned_data[0]:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
	#min_coats
	file = open('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/SP2 min coat data-'+flight+'.txt', 'w')
	file.write('bin_LL\tbin_UL\tbin_mid\tbin_number\tbin_number_conc\tbin_number_conc_norm' + '\n')
	for row in binned_data[1]:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
	#max_coats
	file = open('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/SP2 max coat data-'+flight+'.txt', 'w')
	file.write('bin_LL\tbin_UL\tbin_mid\tbin_number\tbin_number_conc\tbin_number_conc_norm' + '\n')
	for row in binned_data[2]:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
	#fit cores
	file = open('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/SP2 core fit data-'+flight+'.txt', 'w')
	file.write('bin_LL\tbin_UL\tbin_mid\tbin_number\tbin_number_conc\tbin_number_conc_norm' + '\n')
	for row in binned_data[3]:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
##script	
#set up data structure
flight_data = {
	'core_dia':[],
	'min_coated_dia':[],
	'max_coated_dia':[],
	'STP_correction_factor':[],
	'sample_flow':[],
	}
	
	
UHSAS_dict = {}
master_bin_list = getUHSASBins(master_bin_file)
for point in master_bin_list:
	master_bin_ll = master_bin_list[point][0]
	master_bin_ul = master_bin_list[point][1]
	master_bin_mid = master_bin_ll + (master_bin_ul-master_bin_ll)/2
	UHSAS_dict[master_bin_mid] = []
				
UHSAS_to_fit_list = []
for flight in flight_times:
	print flight
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UHSAS_file = flight_times[flight][2]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	
	###SP2
	cursor.execute(('''SELECT bc.rBC_mass_fg, bc.coat_thickness_nm_jancalib, bc.LF_scat_amp, hk.sample_flow, ftd.temperature_C, ftd.BP_Pa
		FROM polar6_coating_2015 bc 
		JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id 
		JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id 
		JOIN polar6_hk_data_2015 hk on bc.hk_data_id = hk.id 
		WHERE bc.rBC_mass_fg IS NOT NULL and bc.UNIX_UTC_ts >= %s and bc.UNIX_UTC_ts < %s and bc.particle_type = %s and fssp.FSSPTotalConc <=%s and hk.sample_flow >%s and hk.sample_flow <%s AND bc.rBC_mass_fg >= %s AND bc.rBC_mass_fg <= %s ORDER BY bc.UNIX_UTC_ts'''),
		(UNIX_start_time,UNIX_end_time,'incand',cloud_droplet_conc,100,200,min_rBC_mass,max_rBC_mass))
	coat_data = cursor.fetchall()
		
	#assemble the data for this bin
	flight_data = assemble_bin_data(coat_data,flight_data)
	
	##UHSAS
	if UHSAS_file == '':
		continue
	
	UHSAS_bin_list = getUHSASBins(UHSAS_file)
    
	#get number concs for each bin
	for point in UHSAS_bin_list:
		bin_ll = UHSAS_bin_list[point][0]
		bin_ul = UHSAS_bin_list[point][1]
		bin_mid = bin_ll + (bin_ul-bin_ll)/2
		
			
		#get UHSAS #avg for that bin on that flight (values taken every sec)
		cursor.execute(('''SELECT avg(property_value)
							FROM polar6_uhsas_rbc_binned_data_altcalib bd
							WHERE bd.UNIX_UTC_ts >= %s 
							AND bd.UNIX_UTC_ts < %s 
							AND (bd.bin_LL + (bd.bin_UL-bd.bin_LL)/2) >= %s 
							AND (bd.bin_LL + (bd.bin_UL-bd.bin_LL)/2) < %s 
							AND bd.binned_property = %s
							'''),
							(UNIX_start_time, UNIX_end_time,bin_ll,bin_ul,'UHSAS_#'))
		UHSAS_number = cursor.fetchall()
		UHSAS_number_conc = UHSAS_number[0][0]
		if UHSAS_number_conc != None:
			
			UHSAS_number_conc_norm = UHSAS_number_conc*1.0/(math.log((bin_ul))-math.log(bin_ll))
			for point in master_bin_list:
				master_bin_ll = master_bin_list[point][0]
				master_bin_ul = master_bin_list[point][1]
				master_bin_mid = master_bin_ll + (master_bin_ul-master_bin_ll)/2
				if master_bin_ll <= bin_mid < master_bin_ul:
					UHSAS_dict[master_bin_mid].append(UHSAS_number_conc_norm)
					if bin_ll >= min_BC_VED:
						UHSAS_to_fit_list.append([master_bin_ll,master_bin_ul,master_bin_mid,np.nan,UHSAS_number_conc,UHSAS_number_conc_norm])
UHSAS_list = []
for bin in UHSAS_dict:
	mean_conc = np.mean(UHSAS_dict[bin])
	UHSAS_list.append([bin,mean_conc])
						
UHSAS_list.sort()
	

#UHSAS fit
UHSAS_to_fit_list.sort()
UHSAS_fitted_list = []
uhsas_fit_func =  fit_distr(UHSAS_to_fit_list,'UHSAS')
for point in UHSAS_bin_list:
	bin_ll = UHSAS_bin_list[point][0]
	bin_ul = UHSAS_bin_list[point][1]
	bin_mid = bin_ll + (bin_ul-bin_ll)/2
	fit_uhsas_number_conc_norm  = lognorm(bin_mid, uhsas_fit_func[0], uhsas_fit_func[1], uhsas_fit_func[2])
	fit_uhsas_number_conc = fit_uhsas_number_conc_norm*(math.log((bin_ul))-math.log(bin_ll))
	UHSAS_fitted_list.append([bin_ll,bin_ul,bin_mid,np.nan,fit_uhsas_number_conc,fit_uhsas_number_conc_norm])
UHSAS_fitted_list.sort()

	

print 'binning'
binned_data = calc_bin_values(flight_data,UNIX_start_time,UNIX_end_time,UHSAS_file)
	

plot_distrs(binned_data,UHSAS_list,UHSAS_fitted_list)
	
write_files(binned_data)
	
cnx.close()	