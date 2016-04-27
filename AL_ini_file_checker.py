import sys
import os
from datetime import datetime
from pprint import pprint
import pickle
from datetime import timedelta



######get data

data_dir = 'F:/Alert/2013/SP2B_files/'  #Alert data is in UTC - see email from Dan Veber
os.chdir(data_dir)
for directory in os.listdir(data_dir):
	
	if os.path.isdir(directory) == True and directory.startswith('20'):
		folder_date = datetime.strptime(directory, '%Y%m%d')
		folder_path = os.path.join(data_dir, directory)
		
		os.chdir(folder_path)
		
		if  datetime(2013,9,27) <= folder_date < datetime(2016,1,1) :
		
			for file in os.listdir('.'):
				
				if file.endswith('.ini'):
					
					with open(file, 'r') as f:
						for line in f:
							#if line.startswith('Last Date Updated'):
							#	raw_date = line[18:].rstrip()
							#	ini_date = datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S')
							
							if line.startswith('1 of Every'):
								sample_rate = float(line[11:].rstrip())
								if sample_rate != 10:
									print file
									#print ini_date, ('UTC')
									print 'sample rate', sample_rate
		os.chdir(data_dir)