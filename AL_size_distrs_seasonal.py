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
import calendar
from scipy.optimize import curve_fit

start = datetime(2011,1,1)
end =  datetime(2012,1,1)
sample_factor = 10

fit_bin_min = 10
bin_incr = 5
fit_bin_max = 1000

def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))

def fit_distr(bin_mids, distr_points):
	bins= []
	concs = []
	i = 0
	for bin in bin_mids:
		if np.isnan(distr_points[i]) == False:
			bins.append(bin)
			concs.append(distr_points[i])
		i+=1
	
	#fit 
	try:
		popt, pcov = curve_fit(lognorm, np.array(bins), np.array(concs), p0=(1000,0.6,150))	

	except Exception,e: 
		popt = [np.nan,np.nan,np.nan]
		pcov = [np.nan,np.nan,np.nan]
		print str(e)
		print 'mass fit failure'

	perr = np.sqrt(np.diag(pcov))		
	return popt
	
def get_fit_data_pts(plot_list):
	
	for row in plot_list:
		fit_coefficients  = row[3]
		fit_bin_mids = []
		fit_points = []
				
		for bin_mid in range((fit_bin_min+bin_incr/2),fit_bin_max,bin_incr):
			#still plot even if fit has failed
			try:
				fit_core_mass_conc_norm  = lognorm(bin_mid+0.5, fit_coefficients[0], fit_coefficients[1], fit_coefficients[2])
			except:
				fit_core_mass_conc_norm = np.nan
			fit_bin_mids.append(bin_mid)
			fit_points.append(fit_core_mass_conc_norm)
			row.append(fit_bin_mids)
			row.append(fit_points)
	
	return plot_list

def calc_number_dist(plot_list):
	list = []
	for row in plot_list:
		season = row[0]
		core_bin_mids = row[1]
		meas_concs = row[2]
		fit_bin_mids = row[4]
		fit_concs = row[5]
		
		bins_to_use = fit_bin_mids
		concs_to_use = fit_concs
		
		calc_numb_vals = []
		i=0
		for conc in concs_to_use:
			bin_mid = bins_to_use[i]
						
			particle_mass = ((bin_mid/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
			number_calc = conc/particle_mass
			
			calc_numb_vals.append(number_calc)
			
			i+=1
			
		fit_coeffs = fit_distr(bins_to_use,calc_numb_vals)
		list.append([season,bins_to_use,calc_numb_vals,fit_coeffs])
	to_plot_list = []
	to_plot_list = get_fit_data_pts(list)
	return to_plot_list
			

def write_files(plot_list,type):
	for row in plot_list:
		season = row[0]
		core_bin_mids = row[1]
		meas_concs = row[2]
		fit_bin_mids = row[4]
		fit_concs = row[5]

		distr_list = []
		i=0
		for fit_bin in fit_bin_mids:
			if (fit_bin+0.5) in core_bin_mids:
				meas_index = core_bin_mids.index(fit_bin+0.5)
				meas_val = meas_concs[meas_index]
			else:
				meas_val = np.nan
				
			if meas_val == 0:
				meas_val = np.nan
				
			distr_list.append([fit_bin+0.5,meas_val,fit_concs[i]])
			i+=1

		
		file = open('C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/'+season+' seasonal rBC '+type+' distribution for 2011-2013.txt', 'w')
		if type == 'mass':
			file.write('bin_midpoints(nm)\tmeas_mass_conc(dM/dlogD-ng/m3)\tfit_mass_conc(dM/dlogD-ng/m3)' + '\n')
		if type == 'number':
			file.write('bin_midpoints(nm)\tmeas_number_conc(dN/dlogD-#/cm3)\tfit_number_conc(dN/dlogD-#/cm3)' + '\n')
		for row in distr_list:
			line = '\t'.join(str(x) for x in row)
			file.write(line + '\n')
		file.close()	
		
	
def plot_distrs(plot_list,type):
	
	colors = ['r','g','b','k','k','k','k']
	ticks = [10,20,30,40,50,60,70,80,100,120,160,200,300,400,500,700,1000]
	fig = plt.figure(figsize= (12,10))
	ax1 = fig.add_subplot(111)
	i= 0
	for row in plot_list:
		season = row[0]
		bin_mids = row[1]
		meas_concs = row[2]
		fit_mids = row[4]
		fit_concs = row[5]
		print '***', season
		print sum(fit_concs)
		
		ax1.scatter(bin_mids,meas_concs, color = colors[i],marker='o', label=season)
		ax1.plot(fit_mids,fit_concs, color = colors[i],marker='')
		i+=1
	ax1.set_xlabel('VED (nm)')
	if type == 'mass':
		ax1.set_ylabel('dM/dlog(VED) ng/m3')
	if type == 'number':
		ax1.set_ylabel('dN/dlog(VED) #/cm3')
	if type == 'volume':
		ax1.set_ylabel('dV/dlog(VED) um3/cm3')
	ax1.set_xscale('log',basex=10)
	#ax1.set_yscale('log')
	ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
	#ax1.set_ylim(0,10)
	ax1.set_xlim(10,1000)
	plt.grid(b=True, which='both', color='grey',linestyle='-')
	plt.legend()

	plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/seaonal rBC '+type+ ' distribution for 2011-2013.png', bbox_inches = 'tight')
	plt.show()
	
def make_seasonal_dict(dict,file):
	with open(file, 'r') as f:
		f.readline()
		f.readline()
		for line in f:
			newline = line.split()
			
			bin_mid = float(newline[0])
			meas_mass_conc = float(newline[1])
			if meas_mass_conc <=0:
				meas_mass_conc = np.nan
			fit_mass_conc = float(newline[2])
			meas_numb_conc = float(newline[3])
			if meas_numb_conc <=0:
				meas_numb_conc = np.nan
			fit_numb_conc = float(newline[4])
			dict[bin_mid].append([meas_mass_conc,fit_mass_conc,meas_numb_conc,fit_numb_conc])

	return dict
	
	
def make_seasonal_dist(season_dict):
	overall_distr = []				
	for bin_mid in season_dict:
		if 70 <= bin_mid < 240:
			bin_ul = bin_mid+2.5
			bin_ll = bin_mid-2.5
			change_log_factor = (math.log(bin_ul)-math.log(bin_ll))/(math.log(bin_ul,10)-math.log(bin_ll,10))
			avg_meas_mass = np.nanmean([row[0]*change_log_factor for row in season_dict[bin_mid]])
			avg_fit_mass  = np.nanmean([row[1]*change_log_factor for row in season_dict[bin_mid]])
			avg_meas_numb = np.nanmean([row[2]*change_log_factor for row in season_dict[bin_mid]])
			avg_fit_numb  = np.nanmean([row[3]*change_log_factor for row in season_dict[bin_mid]])	
			
			avg_rBC_vol = avg_meas_mass*(math.log(bin_ul,10)-math.log(bin_ll,10))*(1e-6)*(1e-9)/1.8 #in cm3/cm3-air
			rad_cm = (bin_mid/2)*(1e-7)
			vol_particle = (4/3)*math.pi*rad_cm**3
			number_calc = avg_rBC_vol/vol_particle
			avg_meas_vol = avg_rBC_vol*1e12/(math.log(bin_ul,10)-math.log(bin_ll,10))#*change_log_factor #convert to um3 from cm3
			
			
			overall_distr.append([bin_mid,avg_meas_mass,avg_fit_mass,avg_meas_numb,avg_fit_numb,avg_meas_vol])
	overall_distr.sort()
	return overall_distr
	
def make_dict():
	SP2_list = {}
	for bin in range(fit_bin_min,fit_bin_max,bin_incr):
		SP2_list[bin+bin_incr/2.] = []
	
	return SP2_list
	
def calc_std_err_of_estimate(data_to_fit_bins,data_to_fit_mass_concs,mass_fit_coefficients):
	comparison_list = []
	i=0
	for bin_mid in data_to_fit_bins:
		norm_mass_conc = data_to_fit_mass_concs[i]
		if norm_mass_conc > 0:
			fit_val = lognorm(bin_mid, mass_fit_coefficients[0], mass_fit_coefficients[1], mass_fit_coefficients[2])
			diff_to_fit = ((norm_mass_conc-fit_val)/norm_mass_conc)**2  #changed to normalize by value here becasue all are on diff scales
			comparison_list.append(diff_to_fit)
		i+=1
		
	std_err_of_estimate = (np.sum(comparison_list)/len(comparison_list))**0.5
	#print 'std_err_of_estimate: ',std_err_of_estimate
	
	return std_err_of_estimate
#####


year_list = [2011,2012,2013]

DJF = make_dict()
MAM = make_dict()
JJA = make_dict()
SON = make_dict()

seasonal_dists = {}

data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/mass and number distributions test/'
os.chdir(data_dir)
for file in os.listdir('.'):
			
	if file.startswith('rBC distributions'):
		file_date = datetime.strptime(file[22:32],'%Y-%m-%d')
		
		if file_date.year in year_list:
			if file_date.month in [12,1,2]:
				DJF = make_seasonal_dict(DJF,file)
			if file_date.month in [3,4,5]:
				MAM = make_seasonal_dict(MAM,file)
			if file_date.month in [6,7,8]:
				JJA = make_seasonal_dict(JJA,file)
			if file_date.month in [9,10,11]:
				SON = make_seasonal_dict(SON,file)	
	
DJF_dist = make_seasonal_dist(DJF)
MAM_dist = make_seasonal_dist(MAM)
JJA_dist = make_seasonal_dist(JJA)
SON_dist = make_seasonal_dist(SON)

seasonal_dists = {}
seasonal_dists['DJF'] = DJF_dist
seasonal_dists['MAM'] = MAM_dist
seasonal_dists['JJA'] = JJA_dist
seasonal_dists['SON'] = SON_dist


to_plot1 = []
to_plot2 = []
to_plot3 = []
for season in seasonal_dists:
	bin_mids = [row[0] for row in seasonal_dists[season]]
	meas_mass_concs = [row[1] for row in seasonal_dists[season]]
	fit_mass_concs = [row[2] for row in seasonal_dists[season]]
	meas_numb_concs = [row[3] for row in seasonal_dists[season]]
	fit_numb_concs = [row[4] for row in seasonal_dists[season]]
	meas_vol_concs = [row[5] for row in seasonal_dists[season]]

	print season
	
	
	
	meas_coeffs_mass = fit_distr(bin_mids,meas_mass_concs)
	meas_coeffs_numb = fit_distr(bin_mids,meas_numb_concs)
	meas_coeffs_vol = fit_distr(bin_mids,meas_vol_concs)
	#fit_coeffs_mass = fit_distr(bin_mids,fit_mass_concs)[0]
	#fit_coeffs_numb = fit_distr(bin_mids,fit_numb_concs)[0]
	
	
	
	print 'mass',calc_std_err_of_estimate(bin_mids,meas_mass_concs,meas_coeffs_mass)
	print 'numb',calc_std_err_of_estimate(bin_mids,meas_numb_concs,meas_coeffs_numb)
	
	to_plot1.append([season,bin_mids,meas_mass_concs,meas_coeffs_mass])
	to_plot2.append([season,bin_mids,meas_numb_concs,meas_coeffs_numb])
	to_plot3.append([season,bin_mids,meas_vol_concs,meas_coeffs_vol])
	#to_plot.append([season,bin_mids,fit_mass_concs,fit_coeffs_mass])
	#to_plot.append([season,bin_mids,fit_numb_concs,fit_coeffs_numb])
	


to_plot1 = get_fit_data_pts(to_plot1)
to_plot2 = get_fit_data_pts(to_plot2)
to_plot3 = get_fit_data_pts(to_plot3)

to_plot_list_calc = calc_number_dist(to_plot1) 

plot_distrs(to_plot1, 'mass')	
plot_distrs(to_plot2, 'number')	
plot_distrs(to_plot_list_calc, 'number')	
plot_distrs(to_plot3, 'volume')	

write_files(to_plot1, 'mass')	
write_files(to_plot_list_calc, 'number')	
write_files(to_plot3, 'volume')	