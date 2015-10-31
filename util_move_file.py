import os
import sys
import shutil


current_dir = 'C:/HYSPLIT_argh/WHI_1h_10-day_endpoints/'
os.chdir(current_dir)

for filename in os.listdir('.'):      
	file_hour = int(filename[-2:])
	if file_hour%2 != 0:
		print file_hour
		
		shutil.move('C:/HYSPLIT_argh/WHI_1h_10-day_endpoints/'+filename, 'C:/HYSPLIT_argh/WHI_1h_10-day_archive/endpoints/'+filename)
		