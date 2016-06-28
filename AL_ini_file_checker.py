import sys
import os
from datetime import datetime
from pprint import pprint
import pickle
from datetime import timedelta



######get data

#data_dir = 'F:/Alert/2011/SP2B_files/'  #Alert data is in UTC - see email from Dan Veber
data_dir = 'F:/WHI_SP2_2009_2010/2010/WHI_ECSP2/Binary/' 
data_dir = 'D:/2012/WHI_UBCSP2/Binary/' 
os.chdir(data_dir)
for directory in os.listdir(data_dir):
	
	if os.path.isdir(directory) == True and directory.startswith('20'):
		folder_date = datetime.strptime(directory, '%Y%m%d')
		folder_path = os.path.join(data_dir, directory)
		
		if folder_date < datetime(2012,6,2):
		
			os.chdir(folder_path)
		
			for file in os.listdir('.'):
				
				if file.endswith('.ini'):
					print file
					with open(file, 'r') as f:
						for line in f:
							if line.startswith('Last Date Updated'):
								raw_date = line[18:].rstrip()
								ini_date = datetime.strptime(raw_date, '%m/%d/%Y %I:%M:%S %p')
								print ini_date
							
							if line.startswith('1 of Every'):
								sample_rate = float(line[11:].rstrip())
								#if sample_rate != 10:
								
								#print ini_date, ('UTC')
								print 'sample rate', sample_rate
							#if line.startswith('Out Of='):
								#print line
			os.chdir(data_dir)