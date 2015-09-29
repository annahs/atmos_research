import os
import sys
from datetime import datetime
import pickle

high_RH_times = []
f = open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/whi__met_summer_2009-2012.txt', 'r')
f.readline()
for line in f:
	newline = line.split()

	file_date = newline[0].strip()
	file_hour = newline[1].strip()
	try:
		RH = float(newline[3].strip())
	except:
		continue
		
	date = datetime.strptime(file_date, '%d/%m/%Y')    
	hour = datetime.strptime(file_hour, '%H:%M').time()
	date_time = datetime.combine(date, hour)
	
	
	if RH > 90:
		high_RH_times.append(date_time)  #in PST!
	
f.close()	

pickl_file = open('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/WHI station met and other data/high RH times.pkl', 'wb')
pickle.dump(high_RH_times, pickl_file)
pickl_file.close()

