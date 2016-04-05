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
savefig = False
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
#'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
#'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,31),datetime(2015,4,7,20,48),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
'science 3'  : [datetime(2015,4,8,13,51),datetime(2015,4,8,16,43),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,21,22),-70.338, 82.5014,'Alert (sc2-5)']   ,   #Alert
'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,47),-62.338, 82.0,'Alert (sc2-5)']   ,      #Alert
#'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
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


	
#bin and step size for extrapolating to the full distr
fit_bins = []
for x in range (35,1000,bin_incr):
	fit_bins.append(x)

plot_data={}
for flight in flight_times:
	print flight
	lower_alt = min_alt
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	
	while (lower_alt + alt_incr) <= max_alt:
		print lower_alt, lower_alt + alt_incr
		binned_data = {}
		for bin in range(min_BC_VED,max_BC_VED,bin_incr):
			#retrieve the data for this bin
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
			
			LEO_successes = 0
			LEO_failures = 0
			cursor.execute(('''SELECT bc.rBC_mass_fg, bc.coat_thickness_nm_jancalib, bc.LF_scat_amp, hk.sample_flow, ftd.temperature_C, ftd.BP_Pa
				FROM polar6_coating_2015 bc 
				JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id 
				JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id 
				JOIN polar6_hk_data_2015 hk on bc.hk_data_id = hk.id 
				WHERE bc.rBC_mass_fg IS NOT NULL and bc.UNIX_UTC_ts >= %s and bc.UNIX_UTC_ts < %s and bc.particle_type = %s and fssp.FSSPTotalConc <=%s and ftd.alt >=%s and ftd.alt < %s and (POW(bc.rBC_mass_fg,(1/3.0))*101.994391398)>=%s and (POW( bc.rBC_mass_fg,(1/3.0))*101.994391398) <%s and hk.sample_flow >%s and hk.sample_flow <%s ORDER BY bc.UNIX_UTC_ts'''),
				(UNIX_start_time,UNIX_end_time,'incand',cloud_droplet_conc,lower_alt, (lower_alt + alt_incr),bin, bin+bin_incr,100,200))
			coat_data = cursor.fetchall()

			for row in coat_data:
				mass = row[0] 
				coat = row[1]
				LEO_amp = row[2]
				sample_flow = row[3]
				temperature = row[4] + 273.15 #convert to Kelvin
				pressure = row[5]
				VED = (((mass/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
				STP_correction_factor = (101325/pressure)*(temperature/273.15)
				
				if 0 <= LEO_amp < 45000:  #succesful LEO fitting
					LEO_successes += 1
					if coat < 0:	#negative coating case then just calc for smaller core size or ignore?
						continue 
						#if coat != None:
						#	optical_properties  = MieCalc(wavelength,(VED-coat),min_coat)
						#	Dp_Dc = np.nan
					else:    #positive coating case
						optical_properties  = MieCalc(wavelength,VED,coat)
						if 160 <= bin < 180:
							Dp_Dc = (VED+2*coat)/VED
						else:
							Dp_Dc = np.nan
					abs_xsec_max_coat = optical_properties[0]
					sca_xsec_max_coat = optical_properties[1]
					abs_xsec_min_coat = abs_xsec_max_coat
					sca_xsec_min_coat = sca_xsec_max_coat
				else:        #failed LEO fitting, we calc a max and min case for these
					LEO_failures += 1
					Dp_Dc = np.nan
					optical_properties_max_coat  = MieCalc(wavelength,VED,max_coat)
					abs_xsec_max_coat = optical_properties_max_coat[0]
					sca_xsec_max_coat = optical_properties_max_coat[1]
					optical_properties_min_coat  = MieCalc(wavelength,VED,min_coat)
					abs_xsec_min_coat = optical_properties_min_coat[0]
					sca_xsec_min_coat = optical_properties_min_coat[1]
				bare_optical_properties = MieCalc(wavelength,VED,0.0)
				abs_xsec_bare = bare_optical_properties[0]
				
				bin_data['mass'].append(mass)
				bin_data['Dp_Dc'].append(Dp_Dc)
				bin_data['STP_correction_factor'].append(STP_correction_factor)
				bin_data['sample_flow'].append(sample_flow)
				bin_data['abs_xsec_max_coat'].append(abs_xsec_max_coat)
				bin_data['sca_xsec_max_coat'].append(sca_xsec_max_coat)
				bin_data['abs_xsec_min_coat'].append(abs_xsec_min_coat)
				bin_data['sca_xsec_min_coat'].append(sca_xsec_min_coat)
				bin_data['abs_xsec_bare'].append(abs_xsec_bare)
		
			bin_mid = bin + (bin_incr/2)
			
			total_mass = np.sum(bin_data['mass']) #in fg
			mean_sample_flow  = np.nanmean(bin_data['sample_flow']) #in cm2/min
			mean_STP_correction_factor  = np.nanmean(bin_data['STP_correction_factor']) #no units
			total_samping_time = sampling_time_at_alt(UNIX_start_time,UNIX_end_time,lower_alt,(lower_alt + alt_incr))
			total_vol = mean_sample_flow*total_samping_time/60 #factor of 60 to convert minutes to secs, result is in cc
			mass_conc = (total_mass/total_vol)*mean_STP_correction_factor #in fg/cm3
			numb_conc = (len(bin_data['mass'])/total_vol)*mean_STP_correction_factor #in #/cm3
			bin_mass_conc_norm = mass_conc/(math.log((bin+bin_incr))-math.log(bin)) #normalize mass
			bin_numb_conc_norm = numb_conc/(math.log((bin+bin_incr))-math.log(bin)) #normalize number
			mean_Dp_Dc = np.nanmean(bin_data['Dp_Dc'])			
			bin_vol_abs_coeff_max = np.nanmean(bin_data['abs_xsec_max_coat']) * bin_numb_conc_norm  #in cm-1 (cm2 * /cm3)
			bin_vol_sca_coeff_max = np.nanmean(bin_data['sca_xsec_max_coat']) * bin_numb_conc_norm  #in cm-1
			bin_vol_abs_coeff_min = np.nanmean(bin_data['abs_xsec_min_coat']) * bin_numb_conc_norm  #in cm-1
			bin_vol_sca_coeff_min = np.nanmean(bin_data['sca_xsec_min_coat']) * bin_numb_conc_norm  #in cm-1
			bin_vol_abs_coeff_bare = np.nanmean(bin_data['abs_xsec_bare']) * bin_numb_conc_norm  #in cm-1  - need to calc absorption enhancement
			fraction_successful = LEO_successes*1.0/(LEO_successes+LEO_failures)
			
			binned_data[bin_mid] = {
				'bin_mass_conc':mass_conc,
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

		#distributions
		fit_concs = {}
		bin_midpoints = binned_data.keys()
		number_concs_norm = []
		mass_concs_norm = []
		LEO_fractions = []
		
		#fit the number binned data so we can extrapolate outside of the detection range
		for key in bin_midpoints:
			number_concs_norm.append(binned_data[key]['bin_numb_conc_norm'])
			mass_concs_norm.append(binned_data[key]['bin_mass_conc_norm'])
			LEO_fractions.append(binned_data[key]['fraction_successful'])
		
		try:
			popt, pcov = curve_fit(lognorm, np.array(bin_midpoints), np.array(number_concs_norm))	
			for bin_val in fit_bins:
				fit_number_val = lognorm(bin_val, popt[0], popt[1], popt[2])
				fit_concs[bin_val] = [fit_number_val]
			Dg_number = find_dg(popt[0], popt[1], popt[2])
			sigma_number = math.exp(popt[1])
			print Dg_number
		except Exception,e: 
			print str(e)
			print 'number fit failure'
		
		#fit the mass binned data so we can extrapolate outside of the detection range
		try:
			popt, pcov = curve_fit(lognorm, np.array(bin_midpoints), np.array(mass_concs_norm))
			for bin_val in fit_bins:
				fit_mass_val = lognorm(bin_val, popt[0], popt[1], popt[2])
				fit_concs[bin_val].append(fit_mass_val)
			Dg_mass = find_dg(popt[0], popt[1], popt[2])
			fraction_measured = fraction_sampled(popt[0], popt[1], popt[2])
			sigma_mass = math.exp(popt[1])
			print Dg_mass
		except Exception,e: 
			print str(e)
			print 'mass fit failure'
					
			
		#####plotting distrs if desired	
		#fitted data
		fitted_data = []
		for key,val in fit_concs.iteritems():
			fitted_data.append([key, val[0],val[1]])
		fitted_data.sort()
		fitted_bin_mids = [row[0] for row in fitted_data]
		fit_binned_number_conc_vals = [row[1] for row in fitted_data]
		fit_binned_mass_conc_vals = [row[2] for row in fitted_data]
		
		if show_distr_plots == True:
			#Leo successful fraction data
			LEO_pts = []
			for bin_midpt in binned_data:
				LEO_fraction = binned_data[bin_midpt]['fraction_successful']
				if LEO_fraction > 0.97:
					LEO_pts.append(bin_midpt)
				LEO_cutoff = min(LEO_pts)

		
			#plots
			fig = plt.figure()
			ax1 = fig.add_subplot(111)
			ax1.scatter(bin_midpoints,number_concs_norm, color = 'k',marker='o')
			ax1.plot(fitted_bin_mids,fit_binned_number_conc_vals, color = 'k',marker=None, label = 'number')	
			ax1.scatter(bin_midpoints,mass_concs_norm, color = 'b',marker='o')
			ax1.plot(fitted_bin_mids,fit_binned_mass_conc_vals, color = 'b',marker=None, label = 'mass')
			ax1.set_xscale('log')
			ax1.set_xlabel('rBC core VED (nm)')
			ax1.set_ylabel('d/dlog(VED)')
			ax1.set_ylim(0,35)
			ax1.set_xlim(40,700)
			plt.legend()
			
			ax2 = ax1.twinx()
			ax2.scatter(bin_midpoints,LEO_fractions, color = 'r',marker='s')
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

		#################		
		#add values from outside dectection range to the binned data
		for row in fitted_data:
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
				
				binned_data[bin_mid] = {
				'bin_mass_conc': 0,
				'bin_Dp_Dc': np.nan,
				'bin_mass_conc_norm':    bin_mass_conc_norm ,
				'bin_numb_conc_norm':    bin_numb_conc_norm ,
				'bin_vol_abs_coeff_max': bin_vol_abs_coeff_max,
				'bin_vol_sca_coeff_max': bin_vol_sca_coeff_max,
				'bin_vol_abs_coeff_min': bin_vol_abs_coeff_min,
				'bin_vol_sca_coeff_min': bin_vol_sca_coeff_min,
				'bin_vol_abs_coeff_bare':bin_vol_abs_coeff_bare,
				'fraction_successful':   fraction_successful,
				}
				
		
		#calc optial parameters for each altitude
		mass_concs_raw_sum = 0
		mass_concs_sum         = 0
		vol_abs_coeff_sum_max  = 0
		vol_sca_coeff_sum_max  = 0
		vol_abs_coeff_sum_min  = 0
		vol_sca_coeff_sum_min  = 0
		vol_abs_coeff_sum_bare = 0
		Dp_Dcs = []
		for bin_mid in binned_data: #integrate
			Dp_Dcs.append(binned_data[bin_mid]['bin_Dp_Dc'])
			mass_concs_raw_sum = mass_concs_raw_sum + binned_data[bin_mid]['bin_mass_conc'] 
			mass_concs_sum = mass_concs_sum + binned_data[bin_mid]['bin_mass_conc_norm']
			vol_abs_coeff_sum_max  = vol_abs_coeff_sum_max  + binned_data[bin_mid]['bin_vol_abs_coeff_max']
			vol_sca_coeff_sum_max  = vol_sca_coeff_sum_max  + binned_data[bin_mid]['bin_vol_sca_coeff_max']
			vol_abs_coeff_sum_min  = vol_abs_coeff_sum_min  + binned_data[bin_mid]['bin_vol_abs_coeff_min']
			vol_sca_coeff_sum_min  = vol_sca_coeff_sum_min  + binned_data[bin_mid]['bin_vol_sca_coeff_min']
			vol_abs_coeff_sum_bare = vol_abs_coeff_sum_bare + binned_data[bin_mid]['bin_vol_abs_coeff_bare']
		Dp_Dc_mean = np.nanmean(Dp_Dcs)
		MAC_max = vol_abs_coeff_sum_max*(10**11)/mass_concs_sum
		MAC_min = vol_abs_coeff_sum_min*(10**11)/mass_concs_sum
		SSA_max = vol_sca_coeff_sum_max/(vol_abs_coeff_sum_max+vol_sca_coeff_sum_max)
		SSA_min = vol_sca_coeff_sum_min/(vol_abs_coeff_sum_min+vol_sca_coeff_sum_min)	
		AE_max = vol_abs_coeff_sum_max/vol_abs_coeff_sum_bare
		AE_min = vol_abs_coeff_sum_min/vol_abs_coeff_sum_bare
		mass_conc_total = mass_concs_raw_sum/fraction_measured
		
		print mass_conc_total, mass_concs_raw_sum, fraction_measured

		#add overall data to dict	
		mean_alt = lower_alt + alt_incr/2
		if mean_alt not in plot_data:
			plot_data[mean_alt] = {
			'mass_concs'	:[],
			'Dp_Dcs'	    :[],
			'Dgs_mass'		:[],
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
		plot_data[mean_alt]['MAC_maxs'	].append(MAC_max)
		plot_data[mean_alt]['MAC_mins'	].append(MAC_min)
		plot_data[mean_alt]['SSA_maxs'	].append(SSA_max)
		plot_data[mean_alt]['SSA_mins'	].append(SSA_min)
		plot_data[mean_alt]['AE_maxs'	].append(AE_max)
		plot_data[mean_alt]['AE_mins'	].append(AE_min)
		
		lower_alt += alt_incr

cnx.close()
print 'next step . . .'

##
plot_data_list = []

for mean_alt in plot_data:
	mean_Dg = np.mean(plot_data[mean_alt]['Dgs_mass'])
	neg_err_Dg = mean_Dg - np.min(plot_data[mean_alt]['Dgs_mass'])
	pos_err_Dg = np.max(plot_data[mean_alt]['Dgs_mass']) - mean_Dg
	
	mean_sigma = np.mean(plot_data[mean_alt]['sigmas_mass'])
	neg_err_sigma = mean_sigma - np.min(plot_data[mean_alt]['sigmas_mass'])
	pos_err_sigma = np.max(plot_data[mean_alt]['sigmas_mass']) - mean_sigma
	
	mean_mass_conc = np.mean(plot_data[mean_alt]['mass_concs'])
	neg_err_mass_conc = mean_mass_conc - np.min(plot_data[mean_alt]['mass_concs'])
	pos_err_mass_conc = np.max(plot_data[mean_alt]['mass_concs']) - mean_mass_conc
	
	Dp_Dc_mean    = np.nanmean(plot_data[mean_alt]['Dp_Dcs'])
	neg_err_Dp_Dc = Dp_Dc_mean - np.min(plot_data[mean_alt]['Dp_Dcs'])
	pos_err_Dp_Dc = np.max(plot_data[mean_alt]['Dp_Dcs']) - Dp_Dc_mean
	
	mean_MAC_max = 	 np.mean(plot_data[mean_alt]['MAC_maxs'])
	mean_MAC_min = 	 np.mean(plot_data[mean_alt]['MAC_mins'])
	mean_SSA_max = 	 np.mean(plot_data[mean_alt]['SSA_maxs'])
	mean_SSA_min = 	 np.mean(plot_data[mean_alt]['SSA_mins'])
	mean_abs_e_max = np.mean(plot_data[mean_alt]['AE_maxs'])
	mean_abs_e_min = np.mean(plot_data[mean_alt]['AE_mins'])

	
	plot_data_list.append([mean_alt,mean_Dg,neg_err_Dg,pos_err_Dg,mean_sigma,neg_err_sigma,pos_err_sigma,mean_mass_conc,neg_err_mass_conc,pos_err_mass_conc,mean_MAC_max,mean_MAC_min,mean_SSA_max,	mean_SSA_min,mean_abs_e_max,mean_abs_e_min,Dp_Dc_mean,neg_err_Dp_Dc,pos_err_Dp_Dc])
                                                                                                                                                                                                                                                  
plot_data_list.sort()                                                                                                                                                                                                                          
                                                                                                                                                                                                                                               
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
p_mean_SSA_max = [row[12] for row in plot_data_list]
p_mean_SSA_min = [row[13] for row in plot_data_list]
p_mean_ae_max = [row[14] for row in plot_data_list] 
p_mean_ae_min = [row[15] for row in plot_data_list] 
	
p_mean_Dp_Dc = [row[16] for row in plot_data_list]
p_neg_err_Dp_Dc = [row[17] for row in plot_data_list]
p_pos_err_Dp_Dc = [row[18] for row in plot_data_list]


dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/'
os.chdir(dir)
max_alt = 6200            

fig = plt.figure(figsize=(10,10))
                     
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)					
				
ax1.plot(p_mean_MAC_max,altitudes,marker='o',linestyle='-', color = 'b', label = 'coated rBC')
ax1.plot(p_mean_MAC_min,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5, label = 'bare rBC')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel('MAC (m2/g)')
ax1.set_xlim(6,18)
ax1.set_ylim(0,max_alt)

ax2.plot(p_mean_SSA_max,altitudes,marker='o',linestyle='-', color = 'b')
ax2.plot(p_mean_SSA_min,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5)
ax2.set_xlabel('SSA')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(0.4,0.8)
ax2.set_ylim(0,max_alt)

ax3.plot(p_mean_ae_max,altitudes,marker='o',linestyle='-', color = 'b')
ax3.plot(p_mean_ae_min,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5)
ax3.set_xlabel('Abs enhancement')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(1,2)
ax3.set_ylim(0,max_alt)

if savefig == True:
	plt.savefig('MAC SSA AE - 550nm - Sc 1-7 full mass range - using variable coating - neg coats incl as smaller bare cores.png', bbox_inches='tight') 

plt.show()

####

fig = plt.figure(figsize=(10,10))
                  
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)
ax4  = plt.subplot2grid((2,2), (1,1), colspan=1)

ax1.errorbar(p_mean_Dg,altitudes,xerr = [p_neg_err_Dg,p_pos_err_Dg],fmt='o',linestyle='-', color = 'b')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel('Dg (from dM/dlog(D) ng/m3-STP)')
ax1.set_xlim(100,220)
ax1.set_ylim(0,max_alt)

ax2.errorbar(p_mean_sigma,altitudes,xerr = [p_neg_err_sigma,p_pos_err_sigma],fmt='o',linestyle='-', color = 'grey')
ax2.set_xlabel('sigma (from dM/dlog(D) ng/m3-STP)')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(1,2)
ax2.set_ylim(0,max_alt)

ax3.errorbar(p_mean_mass_conc,altitudes,xerr = [p_neg_err_mass_conc,p_pos_err_mass_conc],fmt='o',linestyle='-', color = 'green')
ax3.set_xlabel('total mass conc (ng/m3 - STP)')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(0,100)
ax3.set_ylim(0,max_alt)

ax4.errorbar(p_mean_Dp_Dc,altitudes,xerr=[p_neg_err_Dp_Dc,p_pos_err_Dp_Dc],fmt='o',linestyle='-', color = 'red')
ax4.set_xlabel('Dp/Dc (rBC cores from 160-180nm)')
ax4.set_ylabel('altitude (m)')
ax4.set_xlim(0.8,2.4)
ax4.set_ylim(0,max_alt)

if savefig == True:
	#plt.savefig('altitude dependent plots - '+flight_times[flight][4]+' - cloud-free.png', bbox_inches='tight') 
	plt.savefig('altitude dependent plots Dp sig mass DpDc - sc1-7 - cloud-free.png', bbox_inches='tight') 

plt.show()

