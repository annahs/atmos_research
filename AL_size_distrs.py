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
import calendar
from scipy.optimize import curve_fit


start = datetime(2011,3,5,0)
end = datetime(2014,1,1,0)
interval = 48 #hours
compare_to_PAPI = False
show_plot = False
write_to_file = True
fit_bin_min = 10
fit_bin_max = 1000
bin_incr = 5



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def myRound(x, base):
    return int(base * round(float(x)/base))
	
def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))

def make_bin_dict():
	new_dict = {}

	for bin in range(min_BC_VED,max_BC_VED,bin_incr):
		new_dict[bin] = [bin,(bin+bin_incr),0,0]

	return new_dict
	
def calcuate_VED(bbhg_incand_pk_amp,bblg_incand_pk_amp, instr_id):
	
	VED = np.nan
	if instr_id == '58':
		#HG
		bbhg_mass_uncorr = 0.29069 + 1.49267E-4*bbhg_incand_pk_amp + 5.02184E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  
		bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
			
		#LG
		bblg_mass_uncorr = -0.15884 + 0.00176*bblg_incand_pk_amp + 3.19118E-8*bblg_incand_pk_amp*bblg_incand_pk_amp
		bblg_mass_corr = bblg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
		
		if min_rBC_mass <= bbhg_mass_corr < 12.8:
			VED = (((bbhg_mass_corr/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		elif 12.8 <= bblg_mass_corr < max_rBC_mass:
			VED = (((bblg_mass_corr/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
	
	if instr_id == '44':
		bbhg_mass_uncorr = 0.18821 + 1.36864E-4*bbhg_incand_pk_amp + 5.82331E-10*bbhg_incand_pk_amp*bbhg_incand_pk_amp  #SP244
		bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
				
		if min_rBC_mass <= bbhg_mass_corr < max_rBC_mass:
			VED = (((bbhg_mass_corr/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7

	if instr_id == '17':
		bbhg_mass_uncorr = -0.017584 + 0.00647*bbhg_incand_pk_amp #SP217  
		bbhg_mass_corr = bbhg_mass_uncorr/0.7 #AD correction factor is 0.7 +- 0.05
				
		if min_rBC_mass <= bbhg_mass_corr < max_rBC_mass:
			VED = (((bbhg_mass_corr/(10**15*1.8))*6/math.pi)**(1/3.0))*10**7
		
	return VED

def assemble_interval_data(retrieved_records):
	interval_data_dict = {}
	total_sample_vol = 0
	ved_list = []

	for row in retrieved_records:
		ind_start_time = row[0]
		ind_end_time = row[1]
		bbhg_incand_pk_amp = row[2]
		bblg_incand_pk_amp = row[3]  #for SP2 #17 this field is also bbhg_incand_pk_amp (query is modified since there is no LG channel)
		sample_flow = row[4]  #in vccm
		instr_id = row[5]  
		
		if sample_flow == None:
			continue
		if (ind_end_time-ind_start_time) > 500:  #this accounts for the 10min gaps in sp2#17 sampling (1/10 mins) we wanmt to ignore the particles with the huge sample interval
			continue
			
		sample_vol =  (sample_flow*(ind_end_time-ind_start_time)/60)    #/60 b/c sccm and time in secs  
		total_sample_vol = total_sample_vol + sample_vol
		
		VED = calcuate_VED(bbhg_incand_pk_amp,bblg_incand_pk_amp, instr_id)
		ved_list.append(VED)
	
	interval_data_dict['VED list'] = ved_list
	interval_data_dict['sampled volume'] = total_sample_vol
	interval_data_dict['instr'] = instr_id
	return interval_data_dict
	
def make_binned_list(interval_data_dict):
	raw_dia_list = interval_data_dict['VED list']
	total_vol_sccm = interval_data_dict['sampled volume']
	if total_vol_sccm == 0:
		total_vol_sccm = np.nan
	instr_id = interval_data_dict['instr'] 
	bin_dict = make_bin_dict()
	
	for dia in raw_dia_list:	
		for point in bin_dict:
			LL_bin = bin_dict[point][0]
			UL_bin = bin_dict[point][1]
			if (LL_bin <= dia < UL_bin):
				mass = ((dia/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)			
				if instr_id  == '44':
					for count in range(0,8):
						bin_dict[point][3] += mass
						bin_dict[point][2] += 1
				if instr_id  == '58':
					for count in range(0,10):
						bin_dict[point][3] += mass
						bin_dict[point][2] += 1
				else:
					bin_dict[point][3] += mass
					bin_dict[point][2] += 1
	
	dia_list = []

	for point in bin_dict:
		bin_ll = bin_dict[point][0]
		bin_ul = bin_dict[point][1]
		bin_mid = bin_ll + (bin_ul-bin_ll)/2
		
		number = bin_dict[point][2]
		number_conc = number/total_vol_sccm #in #/cm3
		norm_number_conc = number_conc/(math.log(bin_ul)-math.log(bin_ll))
		
		mass = bin_dict[point][3]
		mass_conc = mass/total_vol_sccm #in #/cm3
		norm_mass_conc = mass_conc/(math.log(bin_ul)-math.log(bin_ll))
		
		dia_list.append([bin_ll,bin_ul,bin_mid,number,number_conc,norm_number_conc,mass,mass_conc,norm_mass_conc,total_vol_sccm])
	dia_list.sort()

	return dia_list
	
def fit_distr(data_to_fit_bins,data_to_fit_concs):
	
	core_bin_midpoints = []
	for bin in data_to_fit_bins:
		if np.isnan(bin) == False:
			core_bin_midpoints.append(bin) 
			
	core_mass_conc_norm = []
	for conc in data_to_fit_concs:
		if np.isnan(conc) == False:
			core_mass_conc_norm.append(conc) 

	#fit 
	try:
		popt, pcov = curve_fit(lognorm, np.array(core_bin_midpoints), np.array(core_mass_conc_norm), p0=(2000,0.6,150))	

	except Exception,e: 
		popt = [np.nan,np.nan,np.nan]
		pcov = [np.nan,np.nan,np.nan]
		print str(e)
		print 'fit failure'
			
	perr = np.sqrt(np.diag(pcov))
	sigma = math.exp(popt[1])
	return [popt, perr,sigma]

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
	print 'std_err_of_estimate: ',std_err_of_estimate
	
	return std_err_of_estimate

def get_PAPI_data():
	
	PAPI_list = []
	data_dir = 'F:/Alert/'+ str(start_time.year) +'/Reduced/' + datetime.strftime(datetime(start_time.year, start_time.month, start_time.day),'%Y%m%d') + '/'  #Alert data is in UTC - see email from Dan Veber
	os.chdir(data_dir)	
	for file in os.listdir('.'):
		if file.endswith('SizeDist.dat'):
			print file
			with open(file, 'r') as f:
				temp = f.read().splitlines()
				first_line = True
				for line in temp:
					if first_line == True:
						first_line = False
						continue
					newline = line.split()
					bin_mid = float(newline[0])*1000
					number = float(newline[1])
					mass = float(newline[2])
					
					print number
					PAPI_list.append([bin_mid,mass,number])
	return PAPI_list

def	write_files(core_bin_mids,core_norm_mass_concs,core_norm_numb_concs,fit_bin_mids,mass_fit_points,numb_fit_points,ratio_uncertainty,mass_fit_sigma):
	
	distr_list = []
	
	i=0
	for fit_bin in fit_bin_mids:
		if fit_bin in core_bin_mids: 
			meas_index = core_bin_mids.index(fit_bin)
			meas_mass_val = core_norm_mass_concs[meas_index]
			meas_numb_val = core_norm_numb_concs[meas_index]
			#print fit_bin,meas_index,meas_mass_val
		else:
			meas_mass_val = np.nan
			meas_numb_val = np.nan
			
		if meas_mass_val == 0:
			meas_mass_val = np.nan
		if meas_numb_val == 0:
			meas_numb_val = np.nan
			
		distr_list.append([fit_bin+0.5,meas_mass_val,mass_fit_points[i],meas_numb_val,numb_fit_points[i]])
		i+=1

	
		
	#mass ratio
	meas_area = np.nansum(core_norm_mass_concs)
	fit_area = np.nansum(mass_fit_points)
	ratio = meas_area/fit_area
	
	file = open('C:/Users/Sarah Hanna/Documents/Data/Alert Data/distributions/mass and number distributions 48hr/rBC distributions for '+str(datetime.date(start_time))+'.txt', 'w')
	file.write('fraction of mass distribution measured (area under measured curve/area under fit curve)= ' + str(ratio) + ' +- ' + str(round(ratio_uncertainty,3)) + '\n') 
	file.write('mass fit sigma: ' + str(mass_fit_sigma) + '\n') 
	file.write('bin_midpoints(nm)\tmeas_mass_conc(dM/dlogD-ng/m3)\tfit_mass_conc(dM/dlogD-ng/m3)\tmeas_number_conc(d/dlogD-#/cm3)\tfit_number_conc(d/dlogD-#/cm3)' + '\n')
	for row in distr_list:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()
	
	
	
def plot_distrs(data_to_fit_bins,data_to_fit_mass_concs,data_to_fit_number_concs,mass_fit_params,number_fit_params,fractions_list,instr_id,total_vol):

	mass_fit_points = []
	mass_fit_points_err = []
	numb_fit_points = []
	fit_bin_mids = []
	
	mass_fit_coefficients = mass_fit_params[0]
	mass_fit_coefficients_err = mass_fit_params[1]
	mass_fit_sigma = mass_fit_params[2]
	number_fit_coefficients = number_fit_params[0]
	
	for bin_mid in range((fit_bin_min+bin_incr/2),fit_bin_max,bin_incr):
		#mass
		try:
			fit_core_mass_conc_norm  = lognorm(bin_mid, mass_fit_coefficients[0], mass_fit_coefficients[1], mass_fit_coefficients[2])
			fit_core_mass_conc_err  = lognorm(bin_mid, mass_fit_coefficients[0]-mass_fit_coefficients_err[0], mass_fit_coefficients[1]-mass_fit_coefficients_err[1], mass_fit_coefficients[2]-mass_fit_coefficients_err[2])
		except: #still need something to plot plot even if fit has failed
			fit_core_mass_conc_norm = np.nan
		
		#number
		try:
			fit_core_numb_conc_norm  = lognorm(bin_mid, number_fit_coefficients[0], number_fit_coefficients[1], number_fit_coefficients[2])
		except: 
			fit_core_numb_conc_norm = np.nan
		
		fit_bin_mids.append(bin_mid)
		mass_fit_points.append(fit_core_mass_conc_norm)
		mass_fit_points_err.append(fit_core_mass_conc_err)
		numb_fit_points.append(fit_core_numb_conc_norm)
		
		
	core_bin_mids = data_to_fit_bins
	core_norm_mass_concs = data_to_fit_mass_concs
	core_norm_numb_concs = data_to_fit_number_concs
	
	std_err_of_est = calc_std_err_of_estimate(data_to_fit_bins,data_to_fit_mass_concs,mass_fit_coefficients)
	
	if compare_to_PAPI == True:
		papi_data = get_PAPI_data()
		papi_bins = [row[0] for row in papi_data]
		papi_masses = [row[1] for row in papi_data]
		papi_number = [row[2] for row in papi_data]
		print total_vol, 'vol'
		
	####
	meas_area = np.nansum(core_norm_mass_concs)
	fit_area = np.nansum(mass_fit_points)
	fit_area_err = np.nansum(mass_fit_points_err)
	ratio = meas_area/fit_area
	ratio_err = meas_area/fit_area_err
	ratio_uncertainty = abs(ratio-ratio_err)
	
	print '**** ratio_uncertainty', ratio_uncertainty
	print 'meas val sum: ',meas_area
	print 'fit val sum: ',fit_area
	print 'fraction of mass: ',ratio
	
	if write_to_file == True:
		write_files(core_bin_mids,core_norm_mass_concs,core_norm_numb_concs,fit_bin_mids,mass_fit_points,numb_fit_points,ratio_uncertainty,mass_fit_sigma)
	fractions_list.append([datetime.date(start_time),ratio,instr_id,std_err_of_est])
	
	if show_plot == True:
		#plots
		ticks = [50,60,70,80,100,120,160,200,300,400,600,800]
		fig = plt.figure(figsize= (12,10))
		ax1 = fig.add_subplot(111)
		ax1.scatter(core_bin_mids,core_norm_mass_concs, color = 'k',marker='o', label='rBC cores only')
		ax1.plot(fit_bin_mids,mass_fit_points, color = 'blue',marker='x', label='fit')
		ax1.scatter(core_bin_mids,core_norm_numb_concs, color = 'black',marker='s', label='rBC cores only')
		ax1.plot(fit_bin_mids,numb_fit_points, color = 'green',marker='x', label='fit')
		if compare_to_PAPI == True:
			#ax1.scatter(papi_bins,papi_masses, color = 'r',marker='o', label='PAPI')
			ax1.scatter(papi_bins,papi_number, color = 'r',marker='s', label='PAPI')
		ax1.set_xlabel('VED (nm)')
		ax1.set_ylabel('dM/dlog(VED)')
		ax1.set_xscale('log')
		#ax1.set_yscale('log')
		ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
		ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
		#ax1.set_ylim(0,10)
		ax1.set_xlim(50,1000)
		plt.legend()
		
		plt.show()
		


	
	
##script
start_time = start	
fractions_list = []
while start_time < end:

	print '\n', start_time, '\n'
	end_time = start_time + timedelta(hours=interval)
	UNIX_start = calendar.timegm(start_time.utctimetuple())
	UNIX_end = calendar.timegm(end_time.utctimetuple())

	#distr parameters
	if start_time >= datetime(2013,9,27,0):  #SP2#58
		min_BC_VED = 85  
		max_BC_VED = 350  
	if datetime(2012,3,27,0) <= start_time < datetime(2013,9,23,0): #SP2#44
		min_BC_VED = 10  
		max_BC_VED = 250  
	if start_time <= datetime(2012,3,24,0): #SP2#17
		min_BC_VED = 10
		max_BC_VED = 245  

	min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
	max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

	table = ' alert_mass_number_data_' + str(start_time.year) + ' '

	###SP2
	start_timing = datetime.now()

	if start_time >= datetime(2012,3,27):  #8channel instrs #44 and #58
		cursor.execute('''(SELECT 
			mn.UNIX_UTC_ts_int_start,
			mn.UNIX_UTC_ts_int_end,
			mn.BB_incand_HG,
			mn.BB_incand_LG,
			hk.sample_flow,
			mn.instrument_ID
			FROM''' + table + '''mn
			FORCE INDEX (distrs)
			JOIN alert_hk_data hk on mn.hk_id = hk.id
			WHERE
			mn.UNIX_UTC_ts_int_start >= %s
			AND mn.UNIX_UTC_ts_int_end < %s
			AND mn.hk_id IS NOT NULL)''',
			(UNIX_start,UNIX_end))

		ind_data = cursor.fetchall()
		
	if start_time <= datetime(2012,3,24):	#4channel instr #17 has no LG channel so fetch HG twice
		cursor.execute('''(SELECT 
			mn.UNIX_UTC_ts_int_start,
			mn.UNIX_UTC_ts_int_end,
			mn.BB_incand_HG,
			mn.BB_incand_HG,	
			hk.sample_flow,
			mn.instrument_ID
			FROM''' + table + '''mn
			FORCE INDEX (distrs)
			JOIN alert_hk_data hk on mn.hk_id = hk.id
			WHERE
			mn.UNIX_UTC_ts_int_start >= %s
			AND mn.UNIX_UTC_ts_int_end < %s
			AND mn.hk_id IS NOT NULL)''',
			(UNIX_start,UNIX_end))

		ind_data = cursor.fetchall()

	if ind_data == []:
		start_time += timedelta(hours=interval)
		continue

	print 'fetched: ', datetime.now()-start_timing 

	#assemble the data for this interval
	interval_data_dictionary = assemble_interval_data(ind_data)
	instr_id = interval_data_dictionary['instr'] 
	
	binned_data_list = make_binned_list(interval_data_dictionary)
	total_vol = np.mean([row[9] for row in binned_data_list])

	#mass fitting
	data_to_fit_bins =  [row[2] for row in binned_data_list]
	data_to_fit_mass_concs = [row[8] for row in binned_data_list]
	mass_fit_params = fit_distr(data_to_fit_bins,data_to_fit_mass_concs)
	
	#number fitting
	data_to_fit_bins = []
	data_to_fit_number_concs = []
	for row in binned_data_list:
		bin_mid = row[2]
		number_conc = row[5]
		if bin_mid >= 80:
			data_to_fit_bins.append(bin_mid)
			data_to_fit_number_concs.append(number_conc)
		else:
			data_to_fit_bins.append(np.nan)
			data_to_fit_number_concs.append(np.nan)
	number_fit_params = fit_distr(data_to_fit_bins,data_to_fit_number_concs)
	number_fit_coefficients = number_fit_params[0]

	plot_distrs(data_to_fit_bins,data_to_fit_mass_concs,data_to_fit_number_concs,mass_fit_params,number_fit_params,fractions_list,instr_id,total_vol)
	
	
	#write_files(binned_data)

	start_time += timedelta(hours=interval)


cnx.close()	

