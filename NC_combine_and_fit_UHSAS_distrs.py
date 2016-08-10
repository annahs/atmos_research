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
'science 1'  : [datetime(2015,4,5,9,0),  datetime(2015,4,5,14,0) ,''],	
#'ferry 1'    : [datetime(2015,4,6,9,0),  datetime(2015,4,6,11,0) ,'UHSAS_Polar6_20150406_R1_V1.ict'],  
#'ferry 2'    : [datetime(2015,4,6,15,0), datetime(2015,4,6,18,0) ,'UHSAS_Polar6_20150406_R1_V2.ict'],
'science 2'  : [datetime(2015,4,7,16,0), datetime(2015,4,7,21,0) ,'UHSAS_Polar6_20150407_R1_V1.ict'],
'science 3'  : [datetime(2015,4,8,13,0), datetime(2015,4,8,17,0) ,'UHSAS_Polar6_20150408_R1_V1.ict'],  
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0) ,'UHSAS_Polar6_20150408_R1_V2.ict'],
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0) ,'UHSAS_Polar6_20150409_R1_V1.ict'],
###'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),'UHSAS_Polar6_20150410_R1_V1.ict'],
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
		bin_list = []
		i=0
		for LL_limit in bin_LL_line:
			bin_list.append([float(LL_limit),float(bin_UL_line[i])])
			i+=1
		
		return bin_list


def fit_distrs(binned_data_dict,bin_increment):
	#create bin and step size for extrapolating to the full distr
	fit_bins = []
	for x in range(fit_bin_min,fit_bin_max,bin_increment):
		fit_bins.append(x)
	
	fit_concs = {}
	number_distr = []

	#fit the number binned data so we can extrapolate outside of the detection range
	for key in binned_data_dict:	
		number  = binned_data_dict[key]
		if key >=70:
			number_distr.append([key,number])
	
	number_distr.sort()
	pprint(number_distr)
	bin_midpoints  = [row[0] for row in number_distr]
	number_concs  = [row[1] for row in number_distr]
	
	#core
	try:
		popt, pcov = curve_fit(lognorm, np.array(bin_midpoints), np.array(number_concs))	
		for bin_val in fit_bins:
			fit_core_val = lognorm(bin_val, popt[0], popt[1], popt[2])
			fit_concs[bin_val] = fit_core_val
	except Exception,e: 
		for bin_val in fit_bins:
			fit_concs[bin_val]= np.nan
		print str(e)
		print 'number fit failure'
	

	fitted_data = []
	for key,val in fit_concs.iteritems():
		fitted_data.append([key, val])
	fitted_data.sort()
		
	return fitted_data
	



def get_overall_averages(list_of_lists):
	avgs_list = []
	avg_dict = {}
	for item in list_of_lists:
		for item in list:
			bin = item[0]
			number = item[1]
			if bin in avg_dict:
				avg_dict[bin].append(number)
			else:
				avg_dict[bin] = [number]
	
	for bin in avg_dict:
		avgs_list.append([bin,np.mean(avg_dict[bin])])
		
	return avgs_list
		
def plot_distrs(fitted_points,data_points):

		
		
		
		
	data_bin_midpoints  = [row[0] for row in data_points]
	data_number_concs  = [row[1] for row in data_points]
	
	fit_bin_midpoints  = [row[0] for row in fitted_points]
	fit_number_concs  = [row[1] for row in fitted_points]
	
	#plots
	ticks = [50,60,70,80,100,120,160,200,300,400,600,800]
	fig = plt.figure(figsize= (12,10))
	ax1 = fig.add_subplot(111)
	ax1.plot(data_bin_midpoints,data_number_concs, color = 'k',marker='o', label='UHSAS')
	ax1.plot(fit_bin_midpoints,fit_number_concs, color = 'grey',marker=None, label = 'fit')	
	ax1.set_xlabel('VED (nm)')
	ax1.set_ylabel('dN/dlog(VED)')
	ax1.set_xscale('log')
	#ax1.set_yscale('log')
	ax1.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
	ax1.xaxis.set_major_locator(plt.FixedLocator(ticks))
	#ax1.set_ylim(0,35)
	ax1.set_xlim(50,1000)
	plt.legend()
	
	plt.show()
	
	
	
######  start script  ########	
all_fits = []
for flight in flight_times:
	UHSAS_list = []
	
	start_time = flight_times[flight][0]
	end_time = flight_times[flight][1]
	UNIX_start_time = calendar.timegm(start_time.utctimetuple())
	UNIX_end_time = calendar.timegm(end_time.utctimetuple())
	UHSAS_file = flight_times[flight][2]
	
	if UHSAS_file == '':
		continue
	bin_list = getUHSASBins(UHSAS_file)

	#get number concs for each bin
	for bin in bin_list:
		bin_LL =  bin[0]
		bin_UL =  bin[1]

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
			UHSAS_number_mean_norm = UHSAS_number_mean*1.0/(math.log((bin_UL))-math.log(bin_LL))
			UHSAS_list.append([bin_LL,bin_UL,bin_MP,UHSAS_number_mean,UHSAS_number_mean_norm])
			
	UHSAS_list.sort()
	file = open('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating data/UHSAS distr-'+flight+'.txt', 'w')

	file.write('bin_LL\tbin_UL\tbin_mid\tbin_number_conc\tbin_number_conc_norm' + '\n')
	for row in UHSAS_list:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()	
	
	
sys.exit()	
	#UHSAS_fit = fit_distrs(UHSAS_dict, bin_incr)
	#all_fits.append(UHSAS_fit)
	
UHSAS_avg_distr = get_overall_averages(all_fits)
plot_distrs(UHSAS_fit,UHSAS_avg_distr)


	
cnx.close()
##############	



