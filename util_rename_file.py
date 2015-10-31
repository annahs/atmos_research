import os
import sys

current_dir = 'C:/hysplit4/working/WHI 1h 10-day endpoints/'
os.chdir(current_dir)

for filename in os.listdir('.'):      
	if filename.startswith('tdump106'):
		new_name = 'tdump1006' + filename[8:]
		#print new_name
		#sys.exit()
		os.rename(filename, new_name)
