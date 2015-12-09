import sys
import os
import numpy as np
from scipy import stats
from pprint import pprint
from datetime import datetime
from datetime import timedelta
from datetime import date
import mysql.connector
import pickle
import math
import calendar
import matplotlib.pyplot as plt
import matplotlib.colors
from mpl_toolkits.basemap import Basemap
from matplotlib import dates
import copy
from create_icartt_format_file import CreateIcarttFile
from math import log10, floor

flight = 'science 10'
upper_conc_limit = 300
dropout_limit = 0.0
plot_corr_data = True
plot_numb_data = False
time_incr =	 30#in secs
calib_to_use = 'Alert'
write_icartt_file = False
save_plot = False

#last number is fraction of mass distr sampled rel to AWI
flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200		,0.73]	,	
'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200		,0.72]     ,     #**
'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000	,0.72]   ,       #**
'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014	,0.72]    ,      #**
'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014	,0.63]    ,
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014	,0.68]   ,
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0		,0.65]   ,
'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81		,0.64]  ,
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5	,0.66] ,
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1			,0.69] ,
'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1	,0.72],
'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617	,0.67] ,
'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55		,0.64],
'all' 		 : [datetime(2015,4,5,9,0),datetime(2015,4,21,22,0),-131, 69.55		    ,0.68],
}


fraction_sampled = flight_times[flight][4]
start_time = flight_times[flight][0]
end_time = flight_times[flight][1]

UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())

data_start_day = datetime(start_time.year, start_time.month, start_time.day)
UNIX_start_day = calendar.timegm(data_start_day.utctimetuple())

#optional hk parameters to limit retrieved records to periods where instrument was stable
yag_min = 2.8
yag_max = 6.0
sample_flow_min = 100
sample_flow_max = 200
sheath_flow_min = 400
sheath_flow_max = 800


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

UNIX_interval_start = UNIX_start_time
UNIX_interval_end = UNIX_interval_start + time_incr

sig_figs_SP2 = 5
def round_to_n(x,n):
	if x == 0:
		return 0.0
	elif x < 0:
		return np.nan
	else:
		return round(x, -int(floor(log10(x))) + (n - 1))

icartt_data = []
plot_data = []
first_interval = True
while UNIX_interval_end <= UNIX_end_time:
	
	#check hk values
	cursor.execute(('SELECT sample_flow,yag_power,sheath_flow,yag_xtal_temp from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
	hk_data = cursor.fetchall()
	if hk_data == []:
		UNIX_interval_start += time_incr
		UNIX_interval_end += time_incr
		continue
		

	mean_sample_flow  = np.mean([row[0] for row in hk_data])
	mean_yag_power    = np.mean([row[1] for row in hk_data])
	mean_sheath_flow  = np.mean([row[2] for row in hk_data])
	mean_yag_xtal_temp= np.mean([row[3] for row in hk_data])

	
	#get data from intervals with good average hk parameters
	if (yag_min <= mean_yag_power <= yag_max) and (sample_flow_min <= mean_sample_flow <= sample_flow_max) and (sheath_flow_min <= mean_sheath_flow <= sheath_flow_max):
		
		
		########get the UBC mass conc data
		if calib_to_use == 'Jan':
			cursor.execute(('SELECT UNIX_UTC_ts,total_mass,sampled_vol,interval_start, interval_end,70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220 from polar6_binned_mass_and_sampled_volume_jancalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		if calib_to_use == 'Alert':
			cursor.execute(('SELECT UNIX_UTC_ts,total_mass,sampled_vol,interval_start, interval_end,70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220 from polar6_binned_mass_and_sampled_volume_alertcalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		mass_conc_data = cursor.fetchall()
			
		if mass_conc_data == []:
			UNIX_interval_start += time_incr
			UNIX_interval_end += time_incr
			continue
		
		temp_list = []
		mass_conc_list = []
		for row in mass_conc_data:
			UNIX_ts = row[0]
			mass = row[1] 
			volume = row[2]
			raw_mass_conc = mass/volume
			sampling_period_start = round((row[3] - UNIX_start_day),4) #converts unix utc ts to seconds since midnight of data start day
			sampling_period_end = round((row[4] - UNIX_start_day),4)
				

			
			#get T and P for correction to STP
			cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_ts-0.5,UNIX_ts+0.5))
			TandP_data = cursor.fetchall()
			if TandP_data == []:
				STPcorr_mass_conc = np.nan	
			else:
				temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
				pressure = TandP_data[0][1]
				correction_factor_for_STP = (101325/pressure)*(temperature/273)
				STPcorr_mass_conc = raw_mass_conc*correction_factor_for_STP
				
			mass_conc_list.append([UNIX_ts,STPcorr_mass_conc,raw_mass_conc])
						
			temp_list.append([
				sampling_period_start,
				sampling_period_end,
				round_to_n(volume,sig_figs_SP2),
				round_to_n(mass/1000,sig_figs_SP2),	#/1000 => in ug!
				round_to_n(row[5]/1000,sig_figs_SP2),  #70 to 80 binned mass
				round_to_n(row[6]/1000,sig_figs_SP2),  #80 to 90 binned mass
				round_to_n(row[7]/1000,sig_figs_SP2),  #90 to 100 binned mass
				round_to_n(row[8]/1000,sig_figs_SP2),  #100 to 110 binned mass
				round_to_n(row[9]/1000,sig_figs_SP2),  #110 to 120 binned mass
				round_to_n(row[10]/1000,sig_figs_SP2), #120 to 130 binned mass
				round_to_n(row[11]/1000,sig_figs_SP2), #130 to 140 binned mass
				round_to_n(row[12]/1000,sig_figs_SP2), #140 to 150 binned mass
				round_to_n(row[13]/1000,sig_figs_SP2), #150 to 160 binned mass
				round_to_n(row[14]/1000,sig_figs_SP2), #160 to 170 binned mass
				round_to_n(row[15]/1000,sig_figs_SP2), #170 to 180 binned mass
				round_to_n(row[16]/1000,sig_figs_SP2), #180 to 190 binned mass
				round_to_n(row[17]/1000,sig_figs_SP2), #190 to 200 binned mass
				round_to_n(row[18]/1000,sig_figs_SP2), #200 to 210 binned mass
				round_to_n(row[19]/1000,sig_figs_SP2), #210 to 220 binned mass
				])

		UBC_mean_STPcorr_mass_conc = np.mean([row[1] for row in mass_conc_list])
		UBC_mean_raw_mass_conc = np.mean([row[2] for row in mass_conc_list])
		UBC_mean_ts = math.floor(np.mean([row[0] for row in mass_conc_list]))  #should give us the interval start or midtime :)
		
		#weird dropouts in UBC SP2 . . . . 
		if UBC_mean_raw_mass_conc <=dropout_limit:
			UBC_mean_raw_mass_conc = np.nan
		if UBC_mean_STPcorr_mass_conc <=dropout_limit:
			UBC_mean_STPcorr_mass_conc = np.nan
		
		#####get the UBC number conc data
		if calib_to_use == 'Jan':
			cursor.execute(('SELECT UNIX_UTC_ts,total_number,sampled_vol,interval_start, interval_end,70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220 from polar6_binned_number_and_sampled_volume_jancalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		if calib_to_use == 'Alert':
			cursor.execute(('SELECT UNIX_UTC_ts,total_number,sampled_vol,interval_start, interval_end,70t80,80t90,90t100,100t110,110t120,120t130,130t140,140t150,150t160,160t170,170t180,180t190,190t200,200t210,210t220 from polar6_binned_number_and_sampled_volume_alertcalib where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		number_conc_data = cursor.fetchall()
		
		if number_conc_data == []:
			UNIX_interval_start += time_incr
			UNIX_interval_end += time_incr
			continue
		
		number_conc_list = []
		for row in number_conc_data:
			UNIX_ts = row[0]
			number = row[1]
			volume = row[2]
			raw_number_conc = number/volume
			sampling_period_start = round((row[3] - UNIX_start_day),4) #converts unix utc ts to seconds since midnight of data start day
			sampling_period_end = round((row[4] - UNIX_start_day),4)

			#get T and P for correction to STP
			cursor.execute(('SELECT temperature_C,BP_Pa from polar6_flight_track_details where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_ts-0.5,UNIX_ts+0.5))
			TandP_data = cursor.fetchall()
			if TandP_data == []:
				STPcorr_number_conc = np.nan	
			else:
				temperature = TandP_data[0][0] + 273.15 #convert to Kelvin
				pressure = TandP_data[0][1]
				correction_factor_for_STP = (101325/pressure)*(temperature/273)
				STPcorr_number_conc = raw_number_conc*correction_factor_for_STP
				
			number_conc_list.append([UNIX_ts,STPcorr_number_conc,raw_number_conc])
			
			
			line = [
				sampling_period_start,
				sampling_period_end,
				round_to_n(volume,sig_figs_SP2),
				round_to_n(number,sig_figs_SP2),
				round_to_n(row[5],sig_figs_SP2),  #70 to 80 binned mass
				round_to_n(row[6],sig_figs_SP2),  #80 to 90 binned mass
				round_to_n(row[7],sig_figs_SP2),  #90 to 100 binned mass
				round_to_n(row[8],sig_figs_SP2),  #100 to 110 binned mass
				round_to_n(row[9],sig_figs_SP2),  #110 to 120 binned mass
				round_to_n(row[10],sig_figs_SP2), #120 to 130 binned mass
				round_to_n(row[11],sig_figs_SP2), #130 to 140 binned mass
				round_to_n(row[12],sig_figs_SP2), #140 to 150 binned mass
				round_to_n(row[13],sig_figs_SP2), #150 to 160 binned mass
				round_to_n(row[14],sig_figs_SP2), #160 to 170 binned mass
				round_to_n(row[15],sig_figs_SP2), #170 to 180 binned mass
				round_to_n(row[16],sig_figs_SP2), #180 to 190 binned mass
				round_to_n(row[17],sig_figs_SP2), #190 to 200 binned mass
				round_to_n(row[18],sig_figs_SP2), #200 to 210 binned mass
				round_to_n(row[19],sig_figs_SP2), #210 to 220 binned mass
				]
				
			for item in temp_list:
				tot_mass = item[3]

				if sampling_period_start == item[0]:
					line.insert(4,tot_mass)
					i = 4
					while i < 19:
						line.append(item[i])
						i+=1
			icartt_var_no = len(line) - 1
			icartt_data.append(line)

		UBC_mean_STPcorr_number_conc = np.mean([row[1] for row in number_conc_list])
		UBC_mean_raw_number_conc = np.mean([row[2] for row in number_conc_list])
		UBC_mean_ts = math.floor(np.mean([row[0] for row in number_conc_list]))  #should give us the interval start or midtime :)
		
		######get the AWI mass conc data
		cursor.execute(('SELECT UNIX_UTC_ts,BC_mass_conc from polar6_awi_sp2_mass_concs where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_interval_start,UNIX_interval_end))
		AWI_mass_conc_data = cursor.fetchall()
		if AWI_mass_conc_data == []:
			UNIX_interval_start += time_incr
			UNIX_interval_end += time_incr
			continue
		
		AWI_mass_conc_list = []
		for row in AWI_mass_conc_data:
			AWI_UNIX_ts = row[0]
			AWI_mass_conc = row[1]*1000    #convert ug/m3 to ng/m3
			AWI_mass_conc_list.append([AWI_UNIX_ts,AWI_mass_conc])
			
		AWI_mean_mass_conc = np.mean([row[1] for row in AWI_mass_conc_list])
		AWI_mean_ts = math.floor(np.mean([row[0] for row in AWI_mass_conc_list]))
		#the AWI data has some strange dropouts to large neg values
		if AWI_mean_mass_conc <0:
			AWI_mean_mass_conc = np.nan
		
		

	
		if first_interval == True:
			plot_data.append([UBC_mean_ts,np.nan,np.nan,np.nan,np.nan])   
			first_interval = False
		else:
			plot_data.append([UBC_mean_ts,UBC_mean_STPcorr_mass_conc,UBC_mean_raw_mass_conc,AWI_mean_mass_conc,UBC_mean_raw_number_conc])
			
		
	UNIX_interval_start += time_incr
	UNIX_interval_end += time_incr
	

time_stamps = [dates.date2num(datetime.utcfromtimestamp(row[0])) for row in plot_data]
UBC_STPcorr_mass_conc = [row[1]/fraction_sampled for row in plot_data]
UBC_corr_to_AWI_mass_conc = [row[2]/fraction_sampled for row in plot_data]
UBC_raw_mass_conc = [row[2] for row in plot_data]
AWI_mass_conc = [row[3] for row in plot_data]
UBC_raw_number_conc = [row[4] for row in plot_data]

cnx.close()

#plotting
fig = plt.figure(figsize=(12,12))

ax1  = plt.subplot2grid((2,1), (0,0), colspan=2)
ax2  = plt.subplot2grid((2,1), (1,0), colspan=1)					
#ax3  = plt.subplot2grid((2,2), (1,1), colspan=1)



hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60
if plot_corr_data == True:
	UBC_conc_to_plot = UBC_corr_to_AWI_mass_conc
	UBC_label = 'UBC SP2'
else:
	UBC_conc_to_plot = UBC_raw_mass_conc
	UBC_label = 'UBC SP2 raw data'


ax1.plot(time_stamps,UBC_conc_to_plot,marker='s',color='g',alpha=0.5,label=UBC_label)
if plot_numb_data == True:
	ax1.plot(time_stamps,UBC_raw_number_conc,marker='*',color='orange',alpha=0.5,label='UBC number conc')
ax1.plot(time_stamps,AWI_mass_conc,marker='>',color='r',alpha=0.5,label='AWI SP2')
ax1.set_ylabel('mass conc (ng/m3)')
ax1.set_xlabel('time')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
plt.xlim(dates.date2num(start_time),dates.date2num(end_time))
ax1.set_ylim(0,upper_conc_limit)
fig.suptitle(flight, fontsize=20)
ax1.legend(loc=2)

###plot 2

##linear regression
varx = np.array(UBC_raw_mass_conc)
vary = np.array(AWI_mass_conc)

mask = ~np.isnan(varx) & ~np.isnan(vary)
slope, intercept, r_value, p_value, std_err = stats.linregress(varx[mask], vary[mask])
line = slope*varx+intercept

varx2 = np.array(UBC_corr_to_AWI_mass_conc)
vary2 = np.array(AWI_mass_conc)

mask2 = ~np.isnan(varx2) & ~np.isnan(vary2)
slope2, intercept2, r_value2, p_value2, std_err2 = stats.linregress(varx2[mask2], vary2[mask2])
line2 = slope2*varx2+intercept2


#ax2.scatter(varx,vary,marker='o',color='b',label='UBC SP2 raw data')
#ax2.text(0.12, 0.85,'r-square: ' + str(round(r_value**2,3)),transform=ax2.transAxes)
#ax2.text(0.12, 0.8,'slope: ' + str(round(slope,3)),transform=ax2.transAxes)
#ax2.plot(varx,line,'r-')

if plot_corr_data == True:
	ax2.scatter(varx2,vary2,marker='o',color='b',alpha=1,label='UBC SP2 data')
	ax2.text(0.7, 0.5,'r-square: ' + str(round(r_value2**2,3)),transform=ax2.transAxes)
	ax2.text(0.7, 0.45,'slope: ' + str(round(slope2,3)),transform=ax2.transAxes)
	ax2.plot(varx2,line2,'r-',alpha=1)

ax2.plot([0,upper_conc_limit],[0,upper_conc_limit],color='grey')
ax2.set_ylabel('AWI rBC mass conc (ng/m3)')
ax2.set_xlabel('UBC rBC mass conc (ng/m3)')
ax2.set_xlim(1,upper_conc_limit)
ax2.set_ylim(1,upper_conc_limit)
#ax2.set_xscale('log')
#ax2.set_yscale('log')
#if plot_corr_data == True:
#	plt.legend(loc=4)


####plot 3
#
###linear regression
#varxn = np.array(UBC_conc_to_plot)
#varyn = np.array(UBC_raw_number_conc)
#
#maskn = ~np.isnan(varxn) & ~np.isnan(varyn)
#slopen, interceptn, r_valuen, p_valuen, std_errn = stats.linregress(varxn[maskn], varyn[maskn])
#linen = slopen*varxn+interceptn
#
#ax3.scatter(varxn,varyn,marker='o',color='orange',alpha=1,label='UBC number and mass')
#ax3.text(0.7, 0.5,'r-square: ' + str(round(r_valuen**2,3)),transform=ax3.transAxes)
#ax3.text(0.7, 0.45,'slope: ' + str(round(slopen,3)),transform=ax3.transAxes)
#ax3.plot(varxn,linen,'r-',alpha=1)
#
#ax3.plot([0,upper_conc_limit],[0,upper_conc_limit],color='grey')
#ax3.set_ylabel('UBC rBC number conc (ng/m3)')
#ax3.set_xlabel('UBC rBC mass conc (ng/m3)')
#plt.xlim(0,upper_conc_limit)
#plt.ylim(0,upper_conc_limit)





dir = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/AWI UBC comparison/'
os.chdir(dir)
if save_plot == True:
	plt.savefig('NC - Polar6 - '+'all_data_130'+' - AWI SP2 vs UBC SP2 - UBC Alert calib.png', bbox_inches='tight') 

plt.show()

if write_icartt_file == True:
	##write icartt data to file

	scale_factor_list = ''
	missing_data_indicators_list = ''
	i = 0
	while i < icartt_var_no:
		scale_factor_list = scale_factor_list + '1,'
		missing_data_indicators_list = missing_data_indicators_list + '-9999,'
		i+=1

	date_string_for_filename = datetime.strftime(data_start_day, '%Y%m%d')
	file_name = 'UBCSP2_Polar6_' + date_string_for_filename + '_R0.ict'
	file_location = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UBC SP2 icartt files/Alert_calib/'

	new_file = CreateIcarttFile(file_name,file_location)


	new_file.PI_names = 'Hanna, Sarah; Bertram, Allan' 					
	new_file.PI_affiliations = 'University of British Columbia, Vancouver, Canada'			
	new_file.data_source = 'rBC mass concentration from SP2 (single particle soot photometer)'				
	new_file.mission_name = 'NETCARE Polar 6 Arctic spring campaign 2015'				
	new_file.file_vol = '1, 1'					
	new_file.data_start_date = '2015,04,05'			
	new_file.data_revision_date = date.strftime(date.today(), '%Y,%m,%d')
	new_file.data_interval = '0'				
	new_file.indep_variable_name = 'Start_UTC, seconds' 		
	new_file.no_of_variables =  str(icartt_var_no)			
	new_file.scale_factors = scale_factor_list				
	new_file.missing_data_indicators = missing_data_indicators_list	
	new_file.variable_names = 	'Stop_UTC, seconds\n'\
								'volume_sampled, cm3\n'\
								'total_number, #\n'\
								'total_msss, ug\n'\
								'number_70to80nm, #\n'\
								'number_80to90nm, #\n'\
								'number_90to100nm, #\n'\
								'number_100to110nm, #\n'\
								'number_110to120nm, #\n'\
								'number_120to130nm, #\n'\
								'number_130to140nm, #\n'\
								'number_140to150nm, #\n'\
								'number_150to160nm, #\n'\
								'number_160to170nm, #\n'\
								'number_170to180nm, #\n'\
								'number_180to190nm, #\n'\
								'number_190to200nm, #\n'\
								'number_200to210nm, #\n'\
								'number_210to220nm, #\n'\
								'mass_70to80nm, ug\n'\
								'mass_80to90nm, ug\n'\
								'mass_90to100nm, ug\n'\
								'mass_100to110nm, ug\n'\
								'mass_110to120nm, ug\n'\
								'mass_120to130nm, ug\n'\
								'mass_130to140nm, ug\n'\
								'mass_140to150nm, ug\n'\
								'mass_150to160nm, ug\n'\
								'mass_160to170nm, ug\n'\
								'mass_170to180nm, ug\n'\
								'mass_180to190nm, ug\n'\
								'mass_190to200nm, ug\n'\
								'mass_200to210nm, ug\n'\
								'mass_210to220nm, ug'
	new_file.no_special_comment_lines = '0'		
	new_file.no_normal_comments = '17'		
	new_file.normal_comments = 'PI_CONTACT_INFO: Address: 2036 Main Mall, Vancouver, BC Canada V6T 1Z1, email: sarah.hanna@gmail.com; bertram@chem.ubc.ca\n'\
		'PLATFORM: Polar 6\n'\
		'LOCATION: Aircraft location data on FTP server (particle.chem-eng.utoronto.ca)\n'\
		'ASSOCIATED_DATA: N/A\n'\
		'INSTRUMENT_INFO: Refractory black carbon aerosol measurements based on laser induced incandescence\n'\
		'DATA_INFO: Units are as given above, volume is at ambient conditions (not STP)\n'\
		'UNCERTAINTY: TBD, preliminary data\n'\
		'ULOD_FLAG: -7777\n'\
		'ULOD_VALUE: N/A\n'\
		'LLOD_FLAG: -8888\n'\
		'LLOD_VALUE: TBD\n'\
		'DM_CONTACT_INFO: N/A\n'\
		'PROJECT_INFO: NETCARE Polar 6 aircraft campaign in April 2015\n'\
		'STIPULATIONS_ON_USE: Preliminary data. Use of these data requires prior approval from PI\n'\
		'OTHER_COMMENTS: This data is for rBC cores in the range of 70-220nm. Aquadag was used as a calibration standard and the particle masses have been corrected upward to account for the reported bias in SP2 response to Aquadag (Laborde et al, 2012)\n'\
		'REVISION: R0\n'\
		'R0: Preliminary data, initial release'	
	new_file.data_headers = 'Start_UTC,Stop_UTC,volume_sampled,total_number,total_msss,number_70to80nm,number_80to90nm,number_90to100nm,number_100to110nm,number_110to120nm,number_120to130nm,number_130to140nm,number_140to150nm,number_150to160nm,number_160to170nm,number_170to180nm,number_180to190nm,number_190to200nm,number_200to210nm,number_210to220nm,mass_70to80nm,mass_80to90nm,mass_90to100nm,mass_100to110nm,mass_110to120nm,mass_120to130nm,mass_130to140nm,mass_140to150nm,mass_150to160nm,mass_160to170nm,mass_170to180nm,mass_180to190nm,mass_190to200nm,mass_200to210nm,mass_210to220nm'
		
		
	new_file.createHeader()

	new_file.writeData(icartt_data)