import os
import sys

current_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013/'
os.chdir(current_dir)

for filename in os.listdir('.'):      
	if filename.startswith('201101'):
		new_name = '20111' + filename[6:]
		print new_name
		#sys.exit()
		os.rename(filename, new_name)
