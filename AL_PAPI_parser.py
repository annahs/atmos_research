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


######get data
list = []
data_dir = 'F:/Alert/2013/Reduced/'  #Alert data is in UTC - see email from Dan Veber
os.chdir(data_dir)
for directory in os.listdir(data_dir):
	
	if os.path.isdir(directory) == True and directory.startswith('20'):
		folder_date = datetime.strptime(directory, '%Y%m%d')
		folder_path = os.path.join(data_dir, directory)
		
		os.chdir(folder_path)
		
		if  datetime(2013,10,1) <= folder_date < datetime(2014,1,1) :
		
			for file in os.listdir('.'):
				
				if file.endswith('OutputWaves.dat'):
					print file
					with open(file, 'r') as f:
						temp = f.read().splitlines()
						first_line = True
						for line in temp:
							if first_line == True:
								first_line = False
								continue
							newline = line.split()
							raw_time = (float(newline[0]) + 3600/2) + calendar.timegm(folder_date.utctimetuple())
							date_time = datetime.utcfromtimestamp(raw_time)
							try: 
								incand_conc = float(newline[8])
								if incand_conc == 0:
									incand_conc = np.nan
								tot_incand_conc = float(newline[9])
							except:
								incand_conc = np.nan
								tot_incand_conc = np.nan
							ratio= tot_incand_conc/incand_conc
							list.append([date_time,ratio])
							
							
		os.chdir(data_dir)
	
dates_plot = [dates.date2num(row[0]) for row in list]
ratios = [row[1] for row in list]

mean_ratio =  np.nanmean(ratios)
hfmt  = dates.DateFormatter('%Y%m%d')
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_formatter(hfmt)
ax1.plot(dates_plot,ratios,'-bo')
ax1.set_ylim(0,6)
ax1.set_ylabel('PAPI Total incandescent mass/Incandescent mass\n Oct-Dec 2013')
ax1.set_xlabel('Date')
plt.axhline(y=mean_ratio,color='r')
ax1.text(0.7, 0.9,'mean ratio: ' + str(round(mean_ratio,3)), fontsize = 16, transform=ax1.transAxes)

plt.show()