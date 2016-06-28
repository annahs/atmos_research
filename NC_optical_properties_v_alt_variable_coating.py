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
wavelength = 550  #nm
rBC_RI = complex(2.26,1.26)
min_coat = 0  #assumed minimum coating thickness for particles with LEO failure or outside of detection range = 0
max_coat = 100 #assumed maximum coating thickness for particles with LEO failure or outside of detection range = 100
savefig = True
show_distr_plots = False
#alt parameters
min_alt = 0
max_alt =6000
alt_incr = 1000#800
#distr parameters
min_BC_VED = 80  
max_BC_VED = 220  
bin_incr = 10



flight_times = {
'science 1'  : [datetime(2015,4,5,9,43),datetime(2015,4,5,13,48),15.6500, 78.2200, 'Longyearbyen (sc1)']	,	   #longyearbyen
##'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
##'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,31),datetime(2015,4,7,20,48),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
'science 3'  : [datetime(2015,4,8,13,51),datetime(2015,4,8,16,43),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,21,22),-70.338, 82.5014,'Alert (sc2-5)']   ,   #Alert
'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,47),-62.338, 82.0,'Alert (sc2-5)']   ,      #Alert
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,16),-90.9408, 80.5,'Eureka (sc6-7)'] ,	   #eureka
'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,52),-95, 80.1,'Eureka (sc6-7)'] ,          #eureka
#'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,49),-133.7306, 67.1,'Inuvik (sc8-10)'],     #inuvik
#'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,36),-133.7306, 69.3617,'Inuvik (sc8-10)'] ,  #inuvik
#'science 10' : [datetime(2015,4,21,16,07),datetime(2015,4,21,21,24),-131, 69.55,'Inuvik (sc8-10)'],         #inuvik
}

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	
def MieCalc(wavelength,core_dia,coat_th):
	mie = Mie()
	wl = wavelength
	core_rad = core_dia/2 #nm
	shell_thickness = coat_th
	size_par = 2*math.pi*core_rad*1/wl

	#Refractive indices PSL 1.59-0.0i  rBC 2.26- 1.26i  shell 1.5-0.0i
	core_RI = rBC_RI
	shell_rad = core_rad + shell_thickness
	shell_RI = complex(1.5,0.0)
	mie.x = 2*math.pi*core_rad/wl
	mie.m = core_RI
	mie.y = 2*math.pi*shell_rad/wl
	mie.m2 = shell_RI

	abs = mie.qabs()
	abs_xs_nm2 = abs*math.pi*shell_rad**2 	#in nm^2
	abs_xs  = abs_xs_nm2*1e-14 #in cm^2
	
	sca = mie.qsca()
	sca_xs_nm2 = sca*math.pi*shell_rad**2 #in nm^2
	sca_xs = sca_xs_nm2*1e-14 #in cm^2
	
	ext_xs = sca_xs+abs_xs
	
	return [abs_xs,sca_xs,ext_xs]
	
def find_dg(A, w, xc):
	fit_vals = {}
	for bin_val in range (35,1000,1):
		fit_val = lognorm(bin_val, A, w, xc)
		fit_vals[bin_val] = fit_val
	return max(fit_vals.iterkeys(), key=(lambda key: fit_vals[key]))

def fraction_sampled(A, w, xc):
	fit_vals = []
	fit_vals_m = []
	for bin_val in range (35,1000,1):
		fit_val = lognorm(bin_val, A, w, xc)
		fit_vals.append(fit_val)
	full_distr = np.sum(fit_vals)

	for bin_val in range (min_BC_VED,max_BC_VED,1):
		fit_val_m = lognorm(bin_val, A, w, xc)
		fit_vals_m.append(fit_val_m)
	sampled_distr = np.sum(fit_vals_m)

	return sampled_distr/full_distr

def sampling_time_at_alt(start_time,end_time,min_alt,max_alt):
	cursor.execute(('''SELECT ftd.UNIX_UTC_ts, ftd.alt
		FROM polar6_flight_track_details ftd
		JOIN polar6_fssp_cloud_data fssp on ftd.fssd_id = fssp.id 
		WHERE ftd.UNIX_UTC_ts >= %s and ftd.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s and ftd.alt >=%s and ftd.alt < %s ORDER BY ftd.UNIX_UTC_ts'''),
		(start_time,end_time,cloud_droplet_conc,min_alt,max_alt))
	alt_data = cursor.fetchall()
	first_line = True
	temp_list = []
	interval_list = []
	for line in alt_data:
		current_ts = line[0]
		alt = line[1]
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
	
def assign_min_max_coat(VED):
	Dp_Dc = np.nan
	optical_properties_max_coat  = MieCalc(wavelength,VED,max_coat)
	abs_xsec_max_coat = optical_properties_max_coat[0]
	sca_xsec_max_coat = optical_properties_max_coat[1]
	optical_properties_min_coat  = MieCalc(wavelength,VED,min_coat)
	abs_xsec_min_coat = optical_properties_min_coat[0]
	sca_xsec_min_coat = optical_properties_min_coat[1]
	
	return [Dp_Dc,abs_xsec_max_coat,sca_xsec_max_coat,abs_xsec_min_coat,sca_xsec_min_coat]
	
def assemble_bin_data(retrieved_records):
	#set up data structure
	LEO_successes = 0
	LEO_failures = 0
	bin_data = {
		'mass':[],
		'Dp_Dc':[],
		'STP_correction_factor':[],
		'sample_flow':[],
		'abs_xsec_max_coat':[],
		'sca_xsec_max_coat':[],
		'abs_xsec_min_coat':[],
		'sca_xsec_min_coat':[],
		'abs_xsec_bare':[],
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
		
		#succesful LEO fitting and pos coating	
		if (0 <= LEO_amp < 45000):  
			LEO_successes += 1
			if coat >0:
				optical_properties  = MieCalc(wavelength,VED,coat)
				abs_xsec_max_coat = optical_properties[0]
				sca_xsec_max_coat = optical_properties[1]
				abs_xsec_min_coat = abs_xsec_max_coat
				sca_xsec_min_coat = sca_xsec_max_coat
				
				if 160 <= bin < 180:
					Dp_Dc = (VED+2*coat)/VED
				else:
					Dp_Dc = np.nan
					
				opt_results = [Dp_Dc,abs_xsec_max_coat,sca_xsec_max_coat,abs_xsec_min_coat,sca_xsec_min_coat]
			
			else:
				opt_results = assign_min_max_coat(VED)
		
		#failed LEO fitting or neg coating, we calc a max and min case for these
		else:       
			LEO_failures += 1
			opt_results = assign_min_max_coat(VED)
				
		
		bare_optical_properties = MieCalc(wavelength,VED,0.0)
		abs_xsec_bare = bare_optical_properties[0]
		
		bin_data['mass'].append(mass)
		bin_data['Dp_Dc'].append(opt_results[0])
		bin_data['STP_correction_factor'].append(STP_correction_factor)
		bin_data['sample_flow'].append(sample_flow)
		bin_data['abs_xsec_max_coat'].append(opt_results[1])
		bin_data['sca_xsec_max_coat'].append(opt_results[2])
		bin_data['abs_xsec_min_coat'].append(opt_results[3])
		bin_data['sca_xsec_min_coat'].append(opt_results[4])
		bin_data['abs_xsec_bare'].append(abs_xsec_bare)
		
	bin_data_list = [bin_data,LEO_successes,LEO_failures]
	return bin_data_list
		
def calc_bin_optical_properties(bin_start, binning_incr, bin_data_list,binned_data):
	
	bin_data = bin_data_list[0]
	LEO_successes = bin_data_list[1]
	LEO_failures = bin_data_list[2]
	
	bin_mid = bin_start + (binning_incr/2)
			
	total_mass = np.sum(bin_data['mass']) #in fg
	mean_sample_flow  = np.nanmean(bin_data['sample_flow']) #in cm2/min
	mean_STP_correction_factor  = np.nanmean(bin_data['STP_correction_factor']) #no units
	total_samping_time = sampling_time_at_alt(UNIX_start_time,UNIX_end_time,lower_alt,(lower_alt + alt_incr))
	total_vol = mean_sample_flow*total_samping_time/60 #factor of 60 to convert minutes to secs, result is in cc
	mass_conc = (total_mass/total_vol)*mean_STP_correction_factor #in fg/cm3
	numb_conc = (len(bin_data['mass'])/total_vol)*mean_STP_correction_factor #in #/cm3
	bin_mass_conc_norm = mass_conc/(math.log((bin_start+binning_incr))-math.log(bin_start)) #normalize mass
	bin_numb_conc_norm = numb_conc/(math.log((bin_start+binning_incr))-math.log(bin_start)) #normalize number
	mean_Dp_Dc = np.nanmean(bin_data['Dp_Dc'])			
	bin_vol_abs_coeff_max = np.nanmean(bin_data['abs_xsec_max_coat']) * bin_numb_conc_norm  #in cm-1 (cm2 * /cm3)
	bin_vol_sca_coeff_max = np.nanmean(bin_data['sca_xsec_max_coat']) * bin_numb_conc_norm  #in cm-1
	bin_vol_abs_coeff_min = np.nanmean(bin_data['abs_xsec_min_coat']) * bin_numb_conc_norm  #in cm-1
	bin_vol_sca_coeff_min = np.nanmean(bin_data['sca_xsec_min_coat']) * bin_numb_conc_norm  #in cm-1
	bin_vol_abs_coeff_bare = np.nanmean(bin_data['abs_xsec_bare']) * bin_numb_conc_norm  #in cm-1  - need to calc absorption enhancement
	fraction_successful = LEO_successes*1.0/(LEO_successes+LEO_failures)
	
	binned_data[bin_mid] = {
		'bin_mass_conc':mass_conc,
		'bin_numb_conc':numb_conc,
		'bin_Dp_Dc':mean_Dp_Dc,
		'bin_mass_conc_norm':    bin_mass_conc_norm ,
		'bin_numb_conc_norm':    bin_numb_conc_norm ,
		'bin_vol_abs_coeff_max': bin_vol_abs_coeff_max,
		'bin_vol_sca_coeff_max': bin_vol_sca_coeff_max,
		'bin_vol_abs_coeff_min': bin_vol_abs_coeff_min,
		'bin_vol_sca_coeff_min': bin_vol_sca_coeff_min,
		'bin_vol_abs_coeff_bare':bin_vol_abs_coeff_bare,
		'fraction_successful':   fraction_successful,
		}
		
	return binned_data
	
def fit_distrs(binned_data_dict,bin_increment):
	#create bin and step size for extrapolating to the full distr
	fit_bins = []
	for x in range(50,1000,bin_increment):
		fit_bins.append(x)
	
	fit_concs = {}
	bin_midpoints = binned_data_dict.keys()
	number_concs_norm = []
	mass_concs_norm = []
	LEO_fractions = []
	
	#fit the number binned data so we can extrapolate outside of the detection range
	for key in bin_midpoints:
		number_concs_norm.append(binned_data_dict[key]['bin_numb_conc_norm'])
		mass_concs_norm.append(binned_data_dict[key]['bin_mass_conc_norm'])
		LEO_fractions.append(binned_data_dict[key]['fraction_successful'])

	try:
		popt, pcov = curve_fit(lognorm, np.array(bin_midpoints), np.array(number_concs_norm))	
		integrated_number = 0
		for bin_val in fit_bins:
			fit_number_val = lognorm(bin_val, popt[0], popt[1], popt[2])
			fit_concs[bin_val] = [fit_number_val]
			un_normed_numb = fit_number_val*(math.log((bin_val+bin_increment/2))-math.log(bin_val-bin_increment/2))
			integrated_number = integrated_number + un_normed_numb
		Dg_number = find_dg(popt[0], popt[1], popt[2])
		sigma_number = math.exp(popt[1])
		print Dg_number
	except Exception,e: 
		integrated_number = np.nan
		for bin_val in fit_bins:
			fit_concs[bin_val]= [np.nan]
		print str(e)
		print 'number fit failure'
	
	#fit the mass binned data so we can extrapolate outside of the detection range
	try:
		popt, pcov = curve_fit(lognorm, np.array(bin_midpoints), np.array(mass_concs_norm))
		for bin_val in fit_bins:
			fit_mass_val = lognorm(bin_val, popt[0], popt[1], popt[2])
			fit_concs[bin_val].append(fit_mass_val)
		Dg_mass_result = find_dg(popt[0], popt[1], popt[2])
		fraction_mass_meas = fraction_sampled(popt[0], popt[1], popt[2])
		sigma_mass_result = math.exp(popt[1])
		print Dg_mass_result
	except Exception,e: 
		Dg_mass_result = np.nan
		sigma_mass_result = np.nan
		fraction_mass_meas = np.nan
		for bin_val in fit_bins:
			fit_concs[bin_val].append(np.nan)
		print str(e)
		print 'mass fit failure'
	
	fitted_data = []
	for key,val in fit_concs.iteritems():
		fitted_data.append([key, val[0],val[1]])
	fitted_data.sort()
		
	return [fitted_data,Dg_mass_result,sigma_mass_result,fraction_mass_meas,integrated_number]
	
def plot_distrs(fitted_concs,binned_data_results):
	#####plotting distrs if desired	
	#fitted data
	
	fitted_bin_mids = [row[0] for row in fitted_concs]
	fit_binned_number_conc_vals = [row[1] for row in fitted_concs]
	fit_binned_mass_conc_vals = [row[2] for row in fitted_concs]

	#Leo successful fraction data
	LEO_pts = []
	binned_distrs = []
	for bin_midpt in binned_data_results:
		binned_distrs.append([bin_midpt,binned_data_results[bin_midpt]['bin_numb_conc_norm'],binned_data_results[bin_midpt]['bin_mass_conc_norm'],binned_data_results[bin_midpt]['fraction_successful']]) 
		LEO_fraction = binned_data_results[bin_midpt]['fraction_successful']
		if LEO_fraction > 0.97:
			LEO_pts.append(bin_midpt)
		LEO_cutoff = min(LEO_pts or [np.nan])

	bin_midpt = [row[0] for row in binned_distrs]
	number_concs_norm  = [row[1] for row in binned_distrs]
	mass_concs_norm  = [row[2] for row in binned_distrs]
	LEO_fractions  = [row[3] for row in binned_distrs]

	#plots
	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.scatter(bin_midpt,number_concs_norm, color = 'k',marker='o')
	ax1.plot(fitted_bin_mids,fit_binned_number_conc_vals, color = 'k',marker=None, label = 'number')	
	ax1.scatter(bin_midpt,mass_concs_norm, color = 'b',marker='o')
	ax1.plot(fitted_bin_mids,fit_binned_mass_conc_vals, color = 'b',marker=None, label = 'mass')
	ax1.set_xscale('log')
	ax1.set_xlabel('rBC core VED (nm)')
	ax1.set_ylabel('d/dlog(VED)')
	ax1.set_ylim(0,35)
	ax1.set_xlim(40,700)
	plt.legend()
	
	ax2 = ax1.twinx()
	ax2.scatter(bin_midpt,LEO_fractions, color = 'r',marker='s')
	ax2.set_ylim(0,1)
	ax2.set_xlim(40,700)
	ax2.set_ylabel('fraction successful LEO fits', color='r')
	ax2.axvspan(min_BC_VED, LEO_cutoff, alpha=0.15, color='yellow')
	ax2.axvspan(LEO_cutoff, max_BC_VED, alpha=0.15, color='green')
	ax2.fill([160,180,180,160],[0,0,1,1], fill=False, hatch='\\',color ='grey')
	ax2.fill([130,220,220,130],[0,0,1,1], fill=False, hatch='//',color ='grey')
	ax2.axvspan(35, min_BC_VED, alpha=0.15, color='grey')
	ax2.axvspan(max_BC_VED, 1000, alpha=0.15, color='grey')
	ax2.set_xticks([40,50,60,80,100,150,200,300,400,600])
	ax2.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
	
	plt.show()

	
def add_vals_outside_range(fit_concs,binned_data_dict):
			
	for row in fit_concs:
		bin_mid = row[0]
		if bin_mid > max_BC_VED or bin_mid < min_BC_VED:
			bin_mass_conc_norm = row[2]
			bin_numb_conc_norm = row[1]
			fitted_optical_properties_max = MieCalc(wavelength,bin_mid,max_coat)  #resturns [abs xsec, sca xsec, ext xsec]
			fitted_optical_properties_min = MieCalc(wavelength,bin_mid,min_coat)
			fitted_optical_properties_bare = MieCalc(wavelength,bin_mid,0.0)
			bin_vol_abs_coeff_max = fitted_optical_properties_max[0] * bin_numb_conc_norm  #in cm-1 (cm2 * /cm3)
			bin_vol_sca_coeff_max = fitted_optical_properties_max[1] * bin_numb_conc_norm  #in cm-1
			bin_vol_abs_coeff_min = fitted_optical_properties_min[0] * bin_numb_conc_norm  #in cm-1
			bin_vol_sca_coeff_min = fitted_optical_properties_min[1] * bin_numb_conc_norm  #in cm-1
			bin_vol_abs_coeff_bare = fitted_optical_properties_bare[0] * bin_numb_conc_norm  #in cm-1
			
			binned_data_dict[bin_mid] = {
			'bin_mass_conc': 0,
			'bin_Dp_Dc': np.nan,
			'bin_mass_conc_norm':    bin_mass_conc_norm ,
			'bin_numb_conc_norm':    bin_numb_conc_norm ,
			'bin_vol_abs_coeff_max': bin_vol_abs_coeff_max,
			'bin_vol_sca_coeff_max': bin_vol_sca_coeff_max,
			'bin_vol_abs_coeff_min': bin_vol_abs_coeff_min,
			'bin_vol_sca_coeff_min': bin_vol_sca_coeff_min,
			'bin_vol_abs_coeff_bare':bin_vol_abs_coeff_bare,
			#'fraction_successful':   fraction_successful,
			}
			
	return binned_data_dict
	
#calc optical parameters for each altitude
def calc_opti_params(binned_data_dict,Dg_mass,sigma_mass,plot_data,fraction_measured,BC_frac):
	mass_concs_raw_sum = 0
	mass_concs_sum         = 0
	vol_abs_coeff_sum_max  = 0
	vol_sca_coeff_sum_max  = 0
	vol_abs_coeff_sum_min  = 0
	vol_sca_coeff_sum_min  = 0
	vol_abs_coeff_sum_bare = 0
	Dp_Dcs = []
	for bin_mid in binned_data_dict: #integrate
		Dp_Dcs.append(binned_data_dict[bin_mid]['bin_Dp_Dc'])
		mass_concs_raw_sum = mass_concs_raw_sum + binned_data_dict[bin_mid]['bin_mass_conc'] 
		mass_concs_sum = mass_concs_sum + binned_data_dict[bin_mid]['bin_mass_conc_norm']
		vol_abs_coeff_sum_max  = vol_abs_coeff_sum_max  + binned_data_dict[bin_mid]['bin_vol_abs_coeff_max']
		vol_sca_coeff_sum_max  = vol_sca_coeff_sum_max  + binned_data_dict[bin_mid]['bin_vol_sca_coeff_max']
		vol_abs_coeff_sum_min  = vol_abs_coeff_sum_min  + binned_data_dict[bin_mid]['bin_vol_abs_coeff_min']
		vol_sca_coeff_sum_min  = vol_sca_coeff_sum_min  + binned_data_dict[bin_mid]['bin_vol_sca_coeff_min']
		vol_abs_coeff_sum_bare = vol_abs_coeff_sum_bare + binned_data_dict[bin_mid]['bin_vol_abs_coeff_bare']
	Dp_Dc_mean = np.nanmean(Dp_Dcs)
	MAC_max = vol_abs_coeff_sum_max*(10**11)/mass_concs_sum
	MAC_min = vol_abs_coeff_sum_min*(10**11)/mass_concs_sum
	SSA_max = vol_sca_coeff_sum_max/(vol_abs_coeff_sum_max+vol_sca_coeff_sum_max)
	SSA_min = vol_sca_coeff_sum_min/(vol_abs_coeff_sum_min+vol_sca_coeff_sum_min)	
	AE_max = vol_abs_coeff_sum_max/vol_abs_coeff_sum_bare
	AE_min = vol_abs_coeff_sum_min/vol_abs_coeff_sum_bare
	mass_conc_total = mass_concs_raw_sum/fraction_measured
	
	#add overall data to dict	
	mean_alt = lower_alt + alt_incr/2
	if mean_alt not in plot_data:
		plot_data[mean_alt] = {
		'mass_concs'	:[],
		'Dp_Dcs'	    :[],
		'Dgs_mass'		:[],
		'numb_frac_w_BC':[],
		'sigmas_mass'	:[],
		'MAC_maxs'		:[],
		'MAC_mins'		:[],
		'SSA_maxs'		:[],
		'SSA_mins'		:[],
		'AE_maxs'		:[],
		'AE_mins'		:[],            
		}
	plot_data[mean_alt]['Dgs_mass'	].append(Dg_mass)
	plot_data[mean_alt]['Dp_Dcs'	].append(Dp_Dc_mean)
	plot_data[mean_alt]['sigmas_mass'].append(sigma_mass)	
	plot_data[mean_alt]['mass_concs'].append(mass_conc_total)
	plot_data[mean_alt]['numb_frac_w_BC'].append(BC_frac)
	plot_data[mean_alt]['MAC_maxs'	].append(MAC_max)
	plot_data[mean_alt]['MAC_mins'	].append(MAC_min)
	plot_data[mean_alt]['SSA_maxs'	].append(SSA_max)
	plot_data[mean_alt]['SSA_mins'	].append(SSA_min)
	plot_data[mean_alt]['AE_maxs'	].append(AE_max)
	plot_data[mean_alt]['AE_mins'	].append(AE_min)	
	
	return plot_data
	
plot_data={}
for flight in flight_times:
	print flight
	lower_alt = min_alt
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	print 
	while (lower_alt + alt_incr) <= max_alt:
		binned_data = {}
		print lower_alt, lower_alt + alt_incr
		for bin in range(min_BC_VED,max_BC_VED,bin_incr):
			#retrieve the data for this bin		
			cursor.execute(('''SELECT bc.rBC_mass_fg, bc.coat_thickness_nm_jancalib, bc.LF_scat_amp, hk.sample_flow, ftd.temperature_C, ftd.BP_Pa
				FROM polar6_coating_2015 bc 
				JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id 
				JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id 
				JOIN polar6_hk_data_2015 hk on bc.hk_data_id = hk.id 
				WHERE bc.rBC_mass_fg IS NOT NULL and bc.UNIX_UTC_ts >= %s and bc.UNIX_UTC_ts < %s and bc.particle_type = %s and fssp.FSSPTotalConc <=%s and ftd.alt >=%s and ftd.alt < %s and (POW(bc.rBC_mass_fg,(1/3.0))*101.994391398)>=%s and (POW( bc.rBC_mass_fg,(1/3.0))*101.994391398) <%s and hk.sample_flow >%s and hk.sample_flow <%s ORDER BY bc.UNIX_UTC_ts'''),
				(UNIX_start_time,UNIX_end_time,'incand',cloud_droplet_conc,lower_alt, (lower_alt + alt_incr),bin, bin+bin_incr,100,200))
			coat_data = cursor.fetchall()
			
			#assemble the data for this bin
			bin_data = assemble_bin_data(coat_data)
			
			#calc the overall properties for this bin and add them to the dictionary for this alt
			binned_data = calc_bin_optical_properties(bin,bin_incr,bin_data,binned_data)

		#for this altitude, fit the mass and number distributions
		distr_fit_results = fit_distrs(binned_data,bin_incr)
		fit_conc_values = distr_fit_results[0]
		Dg_mass = distr_fit_results[1]
		sigma_mass = distr_fit_results[2]
		fraction_mass_meas = distr_fit_results[3]
		integrated_SP2_number = distr_fit_results[4]
		
		if show_distr_plots == True:		
			plot_distrs(fit_conc_values,binned_data)
	
		#add values from outside dectection range to the binned data
		binned_data = add_vals_outside_range(fit_conc_values,binned_data)
		
		#get UHSAS values
		cursor.execute(('''SELECT AVG(uh.number_per_sccm)
			FROM polar6_uhsas_total_number uh 
			JOIN polar6_fssp_cloud_data fssp on uh.fssp_id = fssp.id 
			JOIN polar6_flight_track_details ftd on uh.flight_track_data_id = ftd.id 
			WHERE uh.UNIX_UTC_ts >= %s and uh.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s and ftd.alt >=%s and ftd.alt < %s'''),
			(UNIX_start_time,UNIX_end_time,cloud_droplet_conc,lower_alt, (lower_alt + alt_incr)))
		uhsas_data = cursor.fetchall()
		uhsas_number_conc = uhsas_data[0][0]
		if uhsas_number_conc == None:
			uhsas_number_conc = np.nan
		
		numb_frac_w_BC = integrated_SP2_number/uhsas_number_conc
		
		#calculate optical parameters for this altitude and add them to the overall dict
		plot_data = calc_opti_params(binned_data,Dg_mass,sigma_mass,plot_data,fraction_mass_meas,numb_frac_w_BC)
				
		lower_alt += alt_incr

cnx.close()
print 'next step . . .'

##
plot_data_list = []

for mean_alt in plot_data:
	mean_Dg = np.nanmean(plot_data[mean_alt]['Dgs_mass'])
	neg_err_Dg = mean_Dg - np.nanmin(plot_data[mean_alt]['Dgs_mass'])
	pos_err_Dg = np.nanmax(plot_data[mean_alt]['Dgs_mass']) - mean_Dg
	
	mean_sigma = np.nanmean(plot_data[mean_alt]['sigmas_mass'])
	neg_err_sigma = mean_sigma - np.nanmin(plot_data[mean_alt]['sigmas_mass'])
	pos_err_sigma = np.nanmax(plot_data[mean_alt]['sigmas_mass']) - mean_sigma
	
	mean_mass_conc = np.nanmean(plot_data[mean_alt]['mass_concs'])
	neg_err_mass_conc = mean_mass_conc - np.nanmin(plot_data[mean_alt]['mass_concs'])
	pos_err_mass_conc = np.nanmax(plot_data[mean_alt]['mass_concs']) - mean_mass_conc
	
	Dp_Dc_mean    = np.nanmean(plot_data[mean_alt]['Dp_Dcs'])
	neg_err_Dp_Dc = Dp_Dc_mean - np.nanmin(plot_data[mean_alt]['Dp_Dcs'])
	pos_err_Dp_Dc = np.nanmax(plot_data[mean_alt]['Dp_Dcs']) - Dp_Dc_mean
	
	BC_frac_mean    = np.nanmean(plot_data[mean_alt]['numb_frac_w_BC'])
	neg_err_BC_frac = BC_frac_mean - np.nanmin(plot_data[mean_alt]['numb_frac_w_BC'])
	pos_err_BC_frac = np.nanmax(plot_data[mean_alt]['numb_frac_w_BC']) - BC_frac_mean
	
	mean_MAC_max = 	 np.nanmean(plot_data[mean_alt]['MAC_maxs'])
	mean_MAC_min = 	 np.nanmean(plot_data[mean_alt]['MAC_mins'])
	mean_SSA_max = 	 np.nanmean(plot_data[mean_alt]['SSA_maxs'])
	mean_SSA_min = 	 np.nanmean(plot_data[mean_alt]['SSA_mins'])
	mean_abs_e_max = np.nanmean(plot_data[mean_alt]['AE_maxs'])
	mean_abs_e_min = np.nanmean(plot_data[mean_alt]['AE_mins'])
	
	plot_data_list.append([mean_alt,mean_Dg,neg_err_Dg,pos_err_Dg,mean_sigma,neg_err_sigma,pos_err_sigma,mean_mass_conc,neg_err_mass_conc,pos_err_mass_conc,mean_MAC_max,mean_MAC_min,mean_SSA_max,	mean_SSA_min,mean_abs_e_max,mean_abs_e_min,Dp_Dc_mean,neg_err_Dp_Dc,pos_err_Dp_Dc,BC_frac_mean,neg_err_BC_frac,pos_err_BC_frac])
                                                                                                                                                                                                                                                  
plot_data_list.sort()                                                                                                                                                                                                                          
 
bar_height = 800    
 
altitudes_bar = [(row[0]-bar_height/2) for row in plot_data_list]
altitudes = [row[0] for row in plot_data_list]

p_mean_Dg = [row[1] for row in plot_data_list]
p_neg_err_Dg = [row[2] for row in plot_data_list]
p_pos_err_Dg = [row[3] for row in plot_data_list]

p_mean_sigma = [row[4] for row in plot_data_list]
p_neg_err_sigma = [row[5] for row in plot_data_list]
p_pos_err_sigma = [row[6] for row in plot_data_list]

p_mean_mass_conc = [row[7] for row in plot_data_list]
p_neg_err_mass_conc = [row[8] for row in plot_data_list]
p_pos_err_mass_conc = [row[9] for row in plot_data_list]

p_mean_MAC_max = [row[10] for row in plot_data_list]
p_mean_MAC_min = [row[11] for row in plot_data_list]
p_mean_MAC_width = [(row[10] - row[11]) for row in plot_data_list]

p_mean_SSA_max = [row[12] for row in plot_data_list]
p_mean_SSA_min = [row[13] for row in plot_data_list]
p_mean_SSA_width = [(row[12] - row[13]) for row in plot_data_list]


p_mean_ae_max = [row[14] for row in plot_data_list] 
p_mean_ae_min = [row[15] for row in plot_data_list] 
p_mean_ae_width = [(row[14] - row[15]) for row in plot_data_list]


	
p_mean_Dp_Dc = [row[16] for row in plot_data_list]
p_neg_err_Dp_Dc = [row[17] for row in plot_data_list]
p_pos_err_Dp_Dc = [row[18] for row in plot_data_list]

p_BC_frac_mean = [row[19] for row in plot_data_list]
p_neg_err_BC_frac_mean = [row[20] for row in plot_data_list]
p_pos_err_BC_frac_mean = [row[21] for row in plot_data_list]


dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/'
os.chdir(dir)
max_alt = 6200      
bar_height = 800      

fig = plt.figure(figsize=(10,10))
                     
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)					
			

ax1.barh(altitudes_bar,p_mean_MAC_width,height=bar_height, left=p_mean_MAC_min,alpha = 0.5,edgecolor = None, color = 'grey')		
#ax1.plot(p_mean_MAC_max,altitudes,marker='o',linestyle='-', color = 'b', label = 'coated rBC')
#ax1.plot(p_mean_MAC_min,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5, label = 'bare rBC')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel(r'MAC $\mathregular{(m^2/g)}$')
ax1.set_xlim(6,18)
ax1.set_ylim(0,max_alt)
ax1.text(0.06,0.93,'A)', transform=ax1.transAxes)


#ax2.fill_betweenx(altitudes, p_mean_SSA_min, p_mean_SSA_max,alpha = 0.5, color = 'grey')
ax2.barh(altitudes_bar,p_mean_SSA_width,height=bar_height, left=p_mean_SSA_min,alpha = 0.5, color = 'grey')		
#ax2.plot(p_mean_SSA_max,altitudes,marker='o',linestyle='-', color = 'grey')
#ax2.plot(p_mean_SSA_min,altitudes,marker='o',linestyle='-', color = 'grey')
ax2.set_xlabel('SSA')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(0.4,0.8)
ax2.set_ylim(0,max_alt)
ax2.text(0.06,0.93,'B)', transform=ax2.transAxes)


ax3.barh(altitudes_bar,p_mean_ae_width,height=bar_height, left=p_mean_ae_min,alpha = 0.5, color = 'grey')		
#ax3.plot(p_mean_ae_max,altitudes,marker='o',linestyle='-', color = 'b')
#ax3.plot(p_mean_ae_min,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5)
ax3.set_xlabel('Abs enhancement')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(1,2)
ax3.set_ylim(0,max_alt)
ax3.text(0.06,0.93,'C)', transform=ax3.transAxes)


if savefig == True:
	plt.savefig(dir + 'MAC SSA AE - 550nm - Sc 1-7 full mass range - using variable coating - neg coats given max-min.png', bbox_inches='tight') 

plt.show()

####

fig = plt.figure()
                     
ax4  = plt.subplot2grid((1,1), (0,0), colspan=1)
ax4.errorbar(p_mean_Dp_Dc,altitudes,xerr=[p_neg_err_Dp_Dc,p_pos_err_Dp_Dc],fmt='o',linestyle='-', color = 'red')
ax4.set_xlabel(r'$\mathregular{D_p/D_c}$ (rBC cores from 160-180nm)')
ax4.set_ylabel('altitude (m)')
ax4.set_xlim(0.8,2.4)
ax4.set_ylim(0,max_alt)

if savefig == True:
	plt.savefig(dir + 'Dp_Dc 160-180nm - Sc 1-7 full mass range using variable coating - neg coats given max-min.png', bbox_inches='tight') 

plt.show()

#####

fig = plt.figure(figsize=(10,10))
                  
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)
ax4  = plt.subplot2grid((2,2), (1,1), colspan=1)

ax1.errorbar(p_mean_Dg,altitudes,xerr = [p_neg_err_Dg,p_pos_err_Dg],fmt='o',linestyle='-', color = 'b')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel(r'Dg (from dM/dlog(D) $\mathregular{ng/m^3-STP}$)')
ax1.set_xlim(100,220)
ax1.set_ylim(0,max_alt)
ax1.text(0.06,0.93,'A)', transform=ax1.transAxes)


ax2.errorbar(p_mean_sigma,altitudes,xerr = [p_neg_err_sigma,p_pos_err_sigma],fmt='o',linestyle='-', color = 'grey')
ax2.set_xlabel(r'sigma (from dM/dlog(D) $\mathregular{ng/m^3-STP}$)')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(1,2)
ax2.set_ylim(0,max_alt)
ax2.text(0.06,0.93,'B)', transform=ax2.transAxes)


ax3.errorbar(p_mean_mass_conc,altitudes,xerr = [p_neg_err_mass_conc,p_pos_err_mass_conc],fmt='o',linestyle='-', color = 'green')
ax3.set_xlabel(r'total mass conc ($\mathregular{ng/m^3-STP}$)')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(0,100)
ax3.set_ylim(0,max_alt)
ax3.text(0.06,0.93,'C)', transform=ax3.transAxes)


ax4.errorbar(p_BC_frac_mean,altitudes,xerr = [p_neg_err_BC_frac_mean,p_pos_err_BC_frac_mean],fmt='o',linestyle='-', color = 'b')
ax4.set_xlabel('Fraction of all particles which contain rBC')
ax4.set_ylabel('altitude (m)')
ax4.set_xlim(0,0.1)
ax4.set_ylim(0,max_alt)
ax4.text(0.06,0.93,'D)', transform=ax4.transAxes)


if savefig == True:
	#plt.savefig('altitude dependent plots - '+flight_times[flight][4]+' - cloud-free.png', bbox_inches='tight') 
	plt.savefig(dir + 'altitude dependent plots Dp sig mass DpDc fracBC -  using variable coating - sc1-7 - cloud-free - neg coats given max-min.png', bbox_inches='tight') 

plt.show()

