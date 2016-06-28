import os
import sys
import fileinput

current_dir = 'C:/Users/Sarah Hanna/Documents/Data/Alert Data/Alert 1h mass and number concentrations/2011-2013/'
os.chdir(current_dir)

replacements = {'SP2#44':'SP2#17'}

for file in os.listdir('.'):    
	if file.startswith('2011'):
		print file

		lines = []
		with open(file) as infile:
			for line in infile:
				for src, target in replacements.iteritems():
					line = line.replace(src, target)
					
				lines.append(line)
		with open(file, 'w') as outfile:
			for line in lines:
				outfile.write(line)


		
		