import os
import sys
import shutil

current_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/default/'
#'D:/2010/WHI_ECSP2/Binary/'

destination =  'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/default/2010/'

for root, dirs, files in os.walk(current_dir, topdown=False):
    for name in files:
		#if name.endswith('.gz'):
		if name[2:6] == ('2010'):
			print name
			shutil.move(os.path.join(root, name),destination)
            
