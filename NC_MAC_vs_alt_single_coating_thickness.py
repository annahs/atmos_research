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

assumed_coating_th = [41,43,44,40,38,40,44,41,38,38] #nm sc1-7
assumed_coating_th = [43,57,50,57,51,47,46,40,30,17] #nm sc10
wavelength = 550  #nm
rBC_RI = complex(2.26,1.26)
savefig = False
show_distr_plots = False
#alt parameters
min_alt = 0
max_alt = 5000
alt_incr = 500
#distr parameters
bin_value_min = 80  
bin_value_max = 220  
bin_incr = 10
bin_number_lim = (bin_value_max-bin_value_min)/bin_incr
#constants
R = 8.3144621 # in m3*Pa/(K*mol)

flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200]	,	
##'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
##'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
#'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014]    ,
#'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014]    ,
#'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014]   ,
#'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0]   ,
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
#'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5] ,
#'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1] ,
#'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1],
#'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617] ,
#'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55],

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
	
#bin and step size for extrapolating to the full distr
fit_bins = []
for x in range (30,1000,1):
	fit_bins.append(x)

plot_data={}
for flight in flight_times:
	print flight
	lower_alt = min_alt
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	
	alt = 0
	while (lower_alt + alt_incr) <= max_alt:
		#make data binning dicts for the interval
		mass_binned_data = {}
		number_binned_data = {}
		i = bin_value_min  
		while i < bin_value_max:
			mass_binned_data[i] = []
			number_binned_data[i] = []
			i+=bin_incr

		#get mass data
		cursor.execute(('SELECT bnm.70t80,bnm.80t90,bnm.90t100,bnm.100t110,bnm.110t120,bnm.120t130,bnm.130t140,bnm.140t150,bnm.150t160,bnm.160t170,bnm.170t180,bnm.180t190,bnm.190t200,bnm.200t210,bnm.210t220,bnm.sampled_vol,bnm.total_mass, ftd.temperature_C,ftd.BP_Pa from polar6_binned_mass_and_sampled_volume_alertcalib bnm join polar6_flight_track_details ftd ON bnm.flight_track_data_id = ftd.id WHERE ftd.alt >=%s and ftd.alt < %s and bnm.UNIX_UTC_ts >= %s and bnm.UNIX_UTC_ts < %s'),(lower_alt,(lower_alt + alt_incr),UNIX_start_time,UNIX_end_time))
		mass_data = cursor.fetchall()
		for row in mass_data:
			volume_sampled = row[15]
			total_mass = row[16]
			temperature = row[17] + 273.15 #convert to Kelvin
			pressure = row[18]
			correction_factor_for_STP = (101325/pressure)*(temperature/273)
			total_mass_conc_value = total_mass*correction_factor_for_STP/volume_sampled
			
			#append STP corrected mass conc to dict of binned data
			i=1
			j=bin_value_min
			while i <= bin_number_lim:
				mass_binned_data[j].append(row[i]*correction_factor_for_STP/volume_sampled)
				i+=1
				j+=10			


		#get number data
		cursor.execute(('SELECT bnn.70t80,bnn.80t90,bnn.90t100,bnn.100t110,bnn.110t120,bnn.120t130,bnn.130t140,bnn.140t150,bnn.150t160,bnn.160t170,bnn.170t180,bnn.180t190,bnn.190t200,bnn.200t210,bnn.210t220,bnn.sampled_vol,bnn.total_number, ftd.temperature_C,ftd.BP_Pa from polar6_binned_number_and_sampled_volume_alertcalib bnn join polar6_flight_track_details ftd ON bnn.flight_track_data_id = ftd.id WHERE ftd.alt >=%s and ftd.alt < %s and bnn.UNIX_UTC_ts >= %s and bnn.UNIX_UTC_ts < %s'),(lower_alt,(lower_alt + alt_incr),UNIX_start_time,UNIX_end_time))
		number_data = cursor.fetchall()
		for row in number_data:
			volume_sampled = row[15]
			total_number = row[16]
			temperature = row[17] + 273.15 #convert to Kelvin
			pressure = row[18]
			correction_factor_for_STP = (101325/pressure)*(temperature/273)
			
			
			#append STP corrected number conc to dict of binned data
			i=1
			j=bin_value_min
			while i <= bin_number_lim:
				number_binned_data[j].append(row[i]*correction_factor_for_STP/volume_sampled)
				i+=1
				j+=10		
		
		
	
		#make lists from binned data and sort	
		binned_list = []
		number_binned_list = []
		for key in mass_binned_data:	
			abs_xsec = MieCalc(wavelength,(key+bin_incr/2),assumed_coating_th[alt])[0]  
			sca_xsec = MieCalc(wavelength,(key+bin_incr/2),assumed_coating_th[alt])[1]
			abs_xsec_bare = MieCalc(wavelength,(key+bin_incr/2),0)[0]
			sca_xsec_bare = MieCalc(wavelength,(key+bin_incr/2),0)[1]
			binned_list.append([(key+bin_incr/2), np.mean(mass_binned_data[key]), np.mean(number_binned_data[key]), abs_xsec,sca_xsec, abs_xsec_bare,sca_xsec_bare])	
		binned_list.sort()

		
		#optical constants for the measured mass range
		optical_data_meas = []
		for row in binned_list:
			row[1] = row[1]/(math.log((row[0]+bin_incr/2))-math.log(row[0]-bin_incr/2)) #normalize mass
			row[2] = row[2]/(math.log((row[0]+bin_incr/2))-math.log(row[0]-bin_incr/2)) #normalize number
			
			bin_midpoint = row[0]
			bin_mass = row[1]  #in fg/cm3
			bin_number = row[2] #in #/cm3
			bin_abs_xsec = row[3]   #in cm2
			bin_sca_xsec = row[4]   #in cm2
			bin_abs_xsec_bare = row[5]   #in cm2
			bin_sca_xsec_bare = row[6]   #in cm2
			vol_abs_coeff = bin_number*bin_abs_xsec  #in cm-1
			vol_sca_coeff = bin_number*bin_sca_xsec  #in cm-1
			vol_abs_coeff_bare = bin_number*bin_abs_xsec_bare  #in cm-1
			vol_sca_coeff_bare = bin_number*bin_sca_xsec_bare  #in cm-1
			
			mass_abs_coeff_int = (vol_abs_coeff)/bin_mass  #in cm2/fg
			mass_abs_coeff = mass_abs_coeff_int*(10**11)  #in m2/g
			
			optical_data_meas.append([bin_midpoint,bin_mass,bin_number,vol_abs_coeff,vol_sca_coeff,vol_abs_coeff_bare,vol_sca_coeff_bare])

		bin_midpoints = np.array([row[0] for row in optical_data_meas])
		mass_concs = [row[1] for row in optical_data_meas]
		mass_concs_sum = np.sum([row[1] for row in optical_data_meas])
		number_concs = np.array([row[2] for row in optical_data_meas])
		vol_abs_coeff_sum = np.sum([row[3] for row in optical_data_meas])
		vol_sca_coeff_sum = np.sum([row[4] for row in optical_data_meas])
		vol_abs_coeff_sum_bare = np.sum([row[5] for row in optical_data_meas])
		vol_sca_coeff_sum_bare = np.sum([row[6] for row in optical_data_meas])
		MAC_meas = vol_abs_coeff_sum*(10**11)/mass_concs_sum
		SSA_meas = vol_sca_coeff_sum/(vol_sca_coeff_sum+vol_abs_coeff_sum)
		MAC_meas_bare = vol_abs_coeff_sum_bare*(10**11)/mass_concs_sum
		SSA_meas_bare = vol_sca_coeff_sum_bare/(vol_sca_coeff_sum_bare+vol_abs_coeff_sum_bare)
		abs_enhancement_meas = vol_abs_coeff_sum/vol_abs_coeff_sum_bare
		
		#fit mass distr with lognormal
		#get Dg and sigma and write to dict
		try:
			popt, pcov = curve_fit(lognorm, bin_midpoints, mass_concs)	
			fit_binned_mass_concs = []
			for bin in fit_bins:
				fit_val = lognorm(bin, popt[0], popt[1], popt[2])
				fit_binned_mass_concs.append([bin,fit_val])
		except:
			print 'fit failure'
		
					
		#fit number distr with lognormal
		try:
			popt, pcov = curve_fit(lognorm, bin_midpoints, number_concs)
			fit_binned_number_concs = []
			fit_binned_mass_concs_c = []
			for bin in fit_bins:
				fit_val = lognorm(bin, popt[0], popt[1], popt[2])
				fit_binned_number_concs.append([bin,fit_val])
		except:
			print 'fit failure'
		
		#optical constants for the extrapolated (from fit) full mass range
		i=0
		optical_data = []
		for row in fit_binned_number_concs:	
			bin_midpoint = row[0]
			bin_mass = fit_binned_mass_concs[i][1]  #in fg/cm3
			bin_number = row[1] #in #/cm3
			abs_xsec = MieCalc(wavelength,bin_midpoint,assumed_coating_th[alt])[0]
			sca_xsec = MieCalc(wavelength,bin_midpoint,assumed_coating_th[alt])[1]
			abs_xsec_bare = MieCalc(wavelength,bin_midpoint,0)[0]
			sca_xsec_bare = MieCalc(wavelength,bin_midpoint,0)[1]
			vol_abs_coeff = bin_number*abs_xsec  #in cm-1
			vol_sca_coeff = bin_number*sca_xsec  #in cm-1
			vol_abs_coeff_bare = bin_number*abs_xsec_bare  #in cm-1
			vol_sca_coeff_bare = bin_number*sca_xsec_bare  #in cm-1
			
			mass_abs_coeff_int = (vol_abs_coeff)/bin_mass  #in cm2/fg
			mass_abs_coeff = mass_abs_coeff_int*(10**11)  #in m2/g
			
			optical_data.append([bin_mass,vol_abs_coeff,vol_sca_coeff,vol_abs_coeff_bare,vol_sca_coeff_bare,bin_midpoint])
			i+=1
			
		mass_concs_sum_calc = np.sum([row[0] for row in optical_data])
		vol_abs_coeff_sum_calc = np.sum([row[1] for row in optical_data])
		vol_sca_coeff_sum_calc = np.sum([row[2] for row in optical_data])
		vol_abs_coeff_sum_calc_bare = np.sum([row[3] for row in optical_data])
		vol_sca_coeff_sum_calc_bare = np.sum([row[4] for row in optical_data])
		MAC_calc = vol_abs_coeff_sum_calc*(10**11)/mass_concs_sum_calc
		SSA_calc = vol_sca_coeff_sum_calc/(vol_sca_coeff_sum_calc+vol_abs_coeff_sum_calc)
		MAC_calc_bare = vol_abs_coeff_sum_calc_bare*(10**11)/mass_concs_sum_calc
		SSA_calc_bare = vol_sca_coeff_sum_calc_bare/(vol_sca_coeff_sum_calc_bare+vol_abs_coeff_sum_calc_bare)
		abs_enhancement_calc = vol_abs_coeff_sum_calc/vol_abs_coeff_sum_calc_bare
		
		
		#add overall data to dict	
		mean_alt = lower_alt + alt_incr/2
		print mean_alt
		if mean_alt in plot_data:
			plot_data[mean_alt].append([MAC_calc,SSA_calc,MAC_calc_bare,SSA_calc_bare,MAC_meas,SSA_meas,MAC_meas_bare,SSA_meas_bare,abs_enhancement_meas,abs_enhancement_calc])
		else:
			plot_data[mean_alt] = [[MAC_calc,SSA_calc,MAC_calc_bare,SSA_calc_bare,MAC_meas,SSA_meas,MAC_meas_bare,SSA_meas_bare,abs_enhancement_meas,abs_enhancement_calc]]
		
		####plotting distrs if desired	
		fit_binned_mass_conc_vals = [row[1] for row in fit_binned_mass_concs]
		fit_binned_number_conc_vals = [row[1] for row in fit_binned_number_concs]
		if show_distr_plots == True:
			fig = plt.figure()
			ax1 = fig.add_subplot(111)
			ax1.semilogx(bin_midpoints,number_concs, color = 'g',marker='o')
			ax1.semilogx(bin_midpoints,mass_concs, color = 'b',marker='o')
			ax1.semilogx(fit_bins,fit_binned_mass_conc_vals, color = 'b',marker=None)
			ax1.semilogx(fit_bins,fit_binned_number_conc_vals, color = 'g',marker=None)
			plt.ylabel('dM/dlog(VED)')
			ax1.set_xlabel('VED (nm)')
			plt.show()
			
		lower_alt += alt_incr
		alt += 1
cnx.close()
print 'next step . . .'


##
plot_list = []
for mean_alt in plot_data:
	mean_MAC_calc = np.mean([row[0] for row in plot_data[mean_alt]])
	min_MAC_calc = mean_MAC_calc - np.min([row[0] for row in plot_data[mean_alt]])
	max_MAC_calc = np.max([row[0] for row in plot_data[mean_alt]]) - mean_MAC_calc

	mean_SSA_calc = np.mean([row[1] for row in plot_data[mean_alt]])
	min_SSA_calc = mean_SSA_calc - np.min([row[1] for row in plot_data[mean_alt]])
	max_SSA_calc = np.max([row[1] for row in plot_data[mean_alt]]) - mean_SSA_calc

	mean_MAC_calc_bare = np.mean([row[2] for row in plot_data[mean_alt]])
	min_MAC_calc_bare = mean_MAC_calc_bare - np.min([row[2] for row in plot_data[mean_alt]])
	max_MAC_calc_bare = np.max([row[2] for row in plot_data[mean_alt]]) - mean_MAC_calc_bare

	mean_SSA_calc_bare = np.mean([row[3] for row in plot_data[mean_alt]])
	min_SSA_calc_bare = mean_SSA_calc_bare - np.min([row[3] for row in plot_data[mean_alt]])
	max_SSA_calc_bare = np.max([row[3] for row in plot_data[mean_alt]]) - mean_SSA_calc_bare
	
	mean_MAC_meas = np.mean([row[4] for row in plot_data[mean_alt]])
	min_MAC_meas = mean_MAC_meas - np.min([row[4] for row in plot_data[mean_alt]])
	max_MAC_meas = np.max([row[4] for row in plot_data[mean_alt]]) - mean_MAC_meas
	
	mean_SSA_meas = np.mean([row[5] for row in plot_data[mean_alt]])
	min_SSA_meas = mean_SSA_meas - np.min([row[5] for row in plot_data[mean_alt]])
	max_SSA_meas = np.max([row[5] for row in plot_data[mean_alt]]) - mean_SSA_meas

	mean_MAC_meas_bare = np.mean([row[6] for row in plot_data[mean_alt]])
	min_MAC_meas_bare = mean_MAC_meas_bare - np.min([row[6] for row in plot_data[mean_alt]])
	max_MAC_meas_bare = np.max([row[6] for row in plot_data[mean_alt]]) - mean_MAC_meas_bare
	
	mean_SSA_meas_bare = np.mean([row[7] for row in plot_data[mean_alt]])
	min_SSA_meas_bare = mean_SSA_meas_bare - np.min([row[7] for row in plot_data[mean_alt]])
	max_SSA_meas_bare = np.max([row[7] for row in plot_data[mean_alt]]) - mean_SSA_meas_bare

	mean_abse_meas = np.mean([row[8] for row in plot_data[mean_alt]])
	mean_abse_calc = np.mean([row[9] for row in plot_data[mean_alt]])

	
	
	plot_list.append([mean_alt,mean_MAC_calc,mean_SSA_calc,mean_MAC_calc_bare,mean_SSA_calc_bare,mean_MAC_meas,mean_SSA_meas,mean_MAC_meas_bare,mean_SSA_meas_bare,mean_abse_calc,mean_abse_meas])
	plot_list.sort()
	
altitudes = [row[0] for row in plot_list]
MAC_calc_mean = [row[1] for row in plot_list]
SSA_calc_mean = [row[2] for row in plot_list]
MAC_calc_mean_bare = [row[3] for row in plot_list]
SSA_calc_mean_bare = [row[4] for row in plot_list]
MAC_meas_mean = [row[5] for row in plot_list]
SSA_meas_mean = [row[6] for row in plot_list]
MAC_meas_mean_bare = [row[7] for row in plot_list]
SSA_meas_mean_bare = [row[8] for row in plot_list]
mean_abse_calc = [row[9] for row in plot_list]
mean_abse_meas = [row[10] for row in plot_list]


fig = plt.figure(figsize=(10,10))
                         
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)					
				


ax1.plot(MAC_calc_mean,altitudes,marker='o',linestyle='-', color = 'b', label = 'coated rBC')
ax1.plot(MAC_calc_mean_bare,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5, label = 'bare rBC')
#ax1.plot(MAC_meas_mean,altitudes,marker='o',linestyle='-', color = 'r', label = 'coated rBC')
#ax1.plot(MAC_meas_mean_bare,altitudes,marker='o',linestyle='--', color = 'r',alpha = 0.5, label = 'bare rBC')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel('MAC (m2/g)')
ax1.set_xlim(5,18)
ax1.set_ylim(0,5000)

handles, labels = ax1.get_legend_handles_labels()
ax1.legend(handles, labels,loc=7)

ax2.plot(SSA_calc_mean,altitudes,marker='o',linestyle='-', color = 'b')
ax2.plot(SSA_calc_mean_bare,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5)
#ax2.plot(SSA_meas_mean,altitudes,marker='o',linestyle='-', color = 'r')
#ax2.plot(SSA_meas_mean_bare,altitudes,marker='o',linestyle='--', color = 'r',alpha = 0.5)
ax2.set_xlabel('SSA')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(0.38,0.5)
ax2.set_ylim(0,5000)

#ax3.plot(SSA_calc_mean,altitudes,marker='o',linestyle='-', color = 'b')
#ax3.plot(SSA_calc_mean_bare,altitudes,marker='o',linestyle='--', color = 'b',alpha = 0.5)
ax3.plot(mean_abse_calc,altitudes,marker='o',linestyle='-', color = 'b')
#ax3.plot(mean_abse_meas,altitudes,marker='o',linestyle='-', color = 'r')
ax3.set_xlabel('absorption enhancement')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(1.3,1.7)
ax3.set_ylim(0,5000)



dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

if savefig == True:
	plt.savefig('MAC SSA abs enhancement - Sc 1-7 full mass range.png', bbox_inches='tight') 

plt.show()

