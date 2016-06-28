import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
from datetime import timedelta
import calendar
import mysql.connector



#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

max_display_conc = 1000
correction_factor_for_massdistr = 1.85#set to 1 and deal with each cluster separately 1.96 #corrects for only sampling part of the mass distr +- 5%
R = 8.3144621 # in m3*Pa/(K*mol)

#import WHI met data for STP corrections 
WHI_pressures = []
with open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/whi__met_summer_2009-2012.txt', 'r') as f:
	f.readline()
	for line in f:
		newline = line.split('\t') 
		date_PST = datetime.strptime(newline[0], '%d/%m/%Y %H:%M') 
		try:
			pressure_mbar = float(newline[5])
			pressure_Pa = pressure_mbar*100 #100Pa/mbar
			WHI_pressures.append([date_PST,pressure_Pa])
		except:
			continue
temp = []
for line in WHI_pressures:
	date =  line[0]
	pressure = line[1]
	
	if date.year == 2012:
		temp.append(pressure)



WHI_room_temps = []
with open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/whi__rt_stackflow_summer_2009-2012.txt', 'r') as f:
	f.readline()
	for line in f:
		newline = line.split('\t') 
		date_PST = datetime.strptime(newline[0], '%d/%m/%Y %H:%M') 
		try:
			temp_degC = float(newline[1])
			temp_K = temp_degC + 273.15
			if date_PST.year == 2012:
				WHI_room_temps.append([date_PST,temp_K])
		except:
			continue



#set up arrays
full_record = []
record_list = []
record_list_uncorrSTP = []
record_dict = {}
record_dict_uncorrSTP = {}
spike_times = []


#get BC data and remove spikes


prev_ts = datetime.strptime('2000/01/01', '%Y/%m/%d')
prev_bc_mass_conc = 1000

time_jump = timedelta(hours=1)

os.chdir('D:/2012/WHI_UBCSP2/Binary/10 min bins - 2012 calib - AD corrected/',)
for file in os.listdir('.'):
	if file.endswith('.binpckl'):
		print file
		f = open(file, 'r')
		single_bc_record = pickle.load(f)
		f.close()
		
		i=0
			
		for row in single_bc_record:
			#row info: interval_mid_time, incand_number_conc, BC_mass_conc, interval_sampling_duration, interval_incand_count 

			#set units
			record_date =  datetime.utcfromtimestamp(float(row[0])) 
			record_hour = datetime(record_date.year,record_date.month,record_date.day,record_date.hour)
			number_conc = row[1]*1e6 #converts incand #/cm3 to #/m3
			#for BC mass the conversion from /cm3 to /m3 and from fg to ng cancel each other out, so no manipulation is necessary
					
			#get STP correction factor - pressure term
			number_pressures = len(WHI_pressures)
							
			if number_pressures:               
				WHI_pressure_time = WHI_pressures[0][0]
				
				while record_date > WHI_pressure_time + timedelta(hours=1):
					WHI_pressures.pop(0)
					if len(WHI_pressures):
						WHI_pressure_time = WHI_pressures[0][0]
						WHI_pressure = WHI_pressures[0][1]
						continue
					else:
						break
						
				number_pressures = len(WHI_pressures)
			
			#get STP correction factor - temp term
			number_temps = len(WHI_room_temps)
							
			if number_temps:               
				WHI_temp_time = WHI_room_temps[0][0]
				
				while record_date > WHI_temp_time + timedelta(hours=1):
					WHI_room_temps.pop(0)
					if len(WHI_room_temps):
						WHI_temp_time = WHI_room_temps[0][0]
						WHI_temp = WHI_room_temps[0][1]
						continue
					else:
						break
						
				number_temps = len(WHI_room_temps)
			
			#calc correction factor
			volume_ambient = (R*WHI_temp)/(WHI_pressure)
			volume_STP = volume_ambient*(WHI_pressure/101325)*(273/WHI_temp)
			correction_factor_for_STP = volume_ambient/volume_STP
			#determine if bc mass conc is a spike from snow machines etc
			BC_mass_conc = row[2]
			
			#if record_date.year == 2012 and BC_mass_conc > 200.:
			#	continue
			
			if (BC_mass_conc < 6*prev_bc_mass_conc) or (BC_mass_conc < 10.0) or (record_date > prev_ts +time_jump): #check for spikes
					if BC_mass_conc < 2000: #set abs max

						#correcting the rows that are not spikes for the portion of the mass distr that we're not sampling
						#we have to check the LL and UL though, becuase some very few are nans (from binning code) and these mess up all subsequent calcs
						#row[2] = mass conc, row[3] = LL, row[4] = UL
						median = row[2]
						BC_mass_corr = row[2]*correction_factor_for_massdistr*correction_factor_for_STP
						BC_mass_uncorr = row[2]*correction_factor_for_massdistr
					
						new_row = [number_conc,BC_mass_corr]
						new_row_uncorr = [number_conc,BC_mass_uncorr]
						
						if record_hour not in record_dict:
							record_dict[record_hour] = []
						record_dict[record_hour].append(new_row)                         
						
						if record_hour not in record_dict_uncorrSTP:
							record_dict_uncorrSTP[record_hour] = []
						record_dict_uncorrSTP[record_hour].append(new_row_uncorr)                         
						
						
						
						prev_bc_mass_conc = BC_mass_conc
						i=0
			else:
				spike_times.append(record_date)
			
			prev_ts = record_date
			i+=1
temp = []
for hour in record_dict:
	mean_number = np.mean([row[0] for row in record_dict[hour]])
	mean_mass = np.mean([row[1] for row in record_dict[hour]])
	record_list.append([hour,mean_number,mean_mass])
	if hour.month == 7 and hour.day in [3,4,5,6,7,8,9,10,11]:
		temp.append(mean_mass)
		
print 'mean 3-11', np.mean(temp)
record_list.sort()	

for hour in record_dict_uncorrSTP:
	mean_number = np.mean([row[0] for row in record_dict_uncorrSTP[hour]])
	mean_mass = np.mean([row[1] for row in record_dict_uncorrSTP[hour]])
	record_list_uncorrSTP.append([hour,mean_number,mean_mass])

	
record_list_uncorrSTP.sort()	

BC_dates_2012 = [dates.date2num(row[0]) for row in record_list]
BC_number_conc_2012 = [row[1] for row in record_list]
BC_mass_conc_2012 = [row[2] for row in record_list]

BC_dates_2012_uncorr = [dates.date2num(row[0]) for row in record_list_uncorrSTP]
BC_number_conc_2012_uncorr = [row[1] for row in record_list_uncorrSTP]
BC_mass_conc_2012_uncorr = [row[2] for row in record_list_uncorrSTP]


#########EC filter data#######

file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/filter EC/WSL_OCEC_Database_(Aug.2008-May.2012)_QAQC_PI_(to RL).txt'
EC_filter_data = []

with open(file, 'r') as f:
    
    for i in range(0,19):
        f.readline()
        
    for line in f:
		newline = line.split('\t')
		start_date = datetime.strptime(newline[1], '%d/%m/%Y %H:%M')  #PST PDT???
		stop_date = datetime.strptime(newline[2], '%d/%m/%Y %H:%M')

		try:
			EC_conc = float(newline[9])*1000 # orig is in ugC/m3 so *1000 to get ng/m3
		except:
			print 'no value'
			continue
			
		date = (stop_date-start_date)/2 + start_date

		EC_filter_data.append([date,EC_conc])

        
EC_dates = [dates.date2num(row[0]) for row in EC_filter_data]
EC_mass_concs = [row[1] for row in EC_filter_data]        
        
######GC 1 h values
#
##database connection
#cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
#cursor = cnx.cursor()
#
#cursor.execute(('''SELECT *
#		FROM whi_gc_and_sp2_1h_mass_concs
#		''')
#		)
#data_1h = cursor.fetchall()
#
#times_PST = []
#meas = []
#GC = []
#for row in data_1h:
#	ts = row[1]
#	gc = row[3]
#
#	ts_datetime = datetime.utcfromtimestamp(ts)
#	times_PST.append(dates.date2num(ts_datetime+timedelta(hours=-8)))
#	GC.append(gc)
#       
#cnx.close()


####plotting
#os.chdir('C:/Users/Sarah Hanna/Documents/Data/EC Siberian Fire paper/')
#file = open('WHI_rBC_record_July2012.txt', 'w')
#file.write('interval_mid_time_(PST)'+ '\t' +'incand_number_conc(#/m3)'+ '\t' +' BC_mass_conc(ng/m3)'+ '\n')
#
#for row in record_list:
#	line = '\t'.join(str(x) for x in row)
#	file.write(line + '\n')
#	
#file.close()
		



fig = plt.figure(figsize=(12,6))

hfmt = dates.DateFormatter('%b')
hfmt = dates.DateFormatter('%m-%d')
display_month_interval = 1

ax1 =  plt.subplot2grid((1,1), (0,0))

ax1.plot(BC_dates_2012,BC_mass_conc_2012, color='g', marker = '.',label='SP2 corrected to STP')
#ax1.plot(BC_dates_2012_uncorr,BC_mass_conc_2012_uncorr, color='grey', marker = '.',label='SP2 uncorrected')
ax1.scatter(EC_dates,EC_mass_concs, color='r', marker = 'o',s=26,label='EC Filters')
#ax1.scatter(times_PST,GC, color='g', marker = '.',label='GEOS-Chem')

ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.DayLocator(interval = display_month_interval))
ax1.xaxis.set_visible(True)
ax1.set_ylabel('rBC mass concentration (ng/m3 - STP)')
plt.text(0.05, 0.9,'2012', transform=ax1.transAxes,fontsize=18)
#ax1.set_ylim(0, 250)
#ax1.set_xlim(dates.date2num(datetime.strptime('2012/07/20 12:00', '%Y/%m/%d %H:%M')), dates.date2num(datetime.strptime('2012/07/30', '%Y/%m/%d')))
ax1.set_ylim(0, 320)
ax1.set_xlim(dates.date2num(datetime.strptime('2012/04/01 12:00', '%Y/%m/%d %H:%M')), dates.date2num(datetime.strptime('2012/05/31', '%Y/%m/%d')))
plt.legend()
plt.show()
				

				