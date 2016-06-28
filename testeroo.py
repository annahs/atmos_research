#this script is used to add rBC mass to the database

import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from scipy.optimize import curve_fit
from scipy import stats
from SP2_particle_record_UTC import ParticleRecord
from struct import *
import hk_new
import hk_new_no_ts_LEO
from scipy import linspace, polyval, polyfit, sqrt, stats
import math
import mysql.connector
from datetime import datetime
import calendar


dir_c = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Jasons analysis/Raw/2011/'
os.chdir(dir_c)
file_list = []
file_name_list = []
for file in os.listdir('.'):
	file_list.append([file,os.path.getsize('C:/Users/Sarah Hanna/Documents/Data/Alert Data/Jasons analysis/Raw/2011/' + file)/1000])
	file_name_list.append(file)

#setup
data_dir = 'F:/Alert/2011/SP2B_files/'

count = 0
os.chdir(data_dir)
for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
		
		
		folder_date = datetime.strptime(directory, '%Y%m%d')		
		
		if folder_date >= datetime(2011,1,1) and folder_date < datetime(2011,8,13):
			directory_path =os.path.abspath(directory)
			os.chdir(directory_path)
		
			for file in os.listdir('.'):
				if file.endswith('.sp2b') and (file.endswith('gnd.sp2b')==False) and os.path.getsize(directory_path + '/'+ file) !=0:
					
					for j_file_data in file_list:
						if file == j_file_data[0]:
							if j_file_data[1] != os.path.getsize(directory_path + '/'+ file)/1000:
								print  j_file_data[0], j_file_data[1] , file,os.path.getsize(directory_path + '/'+ file)/1000
								break
					
					if file not in file_name_list:
						print file
						print os.path.getsize(directory_path + '/'+ file)/1000
					count +=1
				
		os.chdir(data_dir)
print count