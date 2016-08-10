import sys
import os
from datetime import datetime
from pprint import pprint
import pickle
from datetime import timedelta
import calendar
from matplotlib import dates
import matplotlib.pyplot as plt
import numpy as np

start = datetime(2012,1,1)
end =  datetime(2013,1,1)
sample_factor = 10

######get data
#PAPI_list = []
#data_dir = 'F:/Alert/'+ str(start.year) +'/Reduced/'  #Alert data is in UTC - see email from Dan Veber
#os.chdir(data_dir)
#for directory in os.listdir(data_dir):
#	
#	if os.path.isdir(directory) == True and directory.startswith('20'):
#		folder_date = datetime.strptime(directory, '%Y%m%d')
#		folder_path = os.path.join(data_dir, directory)
#		
#		os.chdir(folder_path)
#		
#		if  start <= folder_date < end :
#		
#			for file in os.listdir('.'):
#				
#				if file.endswith('OutputWaves.dat'):
#					print file
#					with open(file, 'r') as f:
#						temp = f.read().splitlines()
#						first_line = True
#						for line in temp:
#							if first_line == True:
#								first_line = False
#								continue
#							newline = line.split()
#							raw_time = (float(newline[0]) + 3600/2) + calendar.timegm(folder_date.utctimetuple())
#							date_time = datetime.utcfromtimestamp(raw_time) #+ timedelta(hours = 8)
#							incand_conc = float(newline[5])*sample_factor
#							try:
#								incand_mass = float(newline[7])
#								incand_mass_tot = float(newline[8])*sample_factor
#							except:
#								incand_mass = np.nan
#								incand_mass_tot = np.nan
#							PAPI_list.append([date_time,incand_conc,incand_mass,incand_mass_tot])
#							
#							
#		os.chdir(data_dir)
#	
#PAPI_dates = [dates.date2num(row[0]) for row in PAPI_list]
#PAPI_numb = [row[1] for row in PAPI_list]
#PAPI_mass = [row[2] for row in PAPI_list]
#PAPI_mass_tot = [row[3] for row in PAPI_list]

SP2_list = []
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013 - mass concentrations/'  #Alert data is in UTC - see email from Dan Veber
#data_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013/'  #Alert data is in UTC - see email from Dan Veber
os.chdir(data_dir)
for file in os.listdir('.'):
			
	if file.startswith(str(start.year)):
		
		file_date = datetime.strptime(file[0:8],'%Y%m%d')
		if start <= file_date < end :
			print file
			with open(file, 'r') as f:
				temp = f.read().splitlines()
				i = 0
				for line in temp:
					i+=1
					if i > 3:
						newline = line.split()
						date_time = datetime.strptime(newline[0] + newline[1], '%Y-%m-%d%H:%M:%S') + timedelta(minutes = 30)
						incand_conc = float(newline[6])
						incand_mass = float(newline[4])
						incand_mass_uncer = float(newline[5])
						vol = float(newline[7])
						rel_err = incand_mass_uncer*100./incand_mass
						SP2_list.append([date_time,rel_err,incand_mass,vol])
						
SP2_dates = [dates.date2num(row[0]) for row in SP2_list]
print np.nanmean([row[1] for row in SP2_list])
SP2_mass = [row[2] for row in SP2_list]
vol = [row[3] for row in SP2_list]
ratios = []
i=0
for row in SP2_mass:
	try:
		ratio = row/PAPI_mass[i]
		ratios.append([SP2_dates[i],ratio])
	except:
		continue
	i+=1
	
ratio_dates = [row[0] for row in ratios]
ratio_vals = [row[1] for row in ratios]
	
hfmt  = dates.DateFormatter('%Y%m%d %H:%M')
fig = plt.figure(figsize=(20,6))
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_formatter(hfmt)
#ax1.plot(PAPI_dates,PAPI_mass_tot,color='b')#,'-bo')
ax1.plot(SP2_dates,SP2_mass,color='k')#,'-ro')
ax1.plot(SP2_dates,vol,color='r')#,'-ro')
#ax1.plot(ratio_dates,ratio_vals,color='r')#,'-ro')
ax1.set_xlim(start,end)
#ax1.axvline(datetime(2014,9,9))

#ax1.set_ylim(-5,150)
ax1.set_ylabel('incandescent mass (ng/m3) SP2#58')
ax1.set_xlabel('Date')

#plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/2014-2015_mass_conc.png', bbox_inches='tight')


plt.show()