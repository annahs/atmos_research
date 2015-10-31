import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import dates
import os
import pickle
import datetime
from pprint import pprint
import sys
from datetime import timedelta
import calendar


max_display_conc = 1000
correction_factor_for_massdistr = 1#set to 1 and deal with each cluster separately 1.96 #corrects for only sampling part of the mass distr +- 5%
R = 8.3144621 # in m3*Pa/(K*mol)


directory_list = [
'D:/2009/WHI_ECSP2/Binary/2 min bins - AD corrected/',  
'D:/2010/WHI_ECSP2/Binary/2 min bins - AD corrected/',
#'D:/2010/WHI_UBCSP2/Binary/10 min bins/',
'D:/2012/WHI_UBCSP2/Binary/2 min bins - 2012 calib - AD corrected/',
#'D:/2013_a/WHI_UBCSP2/Binary/10 min bins - 2012 calib/',
#'C:/SP2 data/2013_b/10 min bins - 2012 calib/',
#
#'D:/2012/WHI_UBCSP2/Binary/10 min bins - 2014 calib/',
#'D:/2013_a/WHI_UBCSP2/Binary/10 min bins - 20142 calib/',
#'C:/SP2 data/2013_b/10 min bins - 2014 calib/',


]


#fire times for plotting shaded areas
fire_span1_09s=datetime.datetime.strptime('2009/07/03', '%Y/%m/%d')
fire_span1_09f=datetime.datetime.strptime('2009/07/06', '%Y/%m/%d')

fire_span2_09s=datetime.datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span2_09f=datetime.datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span3_09s=datetime.datetime.strptime('2009/08/19', '%Y/%m/%d')
fire_span3_09f=datetime.datetime.strptime('2009/08/20', '%Y/%m/%d')

fire_span1_10s=datetime.datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')

fire_span1_12s=datetime.datetime.strptime('2012/07/6 12:00', '%Y/%m/%d %H:%M') #Siberian event
fire_span1_12f=datetime.datetime.strptime('2012/07/10', '%Y/%m/%d')
		
fire_span2_12s=datetime.datetime.strptime('2012/07/16 00:00', '%Y/%m/%d %H:%M') #local event
fire_span2_12f=datetime.datetime.strptime('2012/07/17', '%Y/%m/%d')

fire_span3_12s=datetime.datetime.strptime('2012/08/16', '%Y/%m/%d')
fire_span3_12f=datetime.datetime.strptime('2012/08/19', '%Y/%m/%d')

fire_span4_12s=datetime.datetime.strptime('2012/08/31', '%Y/%m/%d')
fire_span4_12f=datetime.datetime.strptime('2012/09/03', '%Y/%m/%d')

fire_alpha = 0.2
fire_color = '#990000'

#import WHI met data for STP corrections 


WHI_pressures = []
with open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/whi__met_summer_2009-2012.txt', 'r') as f:
	f.readline()
	for line in f:
		newline = line.split('\t') 
		date_PST = datetime.datetime.strptime(newline[0], '%d/%m/%Y %H:%M') 
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
	
	if date.year == 2009 and date.month in [7,8]:
		temp.append(pressure)
	if date.year == 2010 and date.month in [6,7]:
		temp.append(pressure)
	if date.year == 2012 and date.month in [4,5]:
		temp.append(pressure)
pprint(temp)
print 'mean pressure:',np.mean(temp), 'SD:', np.std(temp)


WHI_room_temps = []
with open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/whi__rt_stackflow_summer_2009-2012.txt', 'r') as f:
	f.readline()
	for line in f:
		newline = line.split('\t') 
		date_PST = datetime.datetime.strptime(newline[0], '%d/%m/%Y %H:%M') 
		try:
			temp_degC = float(newline[1])
			temp_K = temp_degC + 273.15
			WHI_room_temps.append([date_PST,temp_K])
		except:
			continue



#set up arrays
full_record = []
record_list = []
spike_times = []


#get BC data and remove spikes
i=0
while i < len(directory_list):
	record_list.append([])
	i+=1
	
prev_ts = datetime.datetime.strptime('2000/01/01', '%Y/%m/%d')
prev_bc_mass_conc = 1000

time_jump = timedelta(hours=1)

year = 0
for directory in directory_list:

	os.chdir(directory)

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
				row[0] = datetime.datetime.utcfromtimestamp(float(row[0]))  #in PST
				record_date = row[0]
				row[1] = row[1]*1e6 #converts incand #/cm3 to #/m3
				#for BC mass the conversion from /cm3 to /m3 and from fg to ng cancel each other out, so no manipulation is necessary
				
				if record_date.year >= 2012 and record_date.month >= 06:
					break
				########just for the record:  f'd up!!S
				#######UNIX_GMT_ts = calendar.timegm(prev_ts.utctimetuple()) + 8*3600
				#######row.append(UNIX_GMT_ts)
				
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
				correction_factor_for_STP =  volume_ambient/volume_STP
				#determine if bc mass conc is a spike from snow machines etc
				BC_mass_conc = row[2]
				
				if record_date.year == 2012 and BC_mass_conc > 200.:
					continue
				
				if (BC_mass_conc < 6*prev_bc_mass_conc) or (BC_mass_conc < 10.0) or (record_date > prev_ts +time_jump): #check for spikes
						if BC_mass_conc < 2000: #set abs max

							#correcting the rows that are not spikes for the portion of the mass distr that we're not sampling
							#we have to check the LL and UL though, becuase some very few are nans (from binning code) and these mess up all subsequent calcs
							#row[2] = mass conc, row[3] = LL, row[4] = UL
							median = row[2]
							row[2] = row[2]*correction_factor_for_massdistr*correction_factor_for_STP
						
							if np.isnan(row[3]) == True:
								row[3] = median*correction_factor_for_massdistr*correction_factor_for_STP  #just set LL to mass conc if nan
							else:
								row[3] = row[3]*correction_factor_for_massdistr*correction_factor_for_STP
							
							if np.isnan(row[4]) == True:
								row[4] = median*correction_factor_for_massdistr*correction_factor_for_STP  #just set UL to mass conc if nan
							else:
								row[4] = row[4]*correction_factor_for_massdistr*correction_factor_for_STP

							full_record.append(row)
							record_list[year].append(row)                              
							prev_bc_mass_conc = BC_mass_conc
							i=0
				else:
					spike_times.append(record_date)
				
				prev_ts = record_date
				i+=1

	year+=1          

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record')
	
#pickle the full record and spike times
file = open('WHI_rBC_record_2009to2013-spikes_removed.rbcpckl', 'w')
pickle.dump(full_record, file)
file.close()

file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'w')
pickle.dump(spike_times, file)
file.close()


file = open('WHI_rBC_record_2009to2013-spikes_removed.txt', 'w')
file.write('interval_mid_time_(PST)'+ '\t' +'incand_number_conc(#/m3)'+ '\t' +' BC_mass_conc(ng/m3)'+ '\t'+' BC_mass_conc_LL'+ '\t'+' BC_mass_conc_UL'+ '\t' +'interval_sampling_duration'+ '\t' +'interval_incand_count' + '\t' + 'UNIX_GMT_ts'+'\n')

for row in full_record:
	line = '\t'.join(str(x) for x in row)
	file.write(line + '\n')
	
file.close()
		





		
#get fire counts

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/Fire counts')

file = open('fire_counts.firespckl', 'r')
fire_counts = pickle.load(file)
file.close()

print 'plotting a'

bar_width = 1.0/144
max_num_display = 8e8
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record')

fire_count_dates =  [dates.date2num(row[0]) for row in fire_counts]
fire_count_numbers = [row[1] for row in fire_counts]


#2012 calib

BC_dates_2009 = [dates.date2num(row[0]) for row in record_list[0]]
BC_number_conc_2009 = [row[1] for row in record_list[0]]
BC_mass_conc_2009 = [row[2] for row in record_list[0]]

BC_dates_2010_EC = [dates.date2num(row[0]) for row in record_list[1]]
BC_number_conc_2010_EC = [row[1] for row in record_list[1]]
BC_mass_conc_2010_EC = [row[2] for row in record_list[1]]

#BC_dates_2010_UBC = [dates.date2num(row[0]) for row in record_list[2]]
#BC_number_conc_2010_UBC = [row[1] for row in record_list[2]]
#BC_mass_conc_2010_UBC = [row[2] for row in record_list[2]]

BC_dates_2012 = [dates.date2num(row[0]) for row in record_list[2]]
BC_number_conc_2012 = [row[1] for row in record_list[2]]
BC_mass_conc_2012 = [row[2] for row in record_list[2]]



###plotting

fig = plt.figure(figsize=(12,6))

hfmt = dates.DateFormatter('%b')
hfmt = dates.DateFormatter('%m-%d-%H:%M')
display_month_interval = 1


ax1 = plt.subplot2grid((1,12), (0,0), colspan=4)
ax2 = plt.subplot2grid((1,12), (0,4), colspan=4, sharey=ax1)
ax3 = plt.subplot2grid((1,12), (0,8), colspan=4, sharey=ax1)



ax1.scatter(BC_dates_2009,BC_mass_conc_2009, color='blue', marker = '.')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax1.xaxis.set_visible(True)
ax1.set_ylabel('rBC mass concentration (ng/m3)')
plt.text(0.05, 0.9,'2009', transform=ax1.transAxes,fontsize=18)
ax1.set_ylim(0, max_display_conc)
ax1.set_xlim(dates.date2num(datetime.datetime.strptime('2009/06/20', '%Y/%m/%d')), dates.date2num(datetime.datetime.strptime('2009/08/25', '%Y/%m/%d')))
ax1.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)


#ax2.scatter(BC_dates_2010_UBC,BC_mass_conc_2010_UBC,color = 'blue', marker = '^' , facecolor = 'none')   
ax2.scatter(BC_dates_2010_EC,BC_mass_conc_2010_EC, color = 'blue', marker = '.')
ax2.xaxis.set_major_formatter(hfmt)
ax2.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax2.xaxis.set_visible(True)
ax2.yaxis.set_visible(False)
ax2.set_xlabel('month')
plt.text(0.05, 0.9,'2010', transform=ax2.transAxes,fontsize=18)
ax2.set_ylim(0, max_display_conc)
ax2.set_xlim(dates.date2num(datetime.datetime.strptime('2010/05/28', '%Y/%m/%d')), dates.date2num(datetime.datetime.strptime('2010/08/07', '%Y/%m/%d')))
ax2.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)


ax3.plot(BC_dates_2012,BC_mass_conc_2012, color = 'blue' , marker = '.')
ax3.xaxis.set_major_formatter(hfmt)
ax3.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax3.xaxis.set_visible(True)
ax3.yaxis.set_visible(False)
plt.text(0.05, 0.9,'2012', transform=ax3.transAxes,fontsize=18)
ax3.set_ylim(0, max_display_conc)
ax3.set_xlim(dates.date2num(datetime.datetime.strptime('2012/03/28', '%Y/%m/%d')), dates.date2num(datetime.datetime.strptime('2012/06/07', '%Y/%m/%d')))

#ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-01 01:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-01 02:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
#ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-01 05:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-01 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
#ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-02 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-02 23:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
#ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-02 23:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-03 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-05 01:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-05 04:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-05 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-05 20:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-06 21:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-07 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-07 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-08 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-08 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-09 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-09 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-10 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-12 05:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-12 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-15 23:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-16 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-17 20:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-18 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-19 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-19 23:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-21 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-21 20:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-27 22:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-28 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-04-30 07:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-04-30 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-03 02:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-03 03:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-12 00:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-12 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-12 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-12 21:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-20 00:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-20 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-21 07:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-21 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-21 23:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-22 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-24 20:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-25 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-25 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-26 08:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-26 19:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-26 22:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)
ax3.axvspan(dates.date2num(datetime.datetime.strptime('2012-05-30 21:30', '%Y-%m-%d %H:%M')),dates.date2num(datetime.datetime.strptime('2012-05-30 23:30', '%Y-%m-%d %H:%M')), facecolor='blue', alpha=0.2)


plt.subplots_adjust(wspace=0.2)

plt.savefig('WHI rBC record 2009-2013 - horiz.png',bbox_inches='tight',dpi=300)
	

plt.show()
				

				