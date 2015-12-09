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


flight = 'science 10'
calib_to_use = 'Alert' #Jan or Alert
show_alt_plot = False
show_distr_plots = False
alt_incr = 820
max_alt = 6600
lower_alt = 0
min_BC_VED = 155  #for coating
max_BC_VED = 180  #for coating
R = 8.3144621 # in m3*Pa/(K*mol)

flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200]	,	
'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014]    ,
'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014]    ,
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014]   ,
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0]   ,
'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5] ,
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1] ,
'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1],
'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617] ,
'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55],
}

min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

start_time = flight_times[flight][0]
end_time = flight_times[flight][1]

UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())


bin_value_min = 80  
bin_value_max = 220  
bin_number_lim = (bin_value_max-bin_value_min)/10

	
#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	
fit_bins = []
for x in range (30,800,1):
	fit_bins.append(x)

flight_track = []
plot_data={}
interval_plot_list = []
fractions_sampled = []
upper_alt = lower_alt + alt_incr
while upper_alt <= max_alt:
	#get timestamps for intervals within an altitude range
	cursor.execute(('SELECT UNIX_UTC_ts,alt from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and alt >= %s and alt <%s ORDER BY UNIX_UTC_ts'),(UNIX_start_time,UNIX_end_time,lower_alt,upper_alt))
	flight_track_data = cursor.fetchall()
	print 'alt:', lower_alt, '-', upper_alt	
	if flight_track_data == []:
		lower_alt += alt_incr
		upper_alt += alt_incr
		continue
	mean_alt = lower_alt + alt_incr/2
	
	#get time intervals for this altitude
	interval_list = []
	prev_timestamp = flight_track_data[0][0]
	interval_start = prev_timestamp
	for row in flight_track_data[1:]:
		current_timestamp = row[0]
		alt = row[1]	
		flight_track.append([current_timestamp,alt])
		if current_timestamp - prev_timestamp > 10:
			interval_end = prev_timestamp
			interval_list.append([interval_start,interval_end,lower_alt,upper_alt])
			prev_timestamp = current_timestamp
			interval_start = prev_timestamp
		else:
			prev_timestamp = current_timestamp
			
	interval_end = current_timestamp
	interval_list.append([interval_start,interval_end,lower_alt,upper_alt])
	
	#toss out really short intervals from when plane was fluctuating right around one of our cutoff heights 
	def determine(row):
		int_end = row[1]
		int_start = row[0]
		if (int_end - int_start) > 120:
			return True
		else:
			return False
			
	interval_list[:] = [row for row in interval_list if determine(row)]
	for row in interval_list:
		interval_plot_list.append(row)
	
	#increment alt
	lower_alt += alt_incr
	upper_alt += alt_incr
	
	#make data binning dicts for the interval
	mass_binned_data = {}
	number_binned_data = {}
	
	i = bin_value_min  
	while i < bin_value_max:
		mass_binned_data[i] = []
		number_binned_data[i] = []
		i+=10

	
	#get data for each interval of height
	total_mass_concs = []
	total_number_concs = []
	Dp_Dc_list = []
	for interval in interval_list:
		alt_interval_start_time = interval[0]
		alt_interval_end_time   = interval[1]
		
		#get coating data
		cursor.execute(('SELECT rBC_mass_fg,coat_thickness_nm  from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and rBC_mass_fg >= %s and rBC_mass_fg < %s and particle_type = %s and instrument = %s'),(alt_interval_start_time,alt_interval_end_time,min_rBC_mass,max_rBC_mass,'incand','UBCSP2'))
		coating_data = cursor.fetchall()

		for row in coating_data:
			rBC_mass = row[0]
			coat_th = row[1]
			core_VED = (((rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7
			try:
				Dp_Dc = ((2*coat_th)+core_VED)/core_VED
				Dp_Dc_list.append(Dp_Dc)
			except:
				continue
			
		#get mass data
		if calib_to_use == 'Jan':
			cursor.execute(('SELECT 70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220,sampled_vol,total_mass,UNIX_UTC_ts from polar6_binned_mass_and_sampled_volume_jancalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(alt_interval_start_time,alt_interval_end_time))
		if calib_to_use == 'Alert':
			cursor.execute(('SELECT 70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220,sampled_vol,total_mass,UNIX_UTC_ts from polar6_binned_mass_and_sampled_volume_alertcalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(alt_interval_start_time,alt_interval_end_time))
		
		mass_data = cursor.fetchall()
		
		for row in mass_data:
			timestamp = row[17]
			volume_sampled = row[15]
			total_mass = row[16]
						
			#get T and P for correction to STP
			cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(timestamp-0.5,timestamp+0.5))
			TandP_data = cursor.fetchall()
			temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
			pressure = TandP_data[0][1]
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
		if calib_to_use == 'Jan':
			cursor.execute(('SELECT 70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220,sampled_vol,total_number,UNIX_UTC_ts from polar6_binned_number_and_sampled_volume_jancalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(alt_interval_start_time,alt_interval_end_time))
		if calib_to_use == 'Alert':
			cursor.execute(('SELECT 70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220,sampled_vol,total_number,UNIX_UTC_ts from polar6_binned_number_and_sampled_volume_alertcalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(alt_interval_start_time,alt_interval_end_time))
		number_data = cursor.fetchall()
		
		for row in number_data:
			timestamp = row[17]
			volume_sampled = row[15]
			total_number = row[16]
						
			#get T and P for correction to STP
			cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(timestamp-0.5,timestamp+0.5))
			TandP_data = cursor.fetchall()
			temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
			pressure = TandP_data[0][1]
			correction_factor_for_STP = (101325/pressure)*(temperature/273)
			
			total_number_conc_value = total_number*correction_factor_for_STP/volume_sampled
			total_number_concs.append(total_number_conc_value)
				
			#append STP corrected mass conc to dict of binned data
			i=1
			j=bin_value_min
			while i <= bin_number_lim:
				number_binned_data[j].append(row[i]*correction_factor_for_STP/volume_sampled)
				i+=1
				j+=10		
		
		
	###indented here = data per interval with individual intervals
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
		popt = np.nan
		pcov = np.nan
		try:
			popt, pcov = curve_fit(lognorm, mass_conc_bins, mass_concs)	
		except:
			print 'fit failure'
			continue
		fit_y_vals = []
		for bin in fit_bins:
			fit_val = lognorm(bin, popt[0], popt[1], popt[2])
			fit_y_vals.append(fit_val)
		
		#check if the fit is too far off
		if popt[1] > 5:
			print 'sigma too high'
			continue
			
		#get Dg and sigma and write to dict
		sigma = math.exp(popt[1])
		Dg = fit_bins[np.argmax(fit_y_vals)]

		fraction_sampled = sum(fit_y_vals[65:220])/sum(fit_y_vals[65:480])
		fractions_sampled.append(fraction_sampled)
		#add data to dict
		if mean_alt in plot_data:
			plot_data[mean_alt].append([Dg,sigma,total_mass_concs,Dp_Dc_list,fraction_sampled,total_number_concs])
		else:
			plot_data[mean_alt] = [[Dg,sigma,total_mass_concs,Dp_Dc_list,fraction_sampled,total_number_concs]]

		
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

cnx.close()

print 'mass fraction sampled', np.mean(fractions_sampled)

#plottting
if show_alt_plot == True:
	times = [row[0] for row in flight_track]
	alts = [row[1] for row in flight_track]

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.scatter(times,alts)
	ax1.set_ylabel('altitude (m)')
	ax1.set_xlabel('time')
	ax1.set_ylim(0,6000)
	i=0
	colors=['#ADFF2F'	,'#7FFF00'	,'#7CFC00'	,'#00FF00','#32CD32'	,'#98FB98'	,'#90EE90'	,'#00FA9A'	,'#00FF7F'	,'#3CB371'	,'#2E8B57'	,'#228B22'	,'#008000'	,'#006400'	,'#9ACD32'	,'#6B8E23'	,'#808000'	,'#556B2F'	,'#66CDAA'	,'#8FBC8F'	,'#20B2AA'	,'#008B8B'	,'#008080'	,'#00FFFF'	,'#E0FFFF'	,'#AFEEEE'	,'#7FFFD4'	,'#40E0D0'	,'#48D1CC'	,'#00CED1'	,'#5F9EA0'	,'#4682B4'	,'#B0C4DE'	,'#B0E0E6'	,'#ADD8E6'	,'#87CEEB'	,'#87CEFA'	,'#00BFFF'	,'#1E90FF'	,'#6495ED'	,'#7B68EE'	,'#4169E1'	,'#0000FF'	,'#0000CD'	,'#00008B'	,'#000080'	,'#191970'	,]
	interval_plot_list.sort()
	pprint(interval_plot_list)
	for interval in interval_plot_list:
		start_int_time = interval[0]
		end_int_time = interval[1]
		ax1.axvspan(start_int_time,end_int_time, facecolor=colors[i], alpha=0.5)
		i+=1
	plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)
	ax1.get_xaxis().get_major_formatter().set_scientific(False)
	plt.show()

##
plot_list = []
for mean_alt in plot_data:
	
	sampled_fraction = [row[4] for row in plot_data[mean_alt]][0]

	mean_dg = np.mean([row[0] for row in plot_data[mean_alt]])
	min_dg = mean_dg - np.min([row[0] for row in plot_data[mean_alt]])
	max_dg = np.max([row[0] for row in plot_data[mean_alt]]) - mean_dg
	
	mean_sigma = np.mean([row[1] for row in plot_data[mean_alt]])
	min_sigma = mean_sigma-np.min([row[1] for row in plot_data[mean_alt]])
	max_sigma = np.max([row[1] for row in plot_data[mean_alt]])-mean_sigma
	
	median_mass = np.median([row[2]for row in plot_data[mean_alt]])/sampled_fraction 
	p25_err = median_mass-np.percentile([row[2] for row in plot_data[mean_alt]],25)/sampled_fraction 
	p75_err = np.percentile([row[2] for row in plot_data[mean_alt]],75)/sampled_fraction -median_mass
	
	median_Dp_Dc = np.median([row[3] for row in plot_data[mean_alt]])
	Dp_Dc_p25_err = median_Dp_Dc-np.percentile([row[3] for row in plot_data[mean_alt]],25)
	Dp_Dc_p75_err = np.percentile([row[3] for row in plot_data[mean_alt]],75)-median_Dp_Dc
	
	median_number_conc = np.median([row[4] for row in plot_data[mean_alt]])
	number_p25_err = median_number_conc-np.percentile([row[4] for row in plot_data[mean_alt]],25)
	number_p75_err = np.percentile([row[4] for row in plot_data[mean_alt]],75)-median_number_conc
	
	plot_list.append([mean_alt,mean_dg,min_dg,max_dg,mean_sigma,min_sigma,max_sigma,median_mass,p25_err,p75_err,median_Dp_Dc,Dp_Dc_p25_err,Dp_Dc_p75_err,median_number_conc,number_p25_err,number_p75_err])
	
	plot_list.sort()
	
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

ax1  = plt.subplot2grid((3,2), (0,0), colspan=1)
ax2  = plt.subplot2grid((3,2), (1,0), colspan=1)					
ax3  = plt.subplot2grid((3,2), (0,1), colspan=1)
ax4  = plt.subplot2grid((3,2), (2,0), colspan=1)
ax5  = plt.subplot2grid((3,2), (1,1), colspan=1)

ax1.errorbar(Dgs_mean,altitudes,xerr = [Dgs_min_err,Dgs_max_err],fmt='o',linestyle='-')
ax1.set_ylabel('altitude (m)')
ax1.set_xlabel('Dg (from dM/dlog(D) ng/m3-STP)')
ax1.set_xlim(100,200)
ax1.set_ylim(0,6000)

ax2.errorbar(sigmas_mean,altitudes,xerr = [sigmas_min_err,sigmas_max_err],fmt='o',linestyle='-', color = 'grey')
ax2.set_xlabel('sigma (from dM/dlog(D) ng/m3-STP)')
ax2.set_ylabel('altitude (m)')
ax2.set_xlim(1,2)
ax2.set_ylim(0,6000)

ax3.errorbar(mass_med,altitudes,xerr = [mass_25,mass_75],fmt='o',linestyle='-', color = 'green')
ax3.set_xlabel('total mass conc (ng/m3 - STP)')
ax3.set_ylabel('altitude (m)')
ax3.set_xlim(0,180)
ax3.set_ylim(0,6000)

ax4.errorbar(Dp_Dc_med,altitudes,xerr=[Dp_Dc_25,Dp_Dc_75],fmt='o',linestyle='-', color = 'red')
ax4.set_xlabel('Dp/Dc (rBC cores from 155-180nm)')
ax4.set_ylabel('altitude (m)')
ax4.set_xlim(0.8,2.4)
ax4.set_ylim(0,6000)

ax5.errorbar(number_med,altitudes,xerr=[number_25,number_75],fmt='o',linestyle='-', color = 'm')
ax5.set_xlabel('total number conc (#/cm3 - STP)')
ax5.set_ylabel('altitude (m)')
ax5.set_xlim(0.2,1)
ax5.set_ylim(0,6000)
#ax5.set_xscale('log')

fig.suptitle(flight, fontsize=20)

dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/'
os.chdir(dir)
if calib_to_use == 'Jan':
	plt.savefig('NC - Polar6 - '+flight+' - Dg,Sigma,mass_conc,DpDc vs alt at ' + str(alt_incr) + 'm intervals - Jan calib.png', bbox_inches='tight') 
if calib_to_use == 'Alert':
	plt.savefig('NC - Polar6 - '+flight+' - Dg,Sigma,mass_conc,DpDc vs alt at ' + str(alt_incr) + 'm intervals - Alert calib.png', bbox_inches='tight') 

plt.show()

