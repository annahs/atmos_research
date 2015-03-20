#this script runs through the .ini files in direct sub dirs of current_dir and notes when changes in the sample rate occured
#ini files use local time but are convereted to UTC here

import sys
import os
from datetime import datetime
from pprint import pprint
import pickle
from datetime import timedelta

def make_sample_factor_list(current_dir, parameters):

    os.chdir(current_dir)

    prev_ini_date = datetime.strptime('10/10/1000 10:10:10 AM', '%m/%d/%Y %I:%M:%S %p')
    prev_sample_rate = 0
    file_info = []
    
    for item in os.listdir(current_dir):
        daughter = os.path.join(current_dir, item)
        
        if os.path.isdir(daughter):
            for item in os.listdir(daughter):
                if item.endswith('.ini'):
                    ini_path = (os.path.join(daughter, item))
                    print item
                    f = open(ini_path, 'r')
                    for line in f:
						
						if line.startswith('Last Date Updated'):
							raw_date = line[18:].rstrip()
							ini_date = datetime.strptime(raw_date, '%m/%d/%Y %I:%M:%S %p')-timedelta(hours = parameters['timezone'])
						###use following 2 lines if only date information is from file name 
						#raw_date = item[:8].rstrip()
						#ini_date = datetime.strptime(raw_date, '%Y%m%d')+timedelta(hours = parameters['timezone'])

						if line.startswith('1 of Every'):
							sample_rate = float(line[11:].rstrip())
							print ini_date, ('UTC')
							print 'sample rate', sample_rate

							
						
                    if sample_rate != prev_sample_rate:
                        newline = [ini_date,sample_rate]
                        file_info.append(newline)
                        prev_sample_rate = sample_rate
                       
                    f.close()

    #pickle the list
    file = open('sample_rate_changes.srpckl', 'w')
    pickle.dump(file_info, file)
    file.close()


    #write final sorted list to text file 
    file = open('sample_rate_changes.txt', 'w')
    file.write('new_rate_start_time(UTC)' + '\t' + 'sample_rate'+ '\n')
    for line in file_info:
        line_to_write = str(line[0]) + '\t' +  str(line[1]) + '\n'
        file.write(line_to_write)
    file.close()


            

