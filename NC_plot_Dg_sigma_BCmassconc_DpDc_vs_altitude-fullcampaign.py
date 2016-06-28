import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates
from mpl_toolkits.basemap import Basemap
import calendar
from scipy.optimize import curve_fit
from coating_info_from_raw_signal import CoatingData

cloud_droplet_conc = 0.5
savefig = False
show_distr_plots = False
coating_data_from_raw = False
#alt parameters
min_alt = 0
max_alt = 6000
alt_incr = 1000
#coating data parameters
coating_min_BC_VED = 160  
coating_max_BC_VED = 180  
coating_min_rBC_mass = ((coating_min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
coating_max_rBC_mass = ((coating_max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
print coating_min_rBC_mass, coating_max_rBC_mass
#Dg and sigma data parameters
bin_value_min = 80  
bin_value_max = 220  
bin_incr = 10
bin_number_lim = (bin_value_max-bin_value_min)/bin_incr
#constants
R = 8.3144621 # in m3*Pa/(K*mol)
lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor545.lupckl'
#lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-200nmPSLcalib_used_factor446.lupckl'

flight_times = {
'science 1'  : [datetime(2015,4,5,9,43),datetime(2015,4,5,13,48),15.6500, 78.2200, 'Longyearbyen (sc1)']	,	   #longyearbyen
#'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
#'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,31),datetime(2015,4,7,20,48),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
'science 3'  : [datetime(2015,4,8,13,51),datetime(2015,4,8,16,43),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,21,22),-70.338, 82.5014,'Alert (sc2-5)']   ,   #Alert
'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,47),-62.338, 82.0,'Alert (sc2-5)']   ,      #Alert
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,16),-90.9408, 80.5,'Eureka (sc6-7)'] ,	   #eureka
'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,52),-95, 80.1,'Eureka (sc6-7)'] ,          #eureka
##'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,49),-133.7306, 67.1,'Inuvik (sc8-10)'],     #inuvik
#'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,36),-133.7306, 69.3617,'Inuvik (sc8-10)'] ,  #inuvik
#'science 10' : [datetime(2015,4,21,16,07),datetime(2015,4,21,21,24),-131, 69.55,'Inuvik (sc8-10)'],         #inuvik
#
}

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))

fit_bins = []
for x in range (30,800,1):
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
		
		#make data binning dicts for the interval
		mass_binned_data = {}
		number_binned_data = {}
		i = bin_value_min  
		while i < bin_value_max:
			mass_binned_data[i] = []
			number_binned_data[i] = []
			i+=bin_incr
		
		#make arrays to hold data for each alt interval
		total_mass_concs = []
		total_number_concs = []
		Dp_Dc_list = []

		print lower_alt, ' to ' , (lower_alt + alt_incr), 'm'
		
		#get coating data
		cursor.execute(('''SELECT bc.rBC_mass_fg_jancalib, bc.coat_thickness_nm_jancalib, bc.incand_amp, bc.LF_scat_amp 
						   FROM polar6_coating_2015 bc 
						   JOIN polar6_flight_track_details ftd on bc.flight_track_data_id = ftd.id 
						   JOIN polar6_fssp_cloud_data fssp on bc.fssp_id = fssp.id 
						   WHERE ftd.alt >=%s and ftd.alt < %s and bc.rBC_mass_fg >= %s and bc.rBC_mass_fg < %s and bc.particle_type = %s and bc.instrument = %s and bc.UNIX_UTC_ts >= %s and bc.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s'''),
						   (lower_alt,(lower_alt + alt_incr),coating_min_rBC_mass,coating_max_rBC_mass,'incand','UBCSP2',UNIX_start_time,UNIX_end_time,cloud_droplet_conc))

		coating_data = cursor.fetchall()

		no_coats = 0
		coats = []
		for row in coating_data:
			incand_amp = row[2]
			LEO_amp = row[3]
			
			if LEO_amp >= 45000 or LEO_amp < 0:
				continue
			rBC_mass = row[0]
			coat_th = row[1]
			core_VED = (((rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7
			
			if coat_th != None:		
				coats.append(coat_th)
				Dp_Dc = ((2*coat_th)+core_VED)/core_VED
				Dp_Dc_list.append(Dp_Dc)
			else:
				no_coats += 1
				Dp_Dc_list.append(np.nan)
		
		#print no_coats*100./len(coating_data)

		
		#get mass data
		cursor.execute(('''SELECT bnm.70t80,bnm.80t90,bnm.90t100,bnm.100t110,bnm.110t120,bnm.120t130,bnm.130t140,bnm.140t150,bnm.150t160,bnm.160t170,bnm.170t180,bnm.180t190,bnm.190t200,bnm.200t210,bnm.210t220,bnm.sampled_vol,bnm.total_mass, ftd.temperature_C,ftd.BP_Pa 
			FROM polar6_binned_mass_and_sampled_volume_alertcalib bnm 
			JOIN polar6_flight_track_details ftd ON bnm.flight_track_data_id = ftd.id 
			JOIN polar6_fssp_cloud_data fssp on bnm.fssp_id = fssp.id 
			WHERE ftd.alt >=%s and ftd.alt < %s and bnm.UNIX_UTC_ts >= %s and bnm.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s'''),
			(lower_alt,(lower_alt + alt_incr),UNIX_start_time,UNIX_end_time,cloud_droplet_conc))
		mass_data = cursor.fetchall()
		for row in mass_data:
			volume_sampled = row[15]
			total_mass = row[16]
			temperature = row[17] + 273.15 #convert to Kelvin
			pressure = row[18]
			correction_factor_for_STP = (101325/pressure)*(temperature/273)
			
			total_mass_conc_value = total_mass*correction_factor_for_STP/volume_sampled
			total_mass_concs.append(total_mass_conc_value)
			
			#append STP corrected mass conc to dict of binned data
			i=1
			j=bin_value_min
			while i <= bin_number_lim:
				mass_binned_data[j].append(row[i]*correction_factor_for_STP/volume_sampled)
				i+=1
				j+=10			


		#get number data
		cursor.execute(('''SELECT bnn.70t80,bnn.80t90,bnn.90t100,bnn.100t110,bnn.110t120,bnn.120t130,bnn.130t140,bnn.140t150,bnn.150t160,bnn.160t170,bnn.170t180,bnn.180t190,bnn.190t200,bnn.200t210,bnn.210t220,bnn.sampled_vol,bnn.total_number, ftd.temperature_C,ftd.BP_Pa 
			FROM polar6_binned_number_and_sampled_volume_alertcalib bnn 
			JOIN polar6_flight_track_details ftd ON bnn.flight_track_data_id = ftd.id 
			JOIN polar6_fssp_cloud_data fssp on bnn.fssp_id = fssp.id 
			WHERE ftd.alt >=%s and ftd.alt < %s and bnn.UNIX_UTC_ts >= %s and bnn.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s'''),
			(lower_alt,(lower_alt + alt_incr),UNIX_start_time,UNIX_end_time,cloud_droplet_conc))
		number_data = cursor.fetchall()
		for row in number_data:
			volume_sampled = row[15]
			total_number = row[16]
			temperature = row[17] + 273.15 #convert to Kelvin
			pressure = row[18]
			correction_factor_for_STP = (101325/pressure)*(temperature/273)
			
			total_number_conc_value = total_number*correction_factor_for_STP/volume_sampled
			total_number_concs.append(total_number_conc_value)
				
			#append STP corrected number conc to dict of binned data
			i=1
			j=bin_value_min
			while i <= bin_number_lim:
				number_binned_data[j].append(row[i]*correction_factor_for_STP/volume_sampled)
				i+=1
				j+=10		
		
		
	
		#make lists from binned data and sort	
		binned_list = []
		for key in mass_binned_data:	
			binned_list.append([key, np.mean(mass_binned_data[key])])
		binned_list.sort()
		
		number_binned_list = []
		for key in number_binned_data:	
			number_binned_list.append([key, np.mean(number_binned_data[key])])
		number_binned_list.sort()

		##normalize
		for row in binned_list:
			row[1] = row[1]/(math.log((row[0]+10))-math.log(row[0]))
		mass_conc_bins = np.array([row[0] for row in binned_list])
		mass_concs = np.array([row[1] for row in binned_list])
		
		for row in number_binned_list:
			row[1] = row[1]/(math.log(row[0]+10)-math.log(row[0]))
		number_conc_bins = np.array([row[0] for row in number_binned_list])
		number_concs = np.array([row[1] for row in number_binned_list])

		#fit with lognormal
		#get Dg and sigma and write to dict
		
		try:
			popt, pcov = curve_fit(lognorm, mass_conc_bins, mass_concs)	
			fit_y_vals = []
			for bin in fit_bins:
				fit_val = lognorm(bin, popt[0], popt[1], popt[2])
				fit_y_vals.append(fit_val)
			Dg = fit_bins[np.argmax(fit_y_vals)]
		except:
			print 'fit failure'
			Dg = np.nan
		
		#check if the fit is too far off
		if popt[1] > 5 or np.isnan(Dg):
			print 'sigma too high'
			sigma = np.nan
			Dg = np.nan
		else:
			sigma = math.exp(popt[1])
			
		fraction_sampled = sum(fit_y_vals[65:220])/sum(fit_y_vals[65:480])
		
		#add overall data to dict	
		mean_alt = lower_alt + alt_incr/2
		if mean_alt not in plot_data:
			plot_data[mean_alt] = []
		plot_data[mean_alt].append([Dg,sigma,np.mean(total_mass_concs)/fraction_sampled,np.mean(Dp_Dc_list),fraction_sampled,total_number_concs,coats])
		
		
		####plotting	
		if show_distr_plots == True:
			fig = plt.figure()
			ax1 = fig.add_subplot(111)
			ax1.semilogx(number_conc_bins,number_concs, color = 'g',marker='o')
			ax1.semilogx(mass_conc_bins,mass_concs, color = 'b',marker='o')
			ax1.semilogx(fit_bins,fit_y_vals, color = 'r',marker=None)
			plt.ylabel('dM/dlog(VED)')
			ax1.set_xlabel('VED (nm)')
			plt.show()
			
		lower_alt += alt_incr


		
cnx.close()
print 'next step . . .'


##
plot_list = []
for mean_alt in plot_data:
	
	sampled_fraction = [row[4] for row in plot_data[mean_alt]][0]
	
	mean_dg = np.mean([row[0] for row in plot_data[mean_alt]])
	min_dg = mean_dg-np.min([row[0] for row in plot_data[mean_alt]])
	max_dg = np.max([row[0] for row in plot_data[mean_alt]])-mean_dg
	
	mean_sigma = np.mean([row[1] for row in plot_data[mean_alt]])
	min_sigma = mean_sigma-np.min([row[1] for row in plot_data[mean_alt]])
	max_sigma = np.max([row[1] for row in plot_data[mean_alt]])-mean_sigma
	
	mean_mass = np.mean([row[2] for row in plot_data[mean_alt]])
	p25_err = mean_mass-np.min([row[2] for row in plot_data[mean_alt]])
	p75_err = np.max([row[2] for row in plot_data[mean_alt]])-mean_mass
	
	#combined_mass_list = []
	#for row in plot_data[mean_alt]: 
	#	combined_mass_list = combined_mass_list +row[2] #concatenate lists
	#median_mass = np.median(combined_mass_list)/sampled_fraction 
	#p25_err = median_mass-np.percentile(combined_mass_list,25)/sampled_fraction 
	#p75_err = np.percentile(combined_mass_list,75)/sampled_fraction -median_mass
	
	mean_Dp_Dc = np.mean([row[3] for row in plot_data[mean_alt]])
	Dp_Dc_p25_err = mean_Dp_Dc-np.min([row[3] for row in plot_data[mean_alt]])
	Dp_Dc_p75_err = np.max([row[3] for row in plot_data[mean_alt]])-mean_Dp_Dc
	
	#combined_DpDc_list = []
	#for row in plot_data[mean_alt]: 
	#	combined_DpDc_list = combined_DpDc_list +row[3] #concatenate lists
	#median_Dp_Dc = np.median(combined_DpDc_list)
	#Dp_Dc_p25_err = median_Dp_Dc-np.percentile(combined_DpDc_list,25)
	#Dp_Dc_p75_err = np.percentile(combined_DpDc_list,75)-median_Dp_Dc
	
	combined_numb_list = []
	for row in plot_data[mean_alt]: 
		combined_numb_list = combined_numb_list +row[5] #concatenate lists
	median_number_conc = np.median(combined_numb_list)
	number_p25_err = median_number_conc-np.percentile(combined_numb_list,25)
	number_p75_err = np.percentile(combined_numb_list,75)-median_number_conc
	
	combined_coating_list = []
	for row in plot_data[mean_alt]: 
		combined_coating_list = combined_coating_list +row[6] #concatenate lists
	mean_coating = np.mean(combined_coating_list)
	
	plot_list.append([mean_alt,mean_dg,min_dg,max_dg,mean_sigma,min_sigma,max_sigma,mean_mass,p25_err,p75_err,mean_Dp_Dc,Dp_Dc_p25_err,Dp_Dc_p75_err,median_number_conc,number_p25_err,number_p75_err])
	plot_list.sort()
	
	print mean_alt, mean_coating
	
altitudes = [row[0] for row in plot_list]

Dgs_mean = [row[1] for row in plot_list]
Dgs_min_err = [row[2] for row in plot_list]
Dgs_max_err = [row[3] for row in plot_list]

sigmas_mean = [row[4] for row in plot_list]
sigmas_min_err = [row[5] for row in plot_list]
sigmas_max_err = [row[6] for row in plot_list]

mass_med = [row[7] for row in plot_list]
mass_25 = [row[8] for row in plot_list]
mass_75 = [row[9] for row in plot_list]

Dp_Dc_med = [row[10] for row in plot_list]
Dp_Dc_25 = [row[11] for row in plot_list]
Dp_Dc_75 = [row[12] for row in plot_list]

number_med = [row[13] for row in plot_list]
number_25 = [row[14] for row in plot_list]
number_75 = [row[15] for row in plot_list]

fig = plt.figure(figsize=(12,12))
upper_alt = 6500
                  
ax1  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,1), colspan=1)					
ax3  = plt.subplot2grid((2,2), (1,0), colspan=1)
ax4  = plt.subplot2grid((2,2), (1,1), colspan=1)
#ax5  = plt.subplot2grid((3,2), (1,1), colspan=1)

ax1.errorbar(Dgs_mean,altitudes,xerr = [Dgs_min_err,Dgs_max_err],fmt='o',linestyle='-', color = 'b')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel('Dg (from dM/dlog(D) ng/m3-STP)')
ax1.set_xlim(100,220)
ax1.set_ylim(0,upper_alt)

ax2.errorbar(sigmas_mean,altitudes,xerr = [sigmas_min_err,sigmas_max_err],fmt='o',linestyle='-', color = 'grey')
ax2.set_xlabel('sigma (from dM/dlog(D) ng/m3-STP)')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(1,2)
ax2.set_ylim(0,upper_alt)

ax3.errorbar(mass_med,altitudes,xerr = [mass_25,mass_75],fmt='o',linestyle='-', color = 'green')
ax3.set_xlabel('total mass conc (ng/m3 - STP)')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(0,100)
ax3.set_ylim(0,upper_alt)

ax4.errorbar(Dp_Dc_med,altitudes,xerr=[Dp_Dc_25,Dp_Dc_75],fmt='o',linestyle='-', color = 'red')
ax4.set_xlabel('Dp/Dc (rBC cores from 160-180nm)')
ax4.set_ylabel('altitude (m)')
ax4.set_xlim(0.8,2.4)
ax4.set_ylim(0,upper_alt)

#ax5.errorbar(number_med,altitudes,xerr=[number_25,number_75],fmt='o',linestyle='-', color = 'm')
#ax5.set_xlabel('total number conc (#/cm3 - STP)')
#ax5.set_ylabel('altitude (m)')
#ax5.set_xlim(0,50)
#ax5.set_ylim(0,upper_alt)
##ax5.set_xscale('log')

#fig.suptitle('Science Flights 1-7', fontsize=20)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)

if savefig == True:
	#plt.savefig('altitude dependent plots - '+flight_times[flight][4]+' - cloud-free.png', bbox_inches='tight') 
	plt.savefig('altitude dependent plots Dp sig mass DpDc - sc1-7 - cloud-free.png', bbox_inches='tight') 

plt.show()

