import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
import matplotlib.pyplot as plt
import matplotlib.colors
import copy
from scipy.optimize import curve_fit


start_time = datetime(2015,4,5,0,0)
end_time = datetime(2015,4,14,0,0)
min_BC_VED = 70
max_BC_VED = 220
cloud_droplet_conc = 0.5 #threshold droplet conc from FSSP for in-cloud conditions

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
#'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,49),-133.7306, 67.1,'Inuvik (sc8-10)'],     #inuvik
#'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,36),-133.7306, 69.3617,'Inuvik (sc8-10)'] ,  #inuvik
#'science 10' : [datetime(2015,4,21,16,07),datetime(2015,4,21,21,24),-131, 69.55,'Inuvik (sc8-10)'],         #inuvik
#
}


min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)


def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	
#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#make data binning dicts for the interval
fit_bins = []
for x in range (30,800,1):
	fit_bins.append(x)
bin_value_min = 80  
bin_value_max = 220  
bin_incr = 10
bin_number_lim = (bin_value_max-bin_value_min)/bin_incr
mass_binned_data = {}
number_binned_data = {}
i = bin_value_min  
while i < bin_value_max:
	mass_binned_data[i] = []
	number_binned_data[i] = []
	i+=bin_incr

	
for flight in flight_times:
	UNIX_start_time = calendar.timegm(flight_times[flight][0].utctimetuple())
	UNIX_end_time = calendar.timegm(flight_times[flight][1].utctimetuple())
	print flight
	
	
	#get mass data
	cursor.execute(('SELECT bnm.70t80,bnm.80t90,bnm.90t100,bnm.100t110,bnm.110t120,bnm.120t130,bnm.130t140,bnm.140t150,bnm.150t160,bnm.160t170,bnm.170t180,bnm.180t190,bnm.190t200,bnm.200t210,bnm.210t220,bnm.sampled_vol,bnm.total_mass, ftd.temperature_C,ftd.BP_Pa from polar6_binned_mass_and_sampled_volume_alertcalib bnm JOIN polar6_flight_track_details ftd ON bnm.flight_track_data_id = ftd.id JOIN polar6_fssp_cloud_data fssp on bnm.fssp_id = fssp.id WHERE bnm.UNIX_UTC_ts >= %s and bnm.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s'),(UNIX_start_time,UNIX_end_time,cloud_droplet_conc))
	mass_data = cursor.fetchall()
	for row in mass_data:
		volume_sampled = row[15]
		total_mass = row[16]
		temperature = row[17] + 273.15 #convert to Kelvin
		pressure = row[18]
		correction_factor_for_STP = (101325/pressure)*(temperature/273)
		

		#append STP corrected mass conc to dict of binned data
		i=1
		j=bin_value_min
		while i <= bin_number_lim:
			mass_binned_data[j].append(row[i]*correction_factor_for_STP/volume_sampled)
			i+=1
			j+=10			


	#get number data
	cursor.execute(('SELECT bnn.70t80,bnn.80t90,bnn.90t100,bnn.100t110,bnn.110t120,bnn.120t130,bnn.130t140,bnn.140t150,bnn.150t160,bnn.160t170,bnn.170t180,bnn.180t190,bnn.190t200,bnn.200t210,bnn.210t220,bnn.sampled_vol,bnn.total_number, temperature_C,BP_Pa from polar6_binned_number_and_sampled_volume_alertcalib bnn JOIN polar6_flight_track_details ftd ON bnn.flight_track_data_id = ftd.id JOIN polar6_fssp_cloud_data fssp on bnn.fssp_id = fssp.id WHERE bnn.UNIX_UTC_ts >= %s and bnn.UNIX_UTC_ts < %s and fssp.FSSPTotalConc <=%s'),(UNIX_start_time,UNIX_end_time,cloud_droplet_conc))
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
norm_number_concs = [float(i)/max(number_concs) for i in number_concs]

#fit with lognormals
try:
	popt, pcov = curve_fit(lognorm, mass_conc_bins, mass_concs)	
	fit_y_vals = []
	for bin in fit_bins:
		fit_val = lognorm(bin, popt[0], popt[1], popt[2])
		fit_y_vals.append(fit_val)
except Exception,e: 
	print str(e)
	popt, pcov = [[np.nan,np.nan,np.nan],[np.nan,np.nan,np.nan]]

try:
	poptn, pcovn = curve_fit(lognorm, number_conc_bins, number_concs)	
	fit_y_vals_n = []
	for bin in fit_bins:
		fit_val_n = lognorm(bin, poptn[0], poptn[1], poptn[2])
		fit_y_vals_n.append(fit_val_n)
except Exception,e: 
	print str(e)
	poptn, pcovn = [[np.nan,np.nan,np.nan],[np.nan,np.nan,np.nan]]


#check if the fit is too far off
if popt[1] > 5:
	print 'sigma too high'
	sigma = np.nan
else:
	sigma = math.exp(popt[1])

index = fit_y_vals_n.index(max(fit_y_vals_n))

print fit_bins[index]


####plotting	
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.scatter(number_conc_bins,number_concs, color = 'k',marker='o')
ax1.scatter(mass_conc_bins,mass_concs, color = 'b',marker='o')
ax1.plot(fit_bins,fit_y_vals, color = 'b',marker=None, label ='mass')
ax1.plot(fit_bins,fit_y_vals_n, color = 'k',marker=None, label ='number')
ax1.set_xscale('log')
ax1.set_ylabel('d/dlog(VED) #/m3')
ax1.set_xlabel('VED (nm)')
ax1.set_ylim(0,40)
ax1.set_xlim(30,1000)
ax1.set_xticks([30,40,50,60,80,100,150,200,300,400,600,900])
ax1.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
plt.legend()

ax2 = ax1.twinx()
ax2.set_ylim(0,40)
ax2.set_xlim(30,1000)
ax2.set_ylabel('dM/dlog(VED) ng/cm3',color='b')


os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/size distrs/')
#plt.savefig('mass and number distrs -  '+ flight_times[flight][4] +' - cloud-free.png', bbox_inches='tight') 
#plt.savefig('mass and number distrs -  Longyearbyen,Alert,Eureka (sc1-7) - cloud-free.png', bbox_inches='tight') 

plt.show()
	
